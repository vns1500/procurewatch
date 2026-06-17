from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.alert import Alert

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertSummary(BaseModel):
    id: uuid.UUID
    ministries: list[str]
    keywords: list[str]
    email: str
    status: str
    last_triggered: Any
    trigger_count: int
    created_at: Any


class SubscribeRequest(BaseModel):
    ministries: list[str] = []
    keywords: list[str] = []
    email: str


class SubscribeResponse(BaseModel):
    alert_id: uuid.UUID


class PatchAlertRequest(BaseModel):
    status: str


@router.get("", response_model=list[AlertSummary])
async def list_alerts(db: AsyncSession = Depends(get_db)) -> list[AlertSummary]:
    rows = (await db.execute(
        select(Alert).order_by(Alert.created_at.desc())
    )).scalars().all()

    return [
        AlertSummary(
            id=a.id,
            ministries=a.ministries or [],
            keywords=a.keywords or [],
            email=a.email,
            status=a.status,
            last_triggered=a.last_triggered,
            trigger_count=a.trigger_count or 0,
            created_at=a.created_at,
        )
        for a in rows
    ]


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe_alert(
    req: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscribeResponse:
    if not req.email:
        raise HTTPException(status_code=422, detail="Email required")

    alert = Alert(
        ministries=req.ministries,
        keywords=req.keywords,
        email=req.email,
        status="active",
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.info("alert_subscribed", alert_id=str(alert.id), email=req.email)
    return SubscribeResponse(alert_id=alert.id)


@router.patch("/{alert_id}", response_model=AlertSummary)
async def patch_alert(
    alert_id: uuid.UUID,
    req: PatchAlertRequest,
    db: AsyncSession = Depends(get_db),
) -> AlertSummary:
    if req.status not in ("active", "paused"):
        raise HTTPException(status_code=422, detail="status must be 'active' or 'paused'")

    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = req.status
    await db.commit()
    await db.refresh(alert)

    return AlertSummary(
        id=alert.id,
        ministries=alert.ministries or [],
        keywords=alert.keywords or [],
        email=alert.email,
        status=alert.status,
        last_triggered=alert.last_triggered,
        trigger_count=alert.trigger_count or 0,
        created_at=alert.created_at,
    )


@router.delete("/{alert_id}", status_code=204, response_model=None)
async def delete_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
