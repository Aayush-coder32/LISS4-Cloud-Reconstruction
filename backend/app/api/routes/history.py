from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import HistoryResponse, MetricsResponse, ProcessingJobRead
from app.repositories.images import ImageRepository
from app.repositories.jobs import JobRepository
from app.services.imagery import ImageryService
from app.services.pipeline import PipelineService

router = APIRouter(tags=["history"])


def get_pipeline_service(db: DbSession) -> PipelineService:
    image_repository = ImageRepository(db)
    imagery_service = ImageryService(image_repository)
    return PipelineService(image_repository, JobRepository(db), imagery_service)


@router.get("/history", response_model=HistoryResponse)
def history(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> HistoryResponse:
    jobs = service.list_history(current_user)
    return HistoryResponse(jobs=[ProcessingJobRead.model_validate(job) for job in jobs])


@router.get("/metrics", response_model=MetricsResponse)
def metrics(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> MetricsResponse:
    return MetricsResponse(**service.summarize_metrics(current_user))
