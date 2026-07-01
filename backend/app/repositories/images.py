from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import ImageAsset


class ImageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        owner_id: str,
        filename: str,
        source_path: str,
        preview_path: str | None,
        content_type: str,
        width: int,
        height: int,
        band_count: int,
        dtype: str,
        crs: str | None,
        transform_json: list[float] | None,
        bounds_json: dict[str, float] | None,
        capture_date: datetime | None,
        cloud_coverage: float | None,
        metadata_json: dict[str, Any],
    ) -> ImageAsset:
        asset = ImageAsset(
            owner_id=owner_id,
            filename=filename,
            source_path=source_path,
            preview_path=preview_path,
            content_type=content_type,
            width=width,
            height=height,
            band_count=band_count,
            dtype=dtype,
            crs=crs,
            transform_json=transform_json,
            bounds_json=bounds_json,
            capture_date=capture_date,
            cloud_coverage=cloud_coverage,
            metadata_json=metadata_json,
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get(self, asset_id: str) -> ImageAsset | None:
        return self.db.get(ImageAsset, asset_id)

    def list_for_user(self, owner_id: str) -> list[ImageAsset]:
        return list(self.db.scalars(select(ImageAsset).where(ImageAsset.owner_id == owner_id).order_by(ImageAsset.created_at.desc())))
