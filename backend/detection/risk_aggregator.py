"""Composite risk score aggregator."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RISK_CONTRIBUTIONS: dict[str, int] = {
    "post_award_inflation": 55,
    "shell_vendor": 50,
    "director_overlap": 45,
    "inflated_pricing": 40,
    "repeat_monopoly": 40,
    "bid_splitting": 40,
    "spec_tailoring": 35,
    "single_bid": 35,
    "rushed_timeline": 30,
    "geo_mismatch": 20,
}


async def compute_final_risk_score(tender_id: uuid.UUID, db: "AsyncSession") -> int:
    from sqlalchemy import select
    from ..models.anomaly import Anomaly

    result = await db.execute(
        select(Anomaly).where(Anomaly.tender_id == tender_id, Anomaly.status != "false_positive")
    )
    anomalies = result.scalars().all()

    total = 0
    for a in anomalies:
        total += RISK_CONTRIBUTIONS.get(a.type, 15)

    return min(total, 100)


async def update_all_risk_scores(db: "AsyncSession") -> int:
    """Recompute and persist risk scores for all tenders. Returns count updated."""
    from sqlalchemy import select, text
    from ..models.tender import Tender
    from ..models.anomaly import Anomaly

    tender_result = await db.execute(select(Tender.id))
    tender_ids = [row[0] for row in tender_result.all()]

    updated = 0
    for tid in tender_ids:
        score = await compute_final_risk_score(tid, db)

        flags_result = await db.execute(
            select(Anomaly.type)
            .where(Anomaly.tender_id == tid, Anomaly.status != "false_positive")
            .distinct()
        )
        flags = [row[0] for row in flags_result.all()]

        await db.execute(
            text("UPDATE tenders SET risk_score = :s, anomaly_flags = cast(:f as varchar[]) WHERE id = :tid"),
            {"s": score, "f": flags, "tid": str(tid)},
        )
        updated += 1

    await db.commit()
    logger.info("risk_scores_updated", count=updated)
    return updated


async def update_vendor_risk_levels(db: "AsyncSession") -> int:
    """Recompute vendor risk_level from avg tender risk scores."""
    from sqlalchemy import text

    await db.execute(text("""
        UPDATE vendors v
        SET risk_level = CASE
            WHEN avg_score >= 80 THEN 'critical'
            WHEN avg_score >= 60 THEN 'high'
            WHEN avg_score >= 40 THEN 'medium'
            ELSE 'low'
        END
        FROM (
            SELECT winner_vendor_id,
                   AVG(risk_score) AS avg_score
            FROM tenders
            WHERE winner_vendor_id IS NOT NULL
            GROUP BY winner_vendor_id
        ) sub
        WHERE v.id = sub.winner_vendor_id
    """))
    await db.commit()
    logger.info("vendor_risk_levels_updated")
    return 1
