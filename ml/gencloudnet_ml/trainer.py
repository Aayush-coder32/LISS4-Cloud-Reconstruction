from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mlflow
import torch
import torch.nn.functional as F
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader


@dataclass(slots=True)
class TrainingConfig:
    experiment_name: str
    epochs: int = 25
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    mixed_precision: bool = True
    early_stopping_patience: int = 6
    checkpoint_dir: str = "artifacts/checkpoints"


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: TrainingConfig,
    task: str = "segmentation",
) -> dict[str, float]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    optimizer = AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    scaler = torch.cuda.amp.GradScaler(enabled=config.mixed_precision and device == "cuda")

    checkpoint_dir = Path(config.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    best_path = checkpoint_dir / f"{config.experiment_name}.pt"

    best_val = float("inf")
    stale_epochs = 0

    mlflow.set_experiment(config.experiment_name)
    with mlflow.start_run(run_name=config.experiment_name):
        mlflow.log_params(
            {
                "epochs": config.epochs,
                "learning_rate": config.learning_rate,
                "weight_decay": config.weight_decay,
                "task": task,
            }
        )

        for epoch in range(config.epochs):
            train_loss = _run_epoch(model, train_loader, optimizer, scaler, task=task, device=device, train=True)
            val_loss = _run_epoch(model, val_loader, optimizer, scaler, task=task, device=device, train=False)
            scheduler.step(val_loss)
            mlflow.log_metrics({"train_loss": train_loss, "val_loss": val_loss}, step=epoch)

            if val_loss < best_val:
                best_val = val_loss
                stale_epochs = 0
                torch.save({"state_dict": model.state_dict(), "epoch": epoch, "val_loss": val_loss}, best_path)
                mlflow.log_artifact(str(best_path))
            else:
                stale_epochs += 1
                if stale_epochs >= config.early_stopping_patience:
                    break

    return {"best_val_loss": best_val, "checkpoint": str(best_path)}


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scaler: torch.cuda.amp.GradScaler,
    *,
    task: str,
    device: str,
    train: bool,
) -> float:
    model.train(train)
    losses: list[float] = []
    context = torch.enable_grad() if train else torch.no_grad()
    with context:
        for batch in loader:
            primary = batch["primary"].to(device)
            target = batch["target"].to(device)
            mask = (torch.mean(target, dim=1, keepdim=True) > 0.5).float()
            if train:
                optimizer.zero_grad(set_to_none=True)

            with torch.cuda.amp.autocast(enabled=scaler.is_enabled()):
                if task == "segmentation":
                    logits = model(primary)
                    loss = F.binary_cross_entropy_with_logits(logits, mask)
                elif task == "super_resolution":
                    prediction = model(primary)
                    resized_target = F.interpolate(target, size=prediction.shape[-2:], mode="bilinear", align_corners=False)
                    loss = F.l1_loss(prediction, resized_target)
                else:
                    prediction = model(primary, mask)
                    loss = F.l1_loss(prediction, target) + 0.1 * F.mse_loss(prediction, target)

            if train:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()

            losses.append(float(loss.item()))

    return float(sum(losses) / max(len(losses), 1))
