from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import JobStatus, ProcessingJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        owner_id: str,
        image_id: str,
        task_type: str,
        generator_model: str,
        super_resolution_model: str | None,
        pipeline_config_json: dict[str, Any],
    ) -> ProcessingJob:
        job = ProcessingJob(
            owner_id=owner_id,
            image_id=image_id,
            task_type=task_type,
            generator_model=generator_model,
            super_resolution_model=super_resolution_model,
            pipeline_config_json=pipeline_config_json,
            status=JobStatus.pending,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> ProcessingJob | None:
        return self.db.get(ProcessingJob, job_id)

    def list_for_user(self, owner_id: str) -> list[ProcessingJob]:
        return list(self.db.scalars(select(ProcessingJob).where(ProcessingJob.owner_id == owner_id).order_by(ProcessingJob.created_at.desc())))

    def update(self, job: ProcessingJob, **changes: Any) -> ProcessingJob:
        for key, value in changes.items():
            setattr(job, key, value)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def aggregate_for_user(self, owner_id: str) -> list[ProcessingJob]:
        return self.list_for_user(owner_id)
