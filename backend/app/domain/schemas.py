from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.models import JobStatus, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.operator


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class GoogleLoginResponse(BaseModel):
    authorization_url: str


class ImageAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    source_path: str
    preview_path: str | None
    content_type: str
    width: int
    height: int
    band_count: int
    dtype: str
    crs: str | None
    transform_json: list[float] | None
    bounds_json: dict[str, float] | None
    capture_date: datetime | None
    cloud_coverage: float | None
    metadata_json: dict[str, Any]
    created_at: datetime


class UploadResponse(BaseModel):
    asset: ImageAssetRead


class PredictRequest(BaseModel):
    image_id: str
    temporal_image_ids: list[str] = Field(default_factory=list)
    sar_image_id: str | None = None
    generator_model: Literal["classical", "pix2pixhd", "cyclegan", "latent_diffusion", "stable_diffusion"] = "classical"
    super_resolution_model: Literal["realesrgan", "swinir", "none"] = "none"
    enhance: bool = True
    use_deep_cloud_model: bool = False
    explainability: bool = True


class CloudMaskRequest(BaseModel):
    image_id: str
    model_name: Literal["heuristic", "unet", "unetpp", "deeplabv3p", "segformer", "mask2former"] = "heuristic"


class FusionRequest(BaseModel):
    image_id: str
    temporal_image_ids: list[str] = Field(default_factory=list)
    sar_image_id: str | None = None


class SuperResolutionRequest(BaseModel):
    image_id: str
    model_name: Literal["realesrgan", "swinir"] = "realesrgan"


class MetricsResponse(BaseModel):
    cloud_percentage_mean: float
    average_processing_seconds: float
    completed_jobs: int
    failed_jobs: int
    metric_summary: dict[str, float]


class ProcessingJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_id: str
    status: JobStatus
    task_type: str
    generator_model: str
    super_resolution_model: str | None
    pipeline_config_json: dict[str, Any]
    result_path: str | None
    fused_path: str | None
    mask_path: str | None
    confidence_path: str | None
    explainability_path: str | None
    metrics_json: dict[str, Any]
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime


class HistoryResponse(BaseModel):
    jobs: list[ProcessingJobRead]
