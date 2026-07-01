from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch import Tensor, nn


def cloud_saliency_map(image: np.ndarray, mask: np.ndarray, confidence: np.ndarray) -> np.ndarray:
    brightness = np.mean(image, axis=0)
    edges = np.abs(np.gradient(brightness)[0]) + np.abs(np.gradient(brightness)[1])
    saliency = 0.5 * mask + 0.3 * (1.0 - confidence) + 0.2 * edges / max(edges.max(), 1e-6)
    return np.clip(saliency, 0.0, 1.0).astype(np.float32)


def feature_visualization(features: np.ndarray) -> np.ndarray:
    flattened = features.reshape(features.shape[0], -1)
    flattened = flattened - flattened.mean(axis=1, keepdims=True)
    covariance = flattened @ flattened.T
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    principal = eigenvectors[:, np.argmax(eigenvalues)]
    projection = principal @ flattened
    projection = projection.reshape(features.shape[1], features.shape[2])
    projection = (projection - projection.min()) / max(projection.max() - projection.min(), 1e-6)
    return projection.astype(np.float32)


def attention_rollout(attention_matrices: list[np.ndarray]) -> np.ndarray:
    if not attention_matrices:
        raise ValueError("Expected at least one attention matrix")
    result = np.eye(attention_matrices[0].shape[-1], dtype=np.float32)
    for matrix in attention_matrices:
        matrix = matrix + np.eye(matrix.shape[-1], dtype=np.float32)
        matrix = matrix / matrix.sum(axis=-1, keepdims=True)
        result = result @ matrix
    rollout = result.mean(axis=0)
    rollout = (rollout - rollout.min()) / max(rollout.max() - rollout.min(), 1e-6)
    return rollout.astype(np.float32)


def _resolve_module(model: nn.Module, layer_name: str) -> nn.Module:
    for name, module in model.named_modules():
        if name == layer_name:
            return module
    raise KeyError(f"Layer {layer_name!r} not found")


def gradcam(model: nn.Module, input_tensor: Tensor, target_layer: str, target_index: int | None = None) -> np.ndarray:
    activations: list[Tensor] = []
    gradients: list[Tensor] = []

    def forward_hook(_: nn.Module, __: tuple[Tensor, ...], output: Tensor) -> None:
        activations.append(output.detach())

    def backward_hook(_: nn.Module, grad_input: tuple[Tensor, ...], grad_output: tuple[Tensor, ...]) -> None:
        del grad_input
        gradients.append(grad_output[0].detach())

    layer = _resolve_module(model, target_layer)
    forward_handle = layer.register_forward_hook(forward_hook)
    backward_handle = layer.register_full_backward_hook(backward_hook)

    model.zero_grad(set_to_none=True)
    output = model(input_tensor)
    score = output[:, target_index].mean() if output.ndim == 4 and target_index is not None else output.mean()
    score.backward()

    forward_handle.remove()
    backward_handle.remove()

    activation = activations[-1]
    gradient = gradients[-1]
    weights = gradient.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((weights * activation).sum(dim=1, keepdim=True))
    cam = torch.nn.functional.interpolate(cam, size=input_tensor.shape[-2:], mode="bilinear", align_corners=False)
    cam = cam.squeeze().cpu().numpy()
    cam = (cam - cam.min()) / max(cam.max() - cam.min(), 1e-6)
    return cam.astype(np.float32)
