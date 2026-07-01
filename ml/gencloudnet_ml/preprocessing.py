from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject


def ensure_chw(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image[None, ...]
    if image.ndim == 3 and image.shape[0] <= 16:
        return image
    if image.ndim == 3:
        return image.transpose(2, 0, 1)
    raise ValueError(f"Unsupported image shape: {image.shape}")


def normalize_percentile(image: np.ndarray, lower: float = 2.0, upper: float = 98.0) -> np.ndarray:
    image = ensure_chw(image).astype(np.float32)
    normalized = np.empty_like(image)
    for band_index in range(image.shape[0]):
        band = image[band_index]
        low = np.percentile(band, lower)
        high = np.percentile(band, upper)
        normalized[band_index] = np.clip((band - low) / max(high - low, 1e-6), 0.0, 1.0)
    return normalized


def resize_image(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    image = ensure_chw(image)
    resized = [cv2.resize(band, size[::-1], interpolation=cv2.INTER_CUBIC) for band in image]
    return np.stack(resized, axis=0).astype(np.float32)


def denoise_image(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    image = ensure_chw(image).astype(np.float32)
    return np.stack([cv2.medianBlur(band, kernel_size) for band in image], axis=0)


def sharpen_image(image: np.ndarray, amount: float = 0.9, sigma: float = 1.2) -> np.ndarray:
    image = ensure_chw(image).astype(np.float32)
    sharpened = []
    for band in image:
        blurred = cv2.GaussianBlur(band, (0, 0), sigma)
        sharpened.append(np.clip(cv2.addWeighted(band, 1.0 + amount, blurred, -amount, 0), 0.0, 1.0))
    return np.stack(sharpened, axis=0)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    image = normalize_percentile(image)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = []
    for band in image:
        enhanced.append(clahe.apply((band * 255).astype(np.uint8)).astype(np.float32) / 255.0)
    return np.stack(enhanced, axis=0)


def extract_patches(image: np.ndarray, patch_size: int = 256, stride: int = 128) -> tuple[np.ndarray, list[tuple[int, int]]]:
    image = ensure_chw(image)
    patches: list[np.ndarray] = []
    locations: list[tuple[int, int]] = []
    _, height, width = image.shape
    for y in range(0, max(height - patch_size + 1, 1), stride):
        for x in range(0, max(width - patch_size + 1, 1), stride):
            patches.append(image[:, y : y + patch_size, x : x + patch_size])
            locations.append((y, x))
    return np.stack(patches), locations


def merge_patches(
    patches: np.ndarray,
    locations: list[tuple[int, int]],
    output_shape: tuple[int, int, int],
    patch_size: int = 256,
) -> np.ndarray:
    channels, height, width = output_shape
    output = np.zeros((channels, height, width), dtype=np.float32)
    weights = np.zeros((channels, height, width), dtype=np.float32)
    for patch, (y, x) in zip(patches, locations, strict=False):
        patch_height = min(patch_size, height - y)
        patch_width = min(patch_size, width - x)
        output[:, y : y + patch_height, x : x + patch_width] += patch[:, :patch_height, :patch_width]
        weights[:, y : y + patch_height, x : x + patch_width] += 1.0
    return output / np.maximum(weights, 1e-6)


def align_to_reference(
    image: np.ndarray,
    source_profile: dict[str, Any],
    reference_profile: dict[str, Any],
) -> np.ndarray:
    image = ensure_chw(image)
    if not source_profile.get("crs") or not reference_profile.get("crs"):
        return resize_image(image, (reference_profile["height"], reference_profile["width"]))

    destination = np.zeros((image.shape[0], reference_profile["height"], reference_profile["width"]), dtype=np.float32)
    for band_index in range(image.shape[0]):
        reproject(
            source=image[band_index],
            destination=destination[band_index],
            src_transform=source_profile.get("transform", Affine.identity()),
            src_crs=source_profile["crs"],
            dst_transform=reference_profile.get("transform", Affine.identity()),
            dst_crs=reference_profile["crs"],
            resampling=Resampling.bilinear,
        )
    return destination


def read_raster(path: str) -> tuple[np.ndarray, dict[str, Any]]:
    with rasterio.open(path) as src:
        return src.read().astype(np.float32), src.profile.copy()
