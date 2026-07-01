from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    operator = "operator"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.operator)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    images: Mapped[list["ImageAsset"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ImageAsset(Base):
    __tablename__ = "image_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    source_path: Mapped[str] = mapped_column(String(1024))
    preview_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content_type: Mapped[str] = mapped_column(String(128))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    band_count: Mapped[int] = mapped_column(Integer)
    dtype: Mapped[str] = mapped_column(String(64))
    crs: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transform_json: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    bounds_json: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    capture_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cloud_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="images")
    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="image")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("image_assets.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    task_type: Mapped[str] = mapped_column(String(64))
    generator_model: Mapped[str] = mapped_column(String(64), default="classical")
    super_resolution_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pipeline_config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fused_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    mask_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    explainability_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="jobs")
    image: Mapped["ImageAsset"] = relationship(back_populates="jobs")
