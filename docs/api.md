# API Surface

## Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/token`
- `GET /api/v1/auth/google/login`
- `GET /api/v1/auth/google/callback`
- `GET /api/v1/auth/me`

## Assets

- `POST /api/v1/uploads`
- `GET /api/v1/uploads`

## Inference

- `POST /api/v1/predict`
- `POST /api/v1/cloud-mask`
- `POST /api/v1/fusion`
- `POST /api/v1/super-resolution`

## Monitoring

- `GET /api/v1/history`
- `GET /api/v1/metrics`
- `GET /healthz`
