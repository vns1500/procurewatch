from celery import Celery
from celery.schedules import crontab
from ..core.config import settings

celery = Celery(
    "procurewatch",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.tasks.scrape_tasks", "backend.tasks.backup_tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "scrape-gem-daily": {
            "task": "backend.tasks.scrape_tasks.scrape_gem_task",
            "schedule": crontab(hour=2, minute=0),   # 2 AM IST
        },
        "run-detection-hourly": {
            "task": "backend.tasks.scrape_tasks.run_detection_task",
            "schedule": crontab(minute=30),           # :30 every hour
        },
        "backup-daily": {
            "task": "tasks.backup_tasks.backup_database",
            "schedule": crontab(hour=1, minute=0),   # 1 AM IST, before scrape
        },
    },
)
