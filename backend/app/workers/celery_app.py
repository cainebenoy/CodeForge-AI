"""
Celery application factory

Configures a Celery app with Redis as broker and result backend.
Uses the same REDIS_URL as the job store for consistency.

Task reliability features:
- task_acks_late: Tasks acknowledged only after completion (not on receipt)
- task_reject_on_worker_lost: Requeue tasks if the worker crashes
- task_time_limit: Hard kill after AGENT_TIMEOUT + buffer
- task_soft_time_limit: Raise SoftTimeLimitExceeded for graceful cleanup

Start worker:
    celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

Start monitoring:
    celery -A app.workers.celery_app flower --port=5555
"""

import os

from celery import Celery

# Load settings without importing the full Settings model
# (Celery workers are separate processes and may not need FastAPI)
_broker_url = os.environ.get(
    "CELERY_BROKER_URL",
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)
_result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND",
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)
_agent_timeout = int(os.environ.get("AGENT_TIMEOUT", "300"))

celery_app = Celery(
    "codeforge",
    broker=_broker_url,
    backend=_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    # Serialization — JSON only for safety (no pickle)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Reliability — ack after completion, requeue on worker crash
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Timeouts — prevent runaway tasks
    task_time_limit=_agent_timeout + 120,  # Hard kill: 7 min
    task_soft_time_limit=_agent_timeout + 60,  # Graceful: 6 min
    # Result expiry — clean up completed task results after 48h
    result_expires=48 * 3600,
    # Worker settings
    worker_prefetch_multiplier=1,  # Fair scheduling (1 task at a time per worker)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory leak guard)
    # Routing — default queue
    task_default_queue="codeforge",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Retry on connection loss
    broker_connection_retry_on_startup=True,
)
