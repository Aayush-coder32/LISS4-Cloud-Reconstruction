from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from skimage.metrics import structural_similarity
from torch import Tensor, nn


def mse(prediction: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean((prediction - target) ** 2))


def rmse(prediction: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(mse(prediction, target)))


def psnr(prediction: np.ndarray, target: np.ndarray, max_value: float = 1.0) -> float:
    value = mse(prediction, target)
    if value <= 1e-12:
        return float("inf")
    return float(20 * np.log10(max_value) - 10 * np.log10(value))


def ssim(prediction: np.ndarray, target: np.ndarray) -> float:
    prediction = np.moveaxis(prediction, 0, -1)
    target = np.moveaxis(target, 0, -1)
    data_range = max(float(target.max() - target.min()), 1e-6)
    return float(structural_similarity(prediction, target, channel_axis=-1, data_range=data_range))


def dice_score(prediction_mask: np.ndarray, target_mask: np.ndarray, threshold: float = 0.5) -> float:
    pred = (prediction_mask > threshold).astype(np.float32)
    target = (target_mask > threshold).astype(np.float32)
    intersection = np.sum(pred * target)
    return float((2 * intersection + 1e-6) / (pred.sum() + target.sum() + 1e-6))


def iou_score(prediction_mask: np.ndarray, target_mask: np.ndarray, threshold: float = 0.5) -> float:
    pred = (prediction_mask > threshold).astype(np.float32)
    target = (target_mask > threshold).astype(np.float32)
    intersection = np.sum(pred * target)
    union = np.sum(np.clip(pred + target, 0, 1))
    return float((intersection + 1e-6) / (union + 1e-6))


def spectral_angle_mapper(prediction: np.ndarray, target: np.ndarray) -> float:
    pred = prediction.reshape(prediction.shape[0], -1)
    true = target.reshape(target.shape[0], -1)
    numerator = np.sum(pred * true, axis=0)
    denominator = np.linalg.norm(pred, axis=0) * np.linalg.norm(true, axis=0) + 1e-6
    angles = np.arccos(np.clip(numerator / denominator, -1.0, 1.0))
    return float(np.mean(angles))


def ergas(prediction: np.ndarray, target: np.ndarray, ratio: float = 4.0) -> float:
    errors = []
    for band_index in range(prediction.shape[0]):
        band_rmse = rmse(prediction[band_index], target[band_index])
        mean_ref = float(np.mean(target[band_index])) + 1e-6
        errors.append((band_rmse / mean_ref) ** 2)
    return float(100 / ratio * np.sqrt(np.mean(errors)))


def _sqrtm(matrix: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(matrix)
    values = np.clip(values, 0.0, None)
    sqrt_values = np.sqrt(values)
    return (vectors * sqrt_values) @ vectors.T


def fid_score(prediction: np.ndarray, target: np.ndarray) -> float:
    pred = prediction.reshape(prediction.shape[0], -1).T
    true = target.reshape(target.shape[0], -1).T
    mu1, mu2 = pred.mean(axis=0), true.mean(axis=0)
    sigma1 = np.cov(pred, rowvar=False)
    sigma2 = np.cov(true, rowvar=False)
    covmean = _sqrtm(sigma1 @ sigma2)
    return float(np.sum((mu1 - mu2) ** 2) + np.trace(sigma1 + sigma2 - 2 * covmean))


class _TinyPerceptualNet(nn.Module):
    def __init__(self, channels: int = 4) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(channels, 16, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.GELU(),
            nn.AvgPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.GELU(),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.features(x)


def lpips_distance(prediction: np.ndarray, target: np.ndarray) -> float:
    model = _TinyPerceptualNet(channels=prediction.shape[0]).eval()
    with torch.no_grad():
        pred = torch.from_numpy(prediction[None]).float()
        true = torch.from_numpy(target[None]).float()
        pred_features = model(pred)
        true_features = model(true)
        return float(F.l1_loss(pred_features, true_features).item())


def evaluate_all(prediction: np.ndarray, target: np.ndarray, prediction_mask: np.ndarray | None = None, target_mask: np.ndarray | None = None) -> dict[str, float]:
    metrics = {
        "psnr": psnr(prediction, target),
        "ssim": ssim(prediction, target),
        "rmse": rmse(prediction, target),
        "mse": mse(prediction, target),
        "fid": fid_score(prediction, target),
        "lpips": lpips_distance(prediction, target),
        "sam": spectral_angle_mapper(prediction, target),
        "ergas": ergas(prediction, target),
    }
    if prediction_mask is not None and target_mask is not None:
        metrics["dice"] = dice_score(prediction_mask, target_mask)
        metrics["iou"] = iou_score(prediction_mask, target_mask)
    return metrics
