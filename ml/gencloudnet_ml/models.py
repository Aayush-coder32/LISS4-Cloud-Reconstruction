from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import Tensor, nn


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.0) -> None:
        super().__init__()
        layers: list[nn.Module] = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
        ]
        if dropout > 0:
            layers.append(nn.Dropout2d(dropout))
        self.block = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.block(x)


class ResidualBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.GELU(),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )

    def forward(self, x: Tensor) -> Tensor:
        return F.gelu(x + self.layers(x))


class DownBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.pool = nn.MaxPool2d(2)
        self.block = ConvBlock(in_channels, out_channels)

    def forward(self, x: Tensor) -> Tensor:
        return self.block(self.pool(x))


class UpBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.block = ConvBlock(out_channels + skip_channels, out_channels)

    def forward(self, x: Tensor, skip: Tensor) -> Tensor:
        x = self.up(x)
        if x.shape[-2:] != skip.shape[-2:]:
            x = F.interpolate(x, size=skip.shape[-2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.block(x)


class UNet(nn.Module):
    def __init__(self, in_channels: int = 4, out_channels: int = 1, base_channels: int = 32) -> None:
        super().__init__()
        self.enc1 = ConvBlock(in_channels, base_channels)
        self.enc2 = DownBlock(base_channels, base_channels * 2)
        self.enc3 = DownBlock(base_channels * 2, base_channels * 4)
        self.enc4 = DownBlock(base_channels * 4, base_channels * 8)
        self.bottleneck = DownBlock(base_channels * 8, base_channels * 16)
        self.dec4 = UpBlock(base_channels * 16, base_channels * 8, base_channels * 8)
        self.dec3 = UpBlock(base_channels * 8, base_channels * 4, base_channels * 4)
        self.dec2 = UpBlock(base_channels * 4, base_channels * 2, base_channels * 2)
        self.dec1 = UpBlock(base_channels * 2, base_channels, base_channels)
        self.head = nn.Conv2d(base_channels, out_channels, kernel_size=1)

    def forward(self, x: Tensor) -> Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        bottleneck = self.bottleneck(e4)
        d4 = self.dec4(bottleneck, e4)
        d3 = self.dec3(d4, e3)
        d2 = self.dec2(d3, e2)
        d1 = self.dec1(d2, e1)
        return self.head(d1)


class NestedUNet(nn.Module):
    def __init__(self, in_channels: int = 4, out_channels: int = 1, base_channels: int = 32) -> None:
        super().__init__()
        self.x00 = ConvBlock(in_channels, base_channels)
        self.x10 = DownBlock(base_channels, base_channels * 2)
        self.x20 = DownBlock(base_channels * 2, base_channels * 4)
        self.x30 = DownBlock(base_channels * 4, base_channels * 8)
        self.x01 = ConvBlock(base_channels + base_channels * 2, base_channels)
        self.x11 = ConvBlock(base_channels * 2 + base_channels * 4, base_channels * 2)
        self.x21 = ConvBlock(base_channels * 4 + base_channels * 8, base_channels * 4)
        self.x02 = ConvBlock(base_channels * 2 + base_channels * 2, base_channels)
        self.x12 = ConvBlock(base_channels * 4 + base_channels * 4, base_channels * 2)
        self.x03 = ConvBlock(base_channels * 3 + base_channels * 2, base_channels)
        self.out = nn.Conv2d(base_channels, out_channels, kernel_size=1)

    def forward(self, x: Tensor) -> Tensor:
        x00 = self.x00(x)
        x10 = self.x10(x00)
        x20 = self.x20(x10)
        x30 = self.x30(x20)

        x01 = self.x01(torch.cat([x00, F.interpolate(x10, x00.shape[-2:], mode="bilinear", align_corners=False)], dim=1))
        x11 = self.x11(torch.cat([x10, F.interpolate(x20, x10.shape[-2:], mode="bilinear", align_corners=False)], dim=1))
        x21 = self.x21(torch.cat([x20, F.interpolate(x30, x20.shape[-2:], mode="bilinear", align_corners=False)], dim=1))

        x02 = self.x02(
            torch.cat(
                [x00, x01, F.interpolate(x11, x00.shape[-2:], mode="bilinear", align_corners=False)],
                dim=1,
            )
        )
        x12 = self.x12(
            torch.cat(
                [x10, x11, F.interpolate(x21, x10.shape[-2:], mode="bilinear", align_corners=False)],
                dim=1,
            )
        )
        x03 = self.x03(
            torch.cat(
                [x00, x01, x02, F.interpolate(x12, x00.shape[-2:], mode="bilinear", align_corners=False)],
                dim=1,
            )
        )
        return self.out(x03)


class ASPP(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        dilations = (1, 6, 12, 18)
        self.branches = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Conv2d(
                        in_channels,
                        out_channels,
                        kernel_size=1 if dilation == 1 else 3,
                        padding=0 if dilation == 1 else dilation,
                        dilation=dilation,
                        bias=False,
                    ),
                    nn.BatchNorm2d(out_channels),
                    nn.GELU(),
                )
                for dilation in dilations
            ]
        )
        self.project = nn.Sequential(
            nn.Conv2d(out_channels * len(dilations), out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
        )

    def forward(self, x: Tensor) -> Tensor:
        features = [branch(x) for branch in self.branches]
        return self.project(torch.cat(features, dim=1))


class DeepLabV3PlusLite(nn.Module):
    def __init__(self, in_channels: int = 4, out_channels: int = 1, base_channels: int = 48) -> None:
        super().__init__()
        self.low_level = ConvBlock(in_channels, base_channels)
        self.encoder = nn.Sequential(
            DownBlock(base_channels, base_channels * 2),
            DownBlock(base_channels * 2, base_channels * 4),
        )
        self.aspp = ASPP(base_channels * 4, base_channels * 4)
        self.decoder = nn.Sequential(
            nn.Conv2d(base_channels * 5, base_channels * 2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(base_channels * 2),
            nn.GELU(),
            nn.Conv2d(base_channels * 2, out_channels, kernel_size=1),
        )

    def forward(self, x: Tensor) -> Tensor:
        low_level = self.low_level(x)
        encoded = self.encoder(low_level)
        context = self.aspp(encoded)
        upsampled = F.interpolate(context, size=low_level.shape[-2:], mode="bilinear", align_corners=False)
        return self.decoder(torch.cat([low_level, upsampled], dim=1))


class PatchEmbedding(nn.Module):
    def __init__(self, in_channels: int, embed_dim: int, patch_size: int = 4) -> None:
        super().__init__()
        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x: Tensor) -> tuple[Tensor, tuple[int, int]]:
        x = self.proj(x)
        height, width = x.shape[-2:]
        return x.flatten(2).transpose(1, 2), (height, width)


class TransformerEncoderBlock(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int = 4, mlp_ratio: float = 4.0, dropout: float = 0.1) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, int(embed_dim * mlp_ratio)),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(int(embed_dim * mlp_ratio), embed_dim),
        )

    def forward(self, x: Tensor) -> Tensor:
        attn_input = self.norm1(x)
        attn_output, _ = self.attn(attn_input, attn_input, attn_input, need_weights=False)
        x = x + attn_output
        x = x + self.mlp(self.norm2(x))
        return x


