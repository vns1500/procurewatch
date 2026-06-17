"""Daily database backup — pg_dump → compress → Cloudflare R2."""
from __future__ import annotations

import gzip
import io
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import structlog

from .celery_app import celery_app
from ..core.config import settings

logger = structlog.get_logger(__name__)


@celery_app.task(name="tasks.backup_tasks.backup_database")
def backup_database() -> None:
    log = logger.bind(task="backup_database")

    if not settings.is_production:
        log.info("skipping_backup_non_production")
        return

    if not settings.R2_ACCESS_KEY:
        log.warning("r2_not_configured_skipping_backup")
        return

    try:
        db_url = urlparse(settings.DATABASE_URL.replace("+asyncpg", ""))
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"procurewatch_backup_{timestamp}.sql.gz"

        env = {
            "PGPASSWORD": db_url.password or "",
            "PATH": "/usr/bin:/bin",
        }
        cmd = [
            "pg_dump",
            "-h", db_url.hostname or "localhost",
            "-p", str(db_url.port or 5432),
            "-U", db_url.username or "procure",
            "-d", db_url.path.lstrip("/"),
            "--no-password",
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, check=True)
        compressed = gzip.compress(result.stdout)
        log.info("dump_complete", bytes=len(compressed))

        import boto3
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
        )
        s3.upload_fileobj(
            io.BytesIO(compressed),
            settings.R2_BUCKET,
            f"backups/{filename}",
        )
        log.info("backup_uploaded", filename=filename, bucket=settings.R2_BUCKET)

        # Prune backups older than 30 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=settings.R2_BUCKET, Prefix="backups/"):
            for obj in page.get("Contents", []):
                if obj["LastModified"].replace(tzinfo=timezone.utc) < cutoff:
                    s3.delete_object(Bucket=settings.R2_BUCKET, Key=obj["Key"])
                    log.info("pruned_old_backup", key=obj["Key"])

    except Exception as exc:
        log.error("backup_failed", error=str(exc))
        # Alert via email on failure
        if settings.RESEND_API_KEY:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": settings.RESEND_FROM_EMAIL,
                    "to": "officialchidakash@gmail.com",
                    "subject": "ProcureWatch — DB backup FAILED",
                    "html": f"<pre>Backup failed: {exc}</pre>",
                })
            except Exception:
                pass
        raise
