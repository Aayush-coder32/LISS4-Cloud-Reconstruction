# Deployment Guide

## Local stack

1. Copy `.env.example` to `.env`.
2. Build and start services with `docker compose up --build`.
3. Access:
   - Web: `http://localhost:3000`
   - API: `http://localhost:8000/docs`
   - NGINX gateway: `http://localhost`
   - MLflow: `http://localhost:5000`

## Cloud deployment notes

- Run API and worker from the same image to keep model and preprocessing code aligned.
- Back artifacts with object storage and mount a persistent checkpoint volume.
- Put PostgreSQL on managed Postgres with PostGIS enabled.
- Use Redis as the Celery broker and result backend.
- Terminate TLS at NGINX, a cloud load balancer, or an ingress controller.

## Kubernetes shape

- `frontend` deployment + service
- `backend` deployment + service
- `worker` deployment
- `postgres` statefulset or managed database
- `redis` deployment
- `mlflow` deployment
- `nginx` ingress or gateway