class SegFormerLite(nn.Module):
    def __init__(self, in_channels: int = 4, out_channels: int = 1, embed_dim: int = 64) -> None:
        super().__init__()
        self.patch = PatchEmbedding(in_channels, embed_dim, patch_size=4)
        self.blocks = nn.ModuleList([TransformerEncoderBlock(embed_dim) for _ in range(4)])
        self.decode = nn.Sequential(
            nn.Conv2d(embed_dim, embed_dim, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.GELU(),
            nn.Conv2d(embed_dim, out_channels, kernel_size=1),
        )

    def forward(self, x: Tensor) -> Tensor:
        tokens, (height, width) = self.patch(x)
        for block in self.blocks:
            tokens = block(tokens)
        feature_map = tokens.transpose(1, 2).reshape(x.shape[0], -1, height, width)
        logits = self.decode(feature_map)
        return F.interpolate(logits, size=x.shape[-2:], mode="bilinear", align_corners=False)


class Mask2FormerLite(nn.Module):
    def __init__(self, in_channels: int = 4, out_channels: int = 1, embed_dim: int = 64, num_queries: int = 8) -> None:
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, embed_dim, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.GELU(),
        )
        self.transformer = nn.ModuleList([TransformerEncoderBlock(embed_dim) for _ in range(3)])
        self.queries = nn.Parameter(torch.randn(num_queries, embed_dim))
        self.cross_attn = nn.MultiheadAttention(embed_dim, num_heads=4, batch_first=True)
        self.mask_proj = nn.Linear(embed_dim, out_channels)

    def forward(self, x: Tensor) -> Tensor:
        features = self.stem(x)
        tokens = features.flatten(2).transpose(1, 2)
        for block in self.transformer:
            tokens = block(tokens)
        query_tokens = self.queries.unsqueeze(0).expand(x.shape[0], -1, -1)
        attended, _ = self.cross_attn(query_tokens, tokens, tokens, need_weights=False)
        mask_logits = self.mask_proj(attended).mean(dim=1).view(x.shape[0], -1, 1, 1)
        mask_logits = mask_logits.expand(-1, -1, features.shape[-2], features.shape[-1])
        return F.interpolate(mask_logits, size=x.shape[-2:], mode="bilinear", align_corners=False)


