from __future__ import annotations

from datetime import date, timedelta

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.tender import Tender
from models.anomaly import Anomaly

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class MinistryRisk(BaseModel):
    ministry: str
    count: int
    total_value: int


class AnomalyBreakdown(BaseModel):
    type: str
    count: int


class StateRisk(BaseModel):
    state: str
    risk_score: float
    flagged_count: int


class DashboardStats(BaseModel):
    flagged_this_month: int
    suspicious_value: int
    new_anomalies_today: int
    total_tenders_scanned: int
    top_risky_ministries: list[MinistryRisk]
    anomaly_breakdown: list[AnomalyBreakdown]
    state_risk_map: list[StateRisk]


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    log = logger.bind(endpoint="dashboard_stats")

    today = date.today()
    month_start = today.replace(day=1)

    # Flagged this month — use created_at (ingestion date) so synthetic data works
    flagged_q = await db.execute(
        select(func.count())
        .select_from(Tender)
        .where(Tender.risk_score > 0)
        .where(func.date(Tender.created_at) >= month_start)
    )
    flagged_this_month = flagged_q.scalar_one()

    # Total suspicious value (flagged tenders)
    value_q = await db.execute(
        select(func.coalesce(func.sum(Tender.value), 0))
        .select_from(Tender)
        .where(Tender.risk_score > 0)
    )
    suspicious_value = value_q.scalar_one()

    # New anomalies today
    anomalies_today_q = await db.execute(
        select(func.count())
        .select_from(Anomaly)
        .where(func.date(Anomaly.detected_at) == today)
    )
    new_anomalies_today = anomalies_today_q.scalar_one()

    # Total tenders scanned
    total_q = await db.execute(select(func.count()).select_from(Tender))
    total_tenders_scanned = total_q.scalar_one()

    # Top 5 risky ministries
    top_ministry_q = await db.execute(
        select(
            Tender.ministry,
            func.count(Tender.id).label("count"),
            func.coalesce(func.sum(Tender.value), 0).label("total_value"),
        )
        .where(Tender.risk_score > 0)
        .group_by(Tender.ministry)
        .order_by(func.count(Tender.id).desc())
        .limit(5)
    )
    top_risky_ministries = [
        MinistryRisk(ministry=row.ministry, count=row.count, total_value=row.total_value)
        for row in top_ministry_q.all()
    ]

    # Anomaly breakdown by type
    breakdown_q = await db.execute(
        select(Anomaly.type, func.count(Anomaly.id).label("count"))
        .group_by(Anomaly.type)
        .order_by(func.count(Anomaly.id).desc())
    )
    anomaly_breakdown = [
        AnomalyBreakdown(type=row.type, count=row.count)
        for row in breakdown_q.all()
    ]

    # State risk map
    state_q = await db.execute(
        select(
            Tender.state,
            func.avg(Tender.risk_score).label("risk_score"),
            func.count(Tender.id).filter(Tender.risk_score > 0).label("flagged_count"),
        )
        .group_by(Tender.state)
        .order_by(func.avg(Tender.risk_score).desc())
    )
    state_risk_map = [
        StateRisk(
            state=row.state,
            risk_score=float(row.risk_score or 0),
            flagged_count=int(row.flagged_count or 0),
        )
        for row in state_q.all()
    ]

    log.info("dashboard_stats_served",
             flagged_this_month=flagged_this_month,
             total_tenders=total_tenders_scanned)

    return DashboardStats(
        flagged_this_month=flagged_this_month,
        suspicious_value=int(suspicious_value),
        new_anomalies_today=new_anomalies_today,
        total_tenders_scanned=total_tenders_scanned,
        top_risky_ministries=top_risky_ministries,
        anomaly_breakdown=anomaly_breakdown,
        state_risk_map=state_risk_map,
    )
