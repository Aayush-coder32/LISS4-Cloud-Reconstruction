from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.models import JobStatus, ProcessingJob, User
from app.domain.schemas import CloudMaskRequest, FusionRequest, PredictRequest, SuperResolutionRequest
from app.repositories.images import ImageRepository
from app.repositories.jobs import JobRepository
from app.services.imagery import ImageryService
from gencloudnet_ml.pipeline import PipelineConfig, PipelineEngine
from gencloudnet_ml.preprocessing import align_to_reference, normalize_percentile


class PipelineService:
    def __init__(self, image_repository: ImageRepository, job_repository: JobRepository, imagery_service: ImageryService) -> None:
        self.image_repository = image_repository
        self.job_repository = job_repository
        self.imagery_service = imagery_service

    def predict(self, user: User, payload: PredictRequest) -> ProcessingJob:
        primary_asset = self._get_owned_asset(user.id, payload.image_id)
        temporal_assets = [self._get_owned_asset(user.id, asset_id) for asset_id in payload.temporal_image_ids]
        sar_asset = self._get_owned_asset(user.id, payload.sar_image_id) if payload.sar_image_id else None

        job = self.job_repository.create(
            owner_id=user.id,
            image_id=primary_asset.id,
            task_type="predict",
            generator_model=payload.generator_model,
            super_resolution_model=payload.super_resolution_model if payload.super_resolution_model != "none" else None,
            pipeline_config_json=payload.model_dump(),
        )
        return self._run_full_pipeline(job, primary_asset, temporal_assets, sar_asset)

    def cloud_mask(self, user: User, payload: CloudMaskRequest) -> ProcessingJob:
        asset = self._get_owned_asset(user.id, payload.image_id)
        job = self.job_repository.create(
            owner_id=user.id,
            image_id=asset.id,
            task_type="cloud-mask",
            generator_model="classical",
            super_resolution_model=None,
            pipeline_config_json=payload.model_dump(),
        )
        self.job_repository.update(job, status=JobStatus.running, started_at=datetime.now(UTC))
        try:
            image, profile = self.imagery_service.load_asset_array(asset)
            engine = PipelineEngine(
                PipelineConfig(
                    use_deep_cloud_model=payload.model_name != "heuristic",
                    cloud_model_name=payload.model_name,
                    checkpoint_dir=str(settings.checkpoint_dir),
                    explainability=False,
                    enhance=False,
                )
            )
            mask = engine.detect_clouds(normalize_percentile(image), use_deep_model=payload.model_name != "heuristic", model_name=payload.model_name)
            mask_path = self.imagery_service.write_raster(mask[None, ...], profile, stem=f"{job.id}_mask")
            completed = self.job_repository.update(
                job,
                status=JobStatus.completed,
                mask_path=mask_path,
                metrics_json={"cloud_percentage": float(mask.mean() * 100.0)},
                finished_at=datetime.now(UTC),
            )
            return completed
        except Exception as exc:
            return self.job_repository.update(
                job,
                status=JobStatus.failed,
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )

    def fusion(self, user: User, payload: FusionRequest) -> ProcessingJob:
        primary_asset = self._get_owned_asset(user.id, payload.image_id)
        temporal_assets = [self._get_owned_asset(user.id, asset_id) for asset_id in payload.temporal_image_ids]
        sar_asset = self._get_owned_asset(user.id, payload.sar_image_id) if payload.sar_image_id else None

        job = self.job_repository.create(
            owner_id=user.id,
            image_id=primary_asset.id,
            task_type="fusion",
            generator_model="classical",
            super_resolution_model=None,
            pipeline_config_json=payload.model_dump(),
        )
        self.job_repository.update(job, status=JobStatus.running, started_at=datetime.now(UTC))
        try:
            primary, profile = self.imagery_service.load_asset_array(primary_asset)
            temporal = self._load_aligned_temporal(primary, profile, temporal_assets)
            sar = self._load_aligned_sar(primary, profile, sar_asset) if sar_asset else None
            engine = PipelineEngine(PipelineConfig(enhance=False, explainability=False, checkpoint_dir=str(settings.checkpoint_dir)))
            mask = engine.detect_clouds(normalize_percentile(primary))
            fused = engine.temporal_fuse(normalize_percentile(primary), temporal, mask)
            if sar is not None:
                fused = engine.sensor_fuse(fused, sar, mask)

            fused_path = self.imagery_service.write_raster(fused, profile, stem=f"{job.id}_fused")
            completed = self.job_repository.update(
                job,
                status=JobStatus.completed,
                fused_path=fused_path,
                mask_path=self.imagery_service.write_raster(mask[None, ...], profile, stem=f"{job.id}_fusion_mask"),
                metrics_json={"cloud_percentage": float(mask.mean() * 100.0)},
                finished_at=datetime.now(UTC),
            )
            return completed
        except Exception as exc:
            return self.job_repository.update(job, status=JobStatus.failed, error_message=str(exc), finished_at=datetime.now(UTC))

    def super_resolution(self, user: User, payload: SuperResolutionRequest) -> ProcessingJob:
        asset = self._get_owned_asset(user.id, payload.image_id)
        job = self.job_repository.create(
            owner_id=user.id,
            image_id=asset.id,
            task_type="super-resolution",
            generator_model="classical",
            super_resolution_model=payload.model_name,
            pipeline_config_json=payload.model_dump(),
        )
        self.job_repository.update(job, status=JobStatus.running, started_at=datetime.now(UTC))
        try:
            image, profile = self.imagery_service.load_asset_array(asset)
            engine = PipelineEngine(PipelineConfig(super_resolution_model=payload.model_name, enhance=False, explainability=False, checkpoint_dir=str(settings.checkpoint_dir)))
            output = engine.super_resolve(normalize_percentile(image), payload.model_name)
            result_path = self.imagery_service.write_raster(output, profile, stem=f"{job.id}_superres")
            return self.job_repository.update(job, status=JobStatus.completed, result_path=result_path, finished_at=datetime.now(UTC))
        except Exception as exc:
            return self.job_repository.update(job, status=JobStatus.failed, error_message=str(exc), finished_at=datetime.now(UTC))

    def list_history(self, user: User) -> list[ProcessingJob]:
        return self.job_repository.list_for_user(user.id)

    def summarize_metrics(self, user: User) -> dict[str, float | int | dict[str, float]]:
        jobs = self.job_repository.aggregate_for_user(user.id)
        completed = [job for job in jobs if job.status == JobStatus.completed]
        failed = [job for job in jobs if job.status == JobStatus.failed]

        processing_seconds = []
        cloud_percentages = []
        aggregate: dict[str, list[float]] = {}
        for job in completed:
            if job.started_at and job.finished_at:
                processing_seconds.append((job.finished_at - job.started_at).total_seconds())
            if "cloud_percentage" in job.metrics_json:
                cloud_percentages.append(float(job.metrics_json["cloud_percentage"]))
            for key, value in job.metrics_json.items():
                if isinstance(value, (int, float)):
                    aggregate.setdefault(key, []).append(float(value))

        summary = {key: float(sum(values) / max(len(values), 1)) for key, values in aggregate.items()}
        return {
            "cloud_percentage_mean": float(sum(cloud_percentages) / max(len(cloud_percentages), 1)),
            "average_processing_seconds": float(sum(processing_seconds) / max(len(processing_seconds), 1)),
            "completed_jobs": len(completed),
            "failed_jobs": len(failed),
            "metric_summary": summary,
        }

    def _run_full_pipeline(self, job: ProcessingJob, primary_asset, temporal_assets, sar_asset) -> ProcessingJob:
        self.job_repository.update(job, status=JobStatus.running, started_at=datetime.now(UTC))
        try:
            primary, profile = self.imagery_service.load_asset_array(primary_asset)
            temporal = self._load_aligned_temporal(primary, profile, temporal_assets)
            sar = self._load_aligned_sar(primary, profile, sar_asset) if sar_asset else None
            reference = temporal[0] if temporal else None

            engine = PipelineEngine(
                PipelineConfig(
                    generator_model=job.generator_model,
                    super_resolution_model=job.super_resolution_model or "none",
                    enhance=bool(job.pipeline_config_json.get("enhance", True)),
                    explainability=bool(job.pipeline_config_json.get("explainability", True)),
                    use_deep_cloud_model=bool(job.pipeline_config_json.get("use_deep_cloud_model", False)),
                    checkpoint_dir=str(settings.checkpoint_dir),
                )
            )
            artifacts = engine.run(primary, temporal_images=temporal, sar_image=sar, reference_target=reference)

            result_path = self.imagery_service.write_raster(artifacts.reconstruction, profile, stem=f"{job.id}_reconstruction")
            fused_path = self.imagery_service.write_raster(artifacts.fused, profile, stem=f"{job.id}_fused")
            mask_path = self.imagery_service.write_raster(artifacts.cloud_mask[None, ...], profile, stem=f"{job.id}_mask")
            confidence_path = self.imagery_service.write_raster(artifacts.confidence[None, ...], profile, stem=f"{job.id}_confidence")
            explainability_path = None
            if artifacts.explainability is not None:
                explainability_path = self.imagery_service.write_raster(artifacts.explainability[None, ...], profile, stem=f"{job.id}_xai")

            metrics = dict(artifacts.metrics)
            metrics["cloud_percentage"] = float(artifacts.cloud_mask.mean() * 100.0)
            if job.started_at:
                metrics["processing_seconds"] = float((datetime.now(UTC) - job.started_at).total_seconds())

            primary_asset.cloud_coverage = metrics["cloud_percentage"]
            self.image_repository.db.add(primary_asset)
            self.image_repository.db.commit()

            return self.job_repository.update(
                job,
                status=JobStatus.completed,
                result_path=result_path,
                fused_path=fused_path,
                mask_path=mask_path,
                confidence_path=confidence_path,
                explainability_path=explainability_path,
                metrics_json=metrics,
                finished_at=datetime.now(UTC),
            )
        except Exception as exc:
            return self.job_repository.update(job, status=JobStatus.failed, error_message=str(exc), finished_at=datetime.now(UTC))

    def _get_owned_asset(self, owner_id: str, asset_id: str | None):
        if not asset_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset identifier is required")
        asset = self.image_repository.get(asset_id)
        if asset is None or asset.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        return asset

    def _load_aligned_temporal(self, primary: np.ndarray, profile: dict[str, Any], assets: list[Any]) -> list[np.ndarray]:
        aligned = []
        for asset in assets:
            image, temporal_profile = self.imagery_service.load_asset_array(asset)
            aligned.append(align_to_reference(image, temporal_profile, profile) if image.shape[-2:] != primary.shape[-2:] else normalize_percentile(image))
        return [normalize_percentile(item) for item in aligned]

    def _load_aligned_sar(self, primary: np.ndarray, profile: dict[str, Any], asset: Any) -> np.ndarray:
        image, sar_profile = self.imagery_service.load_asset_array(asset)
        aligned = align_to_reference(image, sar_profile, profile) if image.shape[-2:] != primary.shape[-2:] else image
        if aligned.shape[0] > 1:
            aligned = aligned[:1]
        return normalize_percentile(aligned)
