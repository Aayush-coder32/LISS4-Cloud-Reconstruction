from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from gencloudnet_ml.preprocessing import normalize_percentile, read_raster, resize_image


class RasterTemporalDataset(Dataset):
    def __init__(self, manifest_csv: str | Path, patch_size: int = 256, augment: bool = True) -> None:
        self.records = pd.read_csv(manifest_csv).fillna("")
        self.patch_size = patch_size
        self.augment = augment
        self.transform = self._build_transform() if augment else None

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.records.iloc[index]
        primary, _ = read_raster(row["primary"])
        target, _ = read_raster(row["target"])

        temporal_columns = [column for column in self.records.columns if column.startswith("temporal_")]
        temporal = [read_raster(row[column])[0] for column in temporal_columns if row[column]]
        sar = read_raster(row["sar"])[0] if "sar" in row and row["sar"] else None

        primary = resize_image(normalize_percentile(primary), (self.patch_size, self.patch_size))
        target = resize_image(normalize_percentile(target), (self.patch_size, self.patch_size))
        temporal_stack = np.stack(
            [resize_image(normalize_percentile(item), (self.patch_size, self.patch_size)) for item in temporal],
            axis=0,
        ) if temporal else np.zeros((0, primary.shape[0], self.patch_size, self.patch_size), dtype=np.float32)
        sar_tensor = resize_image(normalize_percentile(sar), (self.patch_size, self.patch_size)) if sar is not None else np.zeros_like(primary[:1])

        sample = {
            "primary": primary.transpose(1, 2, 0),
            "target": target.transpose(1, 2, 0),
        }
        if self.transform is not None:
            transformed = self.transform(image=sample["primary"], mask=sample["target"])
            sample["primary"] = transformed["image"]
            sample["target"] = transformed["mask"]

        primary_tensor = torch.from_numpy(np.asarray(sample["primary"]).transpose(2, 0, 1)).float()
        target_tensor = torch.from_numpy(np.asarray(sample["target"]).transpose(2, 0, 1)).float()

        return {
            "primary": primary_tensor,
            "temporal": torch.from_numpy(temporal_stack).float(),
            "sar": torch.from_numpy(sar_tensor).float(),
            "target": target_tensor,
        }

    def _build_transform(self):
        try:
            import albumentations as A
        except ImportError:
            return None
        return A.Compose(
            [
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.RandomBrightnessContrast(p=0.3),
                A.GaussNoise(p=0.2),
            ]
        )
