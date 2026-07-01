from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import torch

from gencloudnet_ml.explainability import cloud_saliency_map
from gencloudnet_ml.metrics import evaluate_all
from gencloudnet_ml.models import get_cloud_model, get_generator, get_super_resolution_model
from gencloudnet_ml.preprocessing import apply_clahe, denoise_image, normalize_percentile, sharpen_image


@dataclass(slots=True)
class PipelineConfig:
    generator_model: str = "classical"
    super_resolution_model: str = "none"
    enhance: bool = True
    explainability: bool = True
    use_deep_cloud_model: bool = False
    cloud_model_name: str = "heuristic"
    checkpoint_dir: str | None = None


@dataclass(slots=True)
class PipelineArtifacts:
    primary: np.ndarray
    cloud_mask: np.ndarray
    fused: np.ndarray
    reconstruction: np.ndarray
    confidence: np.ndarray
    explainability: np.ndarray | None
    metrics: dict[str, float] = field(default_factory=dict)


class PipelineEngine:
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def run(
        self,
        primary: np.ndarray,
        temporal_images: list[np.ndarray] | None = None,
        sar_image: np.ndarray | None = None,
        reference_target: np.ndarray | None = None,
    ) -> PipelineArtifacts:
        primary = normalize_percentile(primary)
        temporal_images = [normalize_percentile(item) for item in (temporal_images or [])]
        sar_image = normalize_percentile(sar_image) if sar_image is not None else None

        mask = self.detect_clouds(primary, use_deep_model=self.config.use_deep_cloud_model, model_name=self.config.cloud_model_name)
        fused = self.temporal_fuse(primary, temporal_images, mask)
        if sar_image is not None:
            fused = self.sensor_fuse(fused, sar_image, mask)

        reconstruction = self.reconstruct(fused, mask)
        if self.config.super_resolution_model != "none":
            reconstruction = self.super_resolve(reconstruction, self.config.super_resolution_model)
        if self.config.enhance:
            reconstruction = sharpen_image(apply_clahe(denoise_image(reconstruction)))

        confidence = self.estimate_confidence(primary, temporal_images, mask, reconstruction)
        explainability = cloud_saliency_map(primary, mask, confidence) if self.config.explainability else None

        metrics = {}
        if reference_target is not None:
            metrics = evaluate_all(reconstruction, normalize_percentile(reference_target), prediction_mask=mask, target_mask=mask)
        elif temporal_images:
            metrics = evaluate_all(reconstruction, temporal_images[0], prediction_mask=mask, target_mask=(1.0 - mask))

        return PipelineArtifacts(
            primary=primary,
            cloud_mask=mask,
            fused=fused,
            reconstruction=reconstruction,
            confidence=confidence,
            explainability=explainability,
            metrics=metrics,
        )

    def detect_clouds(self, image: np.ndarray, use_deep_model: bool = False, model_name: str = "heuristic") -> np.ndarray:
        if use_deep_model and model_name != "heuristic":
            model = get_cloud_model(model_name, in_channels=image.shape[0]).to(self.device).eval()
            with torch.no_grad():
                logits = model(torch.from_numpy(image[None]).float().to(self.device))
                prediction = torch.sigmoid(logits).cpu().numpy()[0, 0]
            return (prediction > 0.5).astype(np.float32)

        rgb = image[:3] if image.shape[0] >= 3 else np.repeat(image[:1], 3, axis=0)
        brightness = rgb.mean(axis=0)
        whiteness = np.std(rgb, axis=0)
        ndvi = np.zeros_like(brightness)
        if image.shape[0] >= 4:
            red = image[2]
            nir = image[3]
            ndvi = (nir - red) / (nir + red + 1e-6)
        cloud_score = 0.6 * brightness + 0.25 * (1.0 - whiteness) + 0.15 * (1.0 - np.clip(ndvi, -1.0, 1.0))
        threshold = float(np.percentile(cloud_score, 82))
        raw_mask = (cloud_score >= threshold).astype(np.uint8)
        refined = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        return refined.astype(np.float32)

    def temporal_fuse(self, primary: np.ndarray, temporal_images: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
        if not temporal_images:
            return primary.copy()
        stack = np.stack([primary, *temporal_images], axis=0)
        median = np.median(stack, axis=0)
        similarity_maps = []
        for candidate in temporal_images:
            delta = np.mean(np.abs(candidate - primary), axis=0)
            similarity_maps.append(1.0 / (delta + 1e-3))
        weights = np.stack(similarity_maps, axis=0)
        weights = weights / np.maximum(weights.sum(axis=0, keepdims=True), 1e-6)
        weighted_temporal = np.sum(weights[:, None, ...] * np.stack(temporal_images, axis=0), axis=0)
        fill = 0.65 * weighted_temporal + 0.35 * median
        return np.where(mask[None] > 0.5, fill, primary).astype(np.float32)

    def sensor_fuse(self, optical: np.ndarray, sar: np.ndarray, mask: np.ndarray) -> np.ndarray:
        sar_band = sar.mean(axis=0, keepdims=True)
        sar_band = (sar_band - sar_band.min()) / max(sar_band.max() - sar_band.min(), 1e-6)
        edges = cv2.Laplacian(sar_band[0], cv2.CV_32F)
        edges = np.abs(edges)
        edges = edges / max(edges.max(), 1e-6)
        blend = 0.7 * optical + 0.3 * np.repeat(sar_band, optical.shape[0], axis=0)
        blend = blend + 0.15 * edges[None] * optical
        return np.where(mask[None] > 0.5, blend, optical).clip(0.0, 1.0).astype(np.float32)

    def reconstruct(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        classical = self._classical_inpaint(image, mask)
        if self.config.generator_model == "classical":
            return classical

        checkpoint = self._checkpoint_path(self.config.generator_model)
        try:
            model = get_generator(self.config.generator_model, channels=image.shape[0], checkpoint_path=checkpoint)
        except Exception:
            return classical

        if hasattr(model, "inpaint"):
            try:
                return np.clip(model.inpaint(classical, mask), 0.0, 1.0).astype(np.float32)
            except Exception:
                return classical

        if checkpoint is None or not Path(checkpoint).exists():
            return classical

        tensor_image = torch.from_numpy(classical[None]).float().to(self.device)
        tensor_mask = torch.from_numpy(mask[None, None]).float().to(self.device)
        model = model.to(self.device).eval()
        with torch.no_grad():
            prediction = model(tensor_image, tensor_mask).cpu().numpy()[0]
        return np.where(mask[None] > 0.5, prediction, image).clip(0.0, 1.0).astype(np.float32)

    def super_resolve(self, image: np.ndarray, model_name: str) -> np.ndarray:
        checkpoint = self._checkpoint_path(model_name)
        if checkpoint and Path(checkpoint).exists():
            model = get_super_resolution_model(model_name, channels=image.shape[0], checkpoint_path=checkpoint).to(self.device).eval()
            with torch.no_grad():
                output = model(torch.from_numpy(image[None]).float().to(self.device)).cpu().numpy()[0]
            return np.clip(output, 0.0, 1.0).astype(np.float32)
        upscale = cv2.resize(image.transpose(1, 2, 0), None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        return np.clip(upscale.transpose(2, 0, 1), 0.0, 1.0).astype(np.float32)

    def estimate_confidence(
        self,
        primary: np.ndarray,
        temporal_images: list[np.ndarray],
        mask: np.ndarray,
        reconstruction: np.ndarray,
    ) -> np.ndarray:
        agreement = []
        for candidate in temporal_images:
            agreement.append(1.0 - np.mean(np.abs(candidate - reconstruction), axis=0))
        agreement_map = np.mean(np.stack(agreement, axis=0), axis=0) if agreement else 1.0 - np.mean(np.abs(primary - reconstruction), axis=0)
        smoothness = 1.0 - np.mean(np.abs(np.gradient(reconstruction, axis=(1, 2))), axis=0).mean(axis=0)
        confidence = 0.6 * np.clip(agreement_map, 0.0, 1.0) + 0.4 * np.clip(smoothness, 0.0, 1.0)
        confidence = np.where(mask > 0.5, confidence, 1.0)
        confidence = cv2.GaussianBlur(confidence.astype(np.float32), (5, 5), 0)
        return np.clip(confidence, 0.0, 1.0)

    @staticmethod
    def _classical_inpaint(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        mask_uint8 = (mask > 0.5).astype(np.uint8) * 255
        reconstructed = []
        for band in image:
            band_uint8 = np.clip(band * 255.0, 0, 255).astype(np.uint8)
            inpainted = cv2.inpaint(band_uint8, mask_uint8, 5, cv2.INPAINT_TELEA)
            reconstructed.append(inpainted.astype(np.float32) / 255.0)
        return np.stack(reconstructed, axis=0)

    def _checkpoint_path(self, name: str) -> str | None:
        if not self.config.checkpoint_dir:
            return None
        candidate = Path(self.config.checkpoint_dir) / f"{name}.pt"
        return str(candidate) if candidate.exists() else None
