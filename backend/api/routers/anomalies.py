from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.anomaly import Anomaly
from ...models.tender import Tender

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/anomalies", tags=["anomalies"])


class AnomalyDetail(BaseModel):
    id: uuid.UUID
    type: str
    severity: str
    evidence: dict[str, Any] | None
    detected_at: Any
    status: str
    tender_id: uuid.UUID
    tender_title: str
    ministry: str
    risk_score: int


class AnomalyListResponse(BaseModel):
    anomalies: list[AnomalyDetail]
    total: int
    page: int
    limit: int


class AnomalyStatusUpdate(BaseModel):
    status: str  # open | investigating | resolved | false_positive


@router.patch("/{anomaly_id}", response_model=AnomalyDetail)
async def update_anomaly_status(
    anomaly_id: uuid.UUID,
    body: AnomalyStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> AnomalyDetail:
    valid = {"open", "investigating", "resolved", "false_positive"}
    if body.status not in valid:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"status must be one of {valid}")

    result = await db.execute(
        select(Anomaly, Tender.title, Tender.ministry, Tender.risk_score)
        .join(Tender, Anomaly.tender_id == Tender.id)
        .where(Anomaly.id == anomaly_id)
    )
    row = result.first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Anomaly not found")

    row[0].status = body.status
    await db.commit()
    await db.refresh(row[0])

    return AnomalyDetail(
        id=row[0].id,
        type=row[0].type,
        severity=row[0].severity,
        evidence=row[0].evidence,
        detected_at=row[0].detected_at,
        status=row[0].status,
        tender_id=row[0].tender_id,
        tender_title=row[1],
        ministry=row[2],
        risk_score=row[3] or 0,
    )


@router.get("", response_model=AnomalyListResponse)
async def list_anomalies(
    type: str | None = Query(None),
    severity: str | None = Query(None),
    ministry: str | None = Query(None),
    date_from: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> AnomalyListResponse:
    conditions = []
    if type:
        conditions.append(Anomaly.type == type)
    if severity:
        conditions.append(Anomaly.severity == severity)
    if date_from:
        conditions.append(func.date(Anomaly.detected_at) >= date_from)
    if ministry:
        conditions.append(Tender.ministry.ilike(f"%{ministry}%"))

    base = (
        select(Anomaly, Tender.title, Tender.ministry, Tender.risk_score)
        .join(Tender, Anomaly.tender_id == Tender.id)
    )
    if conditions:
        base = base.where(and_(*conditions))

    count_q = select(func.count()).select_from(
        base.subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    q = (
        base
        .order_by(Tender.risk_score.desc(), Anomaly.detected_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = (await db.execute(q)).all()

    return AnomalyListResponse(
        anomalies=[
            AnomalyDetail(
                id=row[0].id,
                type=row[0].type,
                severity=row[0].severity,
                evidence=row[0].evidence,
                detected_at=row[0].detected_at,
                status=row[0].status,
                tender_id=row[0].tender_id,
                tender_title=row[1],
                ministry=row[2],
                risk_score=row[3] or 0,
            )
            for row in rows
        ],
        total=total,
        page=page,
        limit=limit,
    )
