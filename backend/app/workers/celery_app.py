from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("gencloudnet", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