class TemporalTransformerFusion(nn.Module):
    def __init__(self, channels: int = 4, embed_dim: int = 64, grid_size: int = 8) -> None:
        super().__init__()
        self.channels = channels
        self.grid_size = grid_size
        self.proj = nn.Linear(channels, embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=4,
            dim_feedforward=embed_dim * 4,
            activation="gelu",
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.head = nn.Linear(embed_dim, channels)

    def forward(self, primary: Tensor, temporal: Tensor) -> Tensor:
        if temporal.ndim != 5:
            raise ValueError("Temporal input must have shape [B, T, C, H, W]")
        batch_size, time_steps, _, _, _ = temporal.shape
        stacked = torch.cat([primary.unsqueeze(1), temporal], dim=1)
        pooled = F.adaptive_avg_pool2d(stacked.view(-1, self.channels, primary.shape[-2], primary.shape[-1]), (self.grid_size, self.grid_size))
        pooled = pooled.view(batch_size, time_steps + 1, self.channels, self.grid_size * self.grid_size).permute(0, 3, 1, 2)
        tokens = self.proj(pooled.reshape(batch_size * self.grid_size * self.grid_size, time_steps + 1, self.channels))
        encoded = self.encoder(tokens)
        fused = self.head(encoded.mean(dim=1))
        fused = fused.view(batch_size, self.grid_size * self.grid_size, self.channels).permute(0, 2, 1)
        fused = fused.view(batch_size, self.channels, self.grid_size, self.grid_size)
        return F.interpolate(fused, size=primary.shape[-2:], mode="bilinear", align_corners=False)


class SensorFusionTransformer(nn.Module):
    def __init__(self, optical_channels: int = 4, sar_channels: int = 1, embed_dim: int = 64) -> None:
        super().__init__()
        self.optical_proj = nn.Conv2d(optical_channels, embed_dim, kernel_size=3, padding=1)
        self.sar_proj = nn.Conv2d(sar_channels, embed_dim, kernel_size=3, padding=1)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads=4, batch_first=True)
        self.out = nn.Conv2d(embed_dim, optical_channels, kernel_size=1)

    def forward(self, optical: Tensor, sar: Tensor) -> Tensor:
        if sar.shape[-2:] != optical.shape[-2:]:
            sar = F.interpolate(sar, size=optical.shape[-2:], mode="bilinear", align_corners=False)
        optical_tokens = self.optical_proj(optical).flatten(2).transpose(1, 2)
        sar_tokens = self.sar_proj(sar).flatten(2).transpose(1, 2)
        attended, _ = self.attn(optical_tokens, sar_tokens, sar_tokens, need_weights=False)
        fused = attended.transpose(1, 2).reshape(optical.shape[0], -1, optical.shape[-2], optical.shape[-1])
        return self.out(fused)


