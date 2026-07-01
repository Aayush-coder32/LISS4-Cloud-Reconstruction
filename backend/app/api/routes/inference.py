from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_user
from app.domain.models import User
from app.domain.schemas import CloudMaskRequest, FusionRequest, PredictRequest, ProcessingJobRead, SuperResolutionRequest
from app.repositories.images import ImageRepository
from app.repositories.jobs import JobRepository
from app.services.imagery import ImageryService
from app.services.pipeline import PipelineService

router = APIRouter(tags=["inference"])


def get_pipeline_service(db: DbSession) -> PipelineService:
    image_repository = ImageRepository(db)
    imagery_service = ImageryService(image_repository)
    return PipelineService(image_repository, JobRepository(db), imagery_service)


@router.post("/predict", response_model=ProcessingJobRead)
def predict(
    payload: PredictRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> ProcessingJobRead:
    job = service.predict(current_user, payload)
    return ProcessingJobRead.model_validate(job)


@router.post("/cloud-mask", response_model=ProcessingJobRead)
def cloud_mask(
    payload: CloudMaskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> ProcessingJobRead:
    job = service.cloud_mask(current_user, payload)
    return ProcessingJobRead.model_validate(job)


@router.post("/fusion", response_model=ProcessingJobRead)
def fusion(
    payload: FusionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> ProcessingJobRead:
    job = service.fusion(current_user, payload)
    return ProcessingJobRead.model_validate(job)


@router.post("/super-resolution", response_model=ProcessingJobRead)
def super_resolution(
    payload: SuperResolutionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(get_pipeline_service)],
) -> ProcessingJobRead:
    job = service.super_resolution(current_user, payload)
    return ProcessingJobRead.model_validate(job)
