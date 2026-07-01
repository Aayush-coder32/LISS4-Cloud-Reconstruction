from __future__ import annotations

from app.core.database import SessionLocal
from app.domain.schemas import PredictRequest
from app.repositories.images import ImageRepository
from app.repositories.jobs import JobRepository
from app.repositories.users import UserRepository
from app.services.imagery import ImageryService
from app.services.pipeline import PipelineService
from app.workers.celery_app import celery_app


@celery_app.task(name="gencloudnet.predict")
def run_prediction_task(user_id: str, payload: dict) -> dict:
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        image_repository = ImageRepository(db)
        service = PipelineService(image_repository, JobRepository(db), ImageryService(image_repository))
        job = service.predict(user, PredictRequest(**payload))
        return {"job_id": job.id, "status": job.status.value}
    finally:
        db.close()
