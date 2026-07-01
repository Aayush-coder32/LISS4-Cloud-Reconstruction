# GenCloudNet

GenCloudNet is a full-stack geospatial AI platform for cloud detection, multi-temporal fusion, reconstruction, super-resolution, explainability, and deployment of cloud-free satellite imagery workflows for LISS-IV, Sentinel, Landsat, and GeoTIFF datasets.

## What is included

- FastAPI backend with JWT auth, Google OAuth hooks, upload ingestion, metadata extraction, inference APIs, history, and metrics.
- PyTorch ML package with preprocessing, segmentation, fusion, reconstruction, confidence estimation, explainability, evaluation, and training utilities.
- Next.js 15 frontend with an operator dashboard, upload workflow, history view, and geospatial visualization.
- Docker Compose stack with PostGIS, Redis, API, worker, frontend, NGINX, and MLflow.
- Tests, CI, architecture notes, deployment guide, and schema documentation.

## Monorepo layout

```text
backend/   FastAPI API, repositories, services, worker
ml/        Research and training package
frontend/  Next.js 15 application
infra/     Docker and reverse proxy
docs/      Architecture and deployment notes
```

## Quick start

1. Copy `.env.example` to `.env`.
2. Start the stack with `docker compose up --build`.
3. Open `http://localhost:3000` for the web app and `http://localhost:8000/docs` for the API.

## Core workflow

1. Upload a GeoTIFF, PNG, or multi-band raster.
2. Extract geospatial metadata and preview imagery.
3. Detect clouds and create a cloud mask.
4. Fuse temporal and SAR context.
5. Reconstruct cloud-covered regions.
6. Enhance and optionally super-resolve the output.
7. Generate confidence maps, explainability layers, and metrics.

## Notes

- The online inference pipeline is deterministic out of the box through temporal fusion and classical inpainting, and can optionally load trained deep models when checkpoints are provided.
- The ML package includes trainable architectures for U-Net style segmentation, transformer fusion, GAN-based reconstruction, and lightweight super-resolution.
