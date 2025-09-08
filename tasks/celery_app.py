# -*- coding: utf-8 -*-
import os
from celery import Celery

# Variáveis de ambiente
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "gemini_tasks",
    broker=REDIS_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=60 * 20,  # 20 minutos
    task_soft_time_limit=60 * 15,
    worker_prefetch_multiplier=1,
)

__all__ = ["celery_app"]
