from __future__ import annotations

import argparse

from torch.utils.data import DataLoader, random_split

from gencloudnet_ml.datasets import RasterTemporalDataset
from gencloudnet_ml.models import (
    Pix2PixHDLite,
    RRDBNetLite,
    UNet,
    get_cloud_model,
)
from gencloudnet_ml.trainer import TrainingConfig, train_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train GenCloudNet models")
    parser.add_argument("--manifest", required=True, help="Path to CSV manifest")
    parser.add_argument("--task", choices=["segmentation", "reconstruction", "super_resolution"], default="segmentation")
    parser.add_argument("--model", default="unet", help="Model name")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--patch-size", type=int, default=256)
    parser.add_argument("--checkpoint-dir", default="artifacts/checkpoints")
    return parser.parse_args()


def build_model(task: str, model_name: str):
    if task == "segmentation":
        return get_cloud_model(model_name)
    if task == "super_resolution":
        return RRDBNetLite()
    return Pix2PixHDLite()


def main() -> None:
    args = parse_args()
    dataset = RasterTemporalDataset(args.manifest, patch_size=args.patch_size)
    train_size = int(len(dataset) * 0.8)
    val_size = max(len(dataset) - train_size, 1)
    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = build_model(args.task, args.model)
    config = TrainingConfig(
        experiment_name=f"{args.task}-{args.model}",
        epochs=args.epochs,
        checkpoint_dir=args.checkpoint_dir,
    )
    result = train_model(model, train_loader, val_loader, config, task=args.task)
    print(result)


if __name__ == "__main__":
    main()
