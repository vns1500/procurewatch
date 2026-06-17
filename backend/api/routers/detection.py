"""Detection pipeline endpoint — POST /detection/run triggers full ML pipeline."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.tender import Tender
from models.vendor import Vendor
from models.anomaly import Anomaly
from models.price_benchmark import PriceBenchmark

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/detection", tags=["detection"])


class DetectionRunResponse(BaseModel):
    status: str
    task_id: str
    message: str


class DetectionResultSummary(BaseModel):
    tenders_scanned: int
    anomalies_created: int
    risk_scores_updated: int
    vendors_enriched: int
    duration_seconds: float


_run_status: dict[str, Any] = {}


async def _run_full_pipeline(task_id: str, db_factory: Any) -> None:
    import time
    from detection.pricing_model import PricingAnomalyDetector
    from detection.risk_aggregator import update_all_risk_scores, update_vendor_risk_levels
    from pipeline.mca_enrichment import enrich_all_vendors

    start = time.monotonic()
    _run_status[task_id] = {"status": "running", "started_at": start}

    async with db_factory() as db:
        try:
            # 1. Load all tenders for training
            tenders_result = await db.execute(select(Tender))
            tenders = tenders_result.scalars().all()

            benchmarks_result = await db.execute(select(PriceBenchmark))
            benchmarks = benchmarks_result.scalars().all()

            # 2. Train isolation forest
            detector = PricingAnomalyDetector()
            if not detector.load():
                detector.train(tenders)

            # 3. Score each tender with pricing model
            new_anomalies = 0
            for tender in tenders:
                anomaly = detector.score_tender(tender, benchmarks)
                if anomaly:
                    # Check not already detected
                    existing = await db.execute(
                        select(Anomaly).where(
                            Anomaly.tender_id == tender.id,
                            Anomaly.type == "inflated_pricing",
                        )
                    )
                    if existing.scalar_one_or_none() is None:
                        db.add(Anomaly(
                            id=anomaly["id"],
                            tender_id=anomaly["tender_id"],
                            type=anomaly["type"],
                            severity=anomaly["severity"],
                            evidence=anomaly["evidence"],
                            status="open",
                        ))
                        new_anomalies += 1

            await db.commit()

            # 4. Recompute all risk scores
            updated = await update_all_risk_scores(db)
            await update_vendor_risk_levels(db)

            # 5. Enrich vendors
            vendors_enriched = await enrich_all_vendors(db)

            elapsed = time.monotonic() - start
            _run_status[task_id] = {
                "status": "completed",
                "result": DetectionResultSummary(
                    tenders_scanned=len(tenders),
                    anomalies_created=new_anomalies,
                    risk_scores_updated=updated,
                    vendors_enriched=vendors_enriched,
                    duration_seconds=round(elapsed, 2),
                ).model_dump(),
            }
            logger.info("detection_pipeline_complete", task_id=task_id, duration=elapsed)

        except Exception as exc:
            logger.exception("detection_pipeline_error", task_id=task_id, error=str(exc))
            _run_status[task_id] = {"status": "failed", "error": str(exc)}


@router.post("/run", response_model=DetectionRunResponse)
async def run_detection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> DetectionRunResponse:
    from core.database import AsyncSessionLocal

    task_id = str(uuid.uuid4())
    _run_status[task_id] = {"status": "queued"}

    background_tasks.add_task(_run_full_pipeline, task_id, AsyncSessionLocal)
    logger.info("detection_pipeline_queued", task_id=task_id)

    return DetectionRunResponse(
        status="queued",
        task_id=task_id,
        message="Full detection pipeline started in background",
    )


@router.get("/run/{task_id}")
async def get_run_status(task_id: str) -> dict[str, Any]:
    status = _run_status.get(task_id)
    if status is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, **status}
