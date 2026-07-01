from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import rasterio
from fastapi import HTTPException, UploadFile, status
from PIL import Image
from rasterio.transform import Affine
from rasterio.windows import Window

from app.core.config import settings
from app.domain.models import ImageAsset
from app.repositories.images import ImageRepository


class ImageryService:
    def __init__(self, image_repository: ImageRepository) -> None:
        self.image_repository = image_repository

    def save_upload(self, owner_id: str, upload: UploadFile, capture_date: datetime | None = None) -> ImageAsset:
        suffix = Path(upload.filename or "upload.bin").suffix.lower() or ".bin"
        target_path = settings.raw_upload_dir / f"{uuid4()}{suffix}"

        with target_path.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)

        metadata = self.extract_metadata(target_path, upload.content_type or "application/octet-stream")
        preview_path = self._generate_preview(target_path, metadata["band_count"])

        asset = self.image_repository.create(
            owner_id=owner_id,
            filename=upload.filename or target_path.name,
            source_path=str(target_path),
            preview_path=str(preview_path) if preview_path else None,
            content_type=upload.content_type or "application/octet-stream",
            width=metadata["width"],
            height=metadata["height"],
            band_count=metadata["band_count"],
            dtype=metadata["dtype"],
            crs=metadata.get("crs"),
            transform_json=metadata.get("transform_json"),
            bounds_json=metadata.get("bounds_json"),
            capture_date=capture_date or metadata.get("capture_date"),
            cloud_coverage=metadata.get("cloud_coverage"),
            metadata_json=metadata,
        )
        return asset

    def extract_metadata(self, path: Path, content_type: str) -> dict[str, Any]:
        if path.suffix.lower() in {".tif", ".tiff"}:
            with rasterio.open(path) as src:
                tags = src.tags()
                capture_date = tags.get("TIFFTAG_DATETIME")
                capture_dt = None
                if capture_date:
                    try:
                        capture_dt = datetime.strptime(capture_date, "%Y:%m:%d %H:%M:%S").replace(tzinfo=UTC)
                    except ValueError:
                        capture_dt = None
                sample = src.read(window=Window(0, 0, min(src.width, 512), min(src.height, 512)))
                brightness = float(np.mean(sample.astype(np.float32)))
                cloud_coverage = float(np.mean(sample > np.percentile(sample, 92)) * 100.0)
                return {
                    "width": src.width,
                    "height": src.height,
                    "band_count": src.count,
                    "dtype": str(src.dtypes[0]),
                    "crs": src.crs.to_string() if src.crs else None,
                    "transform_json": list(src.transform) if isinstance(src.transform, Affine) else None,
                    "bounds_json": {
                        "left": src.bounds.left,
                        "bottom": src.bounds.bottom,
                        "right": src.bounds.right,
                        "top": src.bounds.top,
                    },
                    "capture_date": capture_dt,
                    "cloud_coverage": cloud_coverage,
                    "tags": tags,
                    "content_type": content_type,
                    "mean_brightness": brightness,
                }

        image = Image.open(path)
        array = np.asarray(image)
        band_count = 1 if array.ndim == 2 else array.shape[-1]
        return {
            "width": int(image.width),
            "height": int(image.height),
            "band_count": band_count,
            "dtype": str(array.dtype),
            "crs": None,
            "transform_json": None,
            "bounds_json": None,
            "capture_date": None,
            "cloud_coverage": float(np.mean(array > np.percentile(array, 92)) * 100.0),
            "content_type": content_type,
            "mode": image.mode,
        }

    def load_asset_array(self, asset: ImageAsset) -> tuple[np.ndarray, dict[str, Any]]:
        path = Path(asset.source_path)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source asset file is missing")

        if path.suffix.lower() in {".tif", ".tiff"}:
            with rasterio.open(path) as src:
                return src.read().astype(np.float32), src.profile.copy()

        image = Image.open(path).convert("RGB")
        array = np.asarray(image).astype(np.float32).transpose(2, 0, 1)
        return array, {"driver": "GTiff", "height": array.shape[1], "width": array.shape[2], "count": array.shape[0], "dtype": "float32"}

    def write_raster(self, array: np.ndarray, profile: dict[str, Any], stem: str) -> str:
        array = np.nan_to_num(array).astype(np.float32)
        destination = settings.processed_dir / f"{stem}.tif"
        output_profile = profile.copy()
        output_profile.update(
            {
                "driver": "GTiff",
                "height": int(array.shape[1]),
                "width": int(array.shape[2]),
                "count": int(array.shape[0]),
                "dtype": "float32",
            }
        )
        with rasterio.open(destination, "w", **output_profile) as dst:
            dst.write(array)
        return str(destination)

    def _generate_preview(self, path: Path, band_count: int) -> Path | None:
        preview_path = settings.preview_dir / f"{path.stem}.png"
        try:
            if path.suffix.lower() in {".tif", ".tiff"}:
                with rasterio.open(path) as src:
                    read_count = min(3, src.count)
                    stack = src.read(indexes=list(range(1, read_count + 1))).astype(np.float32)
                    if read_count == 1:
                        stack = np.repeat(stack, 3, axis=0)
                    image = self._to_uint8(stack.transpose(1, 2, 0))
            else:
                pil_image = Image.open(path).convert("RGB")
                image = np.asarray(pil_image)
            Image.fromarray(image).save(preview_path)
            return preview_path
        except Exception:
            if preview_path.exists():
                preview_path.unlink()
            return None

    @staticmethod
    def _to_uint8(array: np.ndarray) -> np.ndarray:
        low = np.percentile(array, 2)
        high = np.percentile(array, 98)
        clipped = np.clip((array - low) / max(high - low, 1e-6), 0.0, 1.0)
        return (clipped * 255).astype(np.uint8)