class FeatureExtractor(nn.Module):
    def __init__(self, mode: str = "vit", in_channels: int = 4, embed_dim: int = 96) -> None:
        super().__init__()
        self.mode = mode
        if mode == "vit":
            self.backbone = nn.Sequential(
                nn.Conv2d(in_channels, embed_dim, kernel_size=4, stride=4),
                nn.GELU(),
                nn.Conv2d(embed_dim, embed_dim, kernel_size=3, padding=1),
            )
        elif mode == "swin":
            self.backbone = nn.Sequential(
                nn.Conv2d(in_channels, embed_dim, kernel_size=3, padding=1),
                ResidualBlock(embed_dim),
                nn.AvgPool2d(2),
                ResidualBlock(embed_dim),
            )
        else:
            self.backbone = nn.Sequential(
                nn.Conv2d(in_channels, embed_dim, kernel_size=7, padding=3),
                nn.GELU(),
                ResidualBlock(embed_dim),
                ResidualBlock(embed_dim),
            )

    def forward(self, x: Tensor) -> Tensor:
        return self.backbone(x)


class ResidualInpaintGenerator(nn.Module):
    def __init__(self, channels: int = 4, base_channels: int = 64, blocks: int = 6) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(channels + 1, base_channels, kernel_size=7, padding=3),
            nn.GELU(),
            nn.Conv2d(base_channels, base_channels * 2, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.Conv2d(base_channels * 2, base_channels * 4, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
        )
        self.bottleneck = nn.Sequential(*[ResidualBlock(base_channels * 4) for _ in range(blocks)])
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(base_channels * 4, base_channels * 2, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.ConvTranspose2d(base_channels * 2, base_channels, kernel_size=4, stride=2, padding=1),
            nn.GELU(),
            nn.Conv2d(base_channels, channels, kernel_size=7, padding=3),
            nn.Sigmoid(),
        )

    def forward(self, image: Tensor, mask: Tensor) -> Tensor:
        if mask.ndim == 3:
            mask = mask.unsqueeze(1)
        x = torch.cat([image, mask], dim=1)
        return self.decoder(self.bottleneck(self.encoder(x)))


class Pix2PixHDLite(ResidualInpaintGenerator):
    def __init__(self, channels: int = 4) -> None:
        super().__init__(channels=channels, base_channels=64, blocks=9)


class CycleGANGenerator(ResidualInpaintGenerator):
    def __init__(self, channels: int = 4) -> None:
        super().__init__(channels=channels, base_channels=48, blocks=6)


class DiffusionInpainter:
    def __init__(self, model_id: str, checkpoint: str | None = None) -> None:
        from diffusers import AutoPipelineForInpainting

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        source = checkpoint if checkpoint and Path(checkpoint).exists() else model_id
        self.pipeline = AutoPipelineForInpainting.from_pretrained(source, torch_dtype=torch.float16 if self.device == "cuda" else torch.float32)
        self.pipeline.to(self.device)

    def inpaint(self, image: np.ndarray, mask: np.ndarray, prompt: str = "reconstruct cloud-free satellite imagery") -> np.ndarray:
        image_uint8 = np.clip(image.transpose(1, 2, 0) * 255.0, 0, 255).astype(np.uint8)
        mask_uint8 = np.clip(mask * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_uint8[:, :, :3])
        pil_mask = Image.fromarray(mask_uint8)
        result = self.pipeline(prompt=prompt, image=pil_image, mask_image=pil_mask).images[0]
        array = np.asarray(result).astype(np.float32) / 255.0
        if image.shape[0] > 3:
            extra_channels = np.repeat(array[..., :1], image.shape[0] - 3, axis=-1)
            array = np.concatenate([array, extra_channels], axis=-1)
        return array.transpose(2, 0, 1)


class RRDBBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.layers = nn.ModuleList([nn.Conv2d(channels, channels, kernel_size=3, padding=1) for _ in range(3)])

    def forward(self, x: Tensor) -> Tensor:
        residual = x
        for layer in self.layers:
            x = F.gelu(layer(x))
        return residual + 0.2 * x


class RRDBNetLite(nn.Module):
    def __init__(self, channels: int = 4, features: int = 64, upscale: int = 2) -> None:
        super().__init__()
        self.upscale = upscale
        self.head = nn.Conv2d(channels, features, kernel_size=3, padding=1)
        self.body = nn.Sequential(*[RRDBBlock(features) for _ in range(5)])
        self.tail = nn.Sequential(
            nn.Conv2d(features, features * upscale * upscale, kernel_size=3, padding=1),
            nn.PixelShuffle(upscale),
            nn.GELU(),
            nn.Conv2d(features, channels, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x: Tensor) -> Tensor:
        features = self.head(x)
        enhanced = self.body(features)
        return self.tail(enhanced + features)


class SwinIRLite(nn.Module):
    def __init__(self, channels: int = 4, embed_dim: int = 64, upscale: int = 2) -> None:
        super().__init__()
        self.upscale = upscale
        self.embed = nn.Conv2d(channels, embed_dim, kernel_size=3, padding=1)
        self.blocks = nn.ModuleList([TransformerEncoderBlock(embed_dim, num_heads=4) for _ in range(4)])
        self.out = nn.Sequential(
            nn.Conv2d(embed_dim, embed_dim * upscale * upscale, kernel_size=3, padding=1),
            nn.PixelShuffle(upscale),
            nn.GELU(),
            nn.Conv2d(embed_dim, channels, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x: Tensor) -> Tensor:
        feature = self.embed(x)
        batch_size, channels, height, width = feature.shape
        tokens = feature.flatten(2).transpose(1, 2)
        for block in self.blocks:
            tokens = block(tokens)
        tokens = tokens.transpose(1, 2).reshape(batch_size, channels, height, width)
        return self.out(tokens)


def _load_checkpoint(module: nn.Module, checkpoint_path: str | None) -> nn.Module:
    if checkpoint_path and Path(checkpoint_path).exists():
        state = torch.load(checkpoint_path, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        module.load_state_dict(state, strict=False)
    return module


def get_cloud_model(name: str, in_channels: int = 4) -> nn.Module:
    registry = {
        "unet": UNet(in_channels=in_channels, out_channels=1),
        "unetpp": NestedUNet(in_channels=in_channels, out_channels=1),
        "deeplabv3p": DeepLabV3PlusLite(in_channels=in_channels, out_channels=1),
        "segformer": SegFormerLite(in_channels=in_channels, out_channels=1),
        "mask2former": Mask2FormerLite(in_channels=in_channels, out_channels=1),
    }
    if name not in registry:
        raise KeyError(f"Unknown cloud model: {name}")
    return registry[name]


def get_generator(name: str, channels: int = 4, checkpoint_path: str | None = None):
    if name == "pix2pixhd":
        return _load_checkpoint(Pix2PixHDLite(channels=channels), checkpoint_path)
    if name == "cyclegan":
        return _load_checkpoint(CycleGANGenerator(channels=channels), checkpoint_path)
    if name == "latent_diffusion":
        return DiffusionInpainter("stabilityai/stable-diffusion-2-inpainting", checkpoint=checkpoint_path)
    if name == "stable_diffusion":
        return DiffusionInpainter("runwayml/stable-diffusion-inpainting", checkpoint=checkpoint_path)
    raise KeyError(f"Unknown generator model: {name}")


def get_super_resolution_model(name: str, channels: int = 4, checkpoint_path: str | None = None) -> nn.Module:
    if name == "realesrgan":
        return _load_checkpoint(RRDBNetLite(channels=channels), checkpoint_path)
    if name == "swinir":
        return _load_checkpoint(SwinIRLite(channels=channels), checkpoint_path)
    raise KeyError(f"Unknown super-resolution model: {name}")
