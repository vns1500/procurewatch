from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func, and_, or_, cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...models.tender import Tender
from ...models.vendor import Vendor
from ...models.anomaly import Anomaly
from ...scrapers.gem import GEMScraper, generate_synthetic_orders

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/tenders", tags=["tenders"])


class AnomalySummary(BaseModel):
    id: uuid.UUID
    type: str
    severity: str
    status: str

    class Config:
        from_attributes = True


class TenderResponse(BaseModel):
    id: uuid.UUID
    gem_id: str
    title: str
    ministry: str
    state: str
    value: int
    tender_date: date
    close_date: date
    bid_count: int
    risk_score: int
    anomaly_flags: list[str]
    vendor_name: str | None = None
    created_at: Any

    class Config:
        from_attributes = True


class TenderListResponse(BaseModel):
    tenders: list[TenderResponse]
    total: int
    page: int
    limit: int


class RawTenderIngest(BaseModel):
    gem_id: str
    title: str
    ministry: str
    state: str
    value: int
    tender_date: date
    close_date: date
    bid_count: int = 1
    vendor_name: str | None = None
    vendor_gstin: str | None = None
    vendor_state: str | None = None
    vendor_incorporation_date: date | None = None
    raw_json: dict[str, Any] | None = None


@router.get("", response_model=TenderListResponse)
async def list_tenders(
    ministry: str | None = Query(None),
    state: str | None = Query(None),
    risk_min: int | None = Query(None, ge=0, le=100),
    risk_max: int | None = Query(None, ge=0, le=100),
    anomaly_type: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TenderListResponse:
    log = logger.bind(ministry=ministry, state=state, risk_min=risk_min, page=page)

    conditions = []
    if ministry:
        conditions.append(Tender.ministry.ilike(f"%{ministry}%"))
    if state:
        conditions.append(Tender.state.ilike(f"%{state}%"))
    if risk_min is not None:
        conditions.append(Tender.risk_score >= risk_min)
    if risk_max is not None:
        conditions.append(Tender.risk_score <= risk_max)
    if date_from:
        conditions.append(Tender.tender_date >= date_from)
    if date_to:
        conditions.append(Tender.tender_date <= date_to)
    if anomaly_type:
        conditions.append(Tender.anomaly_flags.any(anomaly_type))

    count_q = select(func.count()).select_from(Tender)
    if conditions:
        count_q = count_q.where(and_(*conditions))
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = (
        select(Tender, Vendor.name.label("vendor_name"))
        .outerjoin(Vendor, Tender.winner_vendor_id == Vendor.id)
        .order_by(Tender.risk_score.desc(), Tender.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    if conditions:
        q = q.where(and_(*conditions))

    rows = await db.execute(q)
    result_rows = rows.all()

    tender_list: list[TenderResponse] = []
    for row in result_rows:
        t = row[0]
        vendor_name = row[1]
        tender_list.append(TenderResponse(
            id=t.id,
            gem_id=t.gem_id,
            title=t.title,
            ministry=t.ministry,
            state=t.state,
            value=t.value,
            tender_date=t.tender_date,
            close_date=t.close_date,
            bid_count=t.bid_count,
            risk_score=t.risk_score,
            anomaly_flags=t.anomaly_flags or [],
            vendor_name=vendor_name,
            created_at=t.created_at,
        ))

    log.info("tenders_listed", total=total, returned=len(tender_list))
    return TenderListResponse(tenders=tender_list, total=total, page=page, limit=limit)


@router.post("/ingest")
async def ingest_tenders(
    raw_tenders: list[RawTenderIngest],
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    from ...detection.rules import run_all_rules, detect_bid_splitting

    log = logger.bind(incoming=len(raw_tenders))
    saved = 0
    skipped = 0
    new_tenders: list[Tender] = []

    for raw in raw_tenders:
        existing = await db.execute(select(Tender).where(Tender.gem_id == raw.gem_id))
        if existing.scalar_one_or_none() is not None:
            skipped += 1
            continue

        # Upsert vendor
        vendor: Vendor | None = None
        if raw.vendor_gstin:
            v_result = await db.execute(select(Vendor).where(Vendor.gstin == raw.vendor_gstin))
            vendor = v_result.scalar_one_or_none()
        if vendor is None and raw.vendor_name:
            vendor = Vendor(
                name=raw.vendor_name,
                gstin=raw.vendor_gstin,
                state=raw.vendor_state,
                incorporation_date=raw.vendor_incorporation_date,
            )
            db.add(vendor)
            await db.flush()

        tender = Tender(
            gem_id=raw.gem_id,
            title=raw.title,
            ministry=raw.ministry,
            state=raw.state,
            value=raw.value,
            tender_date=raw.tender_date,
            close_date=raw.close_date,
            bid_count=raw.bid_count,
            winner_vendor_id=vendor.id if vendor else None,
            raw_json=raw.raw_json,
            anomaly_flags=[],
            risk_score=0,
        )
        db.add(tender)
        await db.flush()

        risk_score, anomalies = run_all_rules(tender, [])
        flags: list[str] = []
        for a in anomalies:
            anomaly_obj = Anomaly(
                tender_id=tender.id,
                type=a["type"],
                severity=a["severity"],
                evidence=a["evidence"],
                status="open",
            )
            db.add(anomaly_obj)
            flags.append(a["type"])

        tender.risk_score = risk_score
        tender.anomaly_flags = flags
        new_tenders.append(tender)
        saved += 1

    # Bid splitting across all new tenders with vendors
    split_anomalies = detect_bid_splitting(new_tenders)
    for a in split_anomalies:
        aobj = Anomaly(
            tender_id=a["tender_id"],
            type=a["type"],
            severity=a["severity"],
            evidence=a["evidence"],
            status="open",
        )
        db.add(aobj)
        # Update tender flags
        for t in new_tenders:
            if t.id == a["tender_id"] and "bid_splitting" not in (t.anomaly_flags or []):
                t.anomaly_flags = list(t.anomaly_flags or []) + ["bid_splitting"]
                t.risk_score = min((t.risk_score or 0) + 40, 100)

    # Update vendor stats for all vendors that won new tenders
    from collections import defaultdict
    vendor_tenders: dict = defaultdict(list)
    for t in new_tenders:
        if t.winner_vendor_id:
            vendor_tenders[t.winner_vendor_id].append(t)

    for vendor_id, won in vendor_tenders.items():
        v_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
        v = v_result.scalar_one_or_none()
        if v:
            v.total_wins = (v.total_wins or 0) + len(won)
            v.total_value = (v.total_value or 0) + sum(t.value for t in won)
            max_risk = max((t.risk_score or 0) for t in won)
            if max_risk >= 65:
                v.risk_level = "critical"
            elif max_risk >= 35:
                v.risk_level = "high" if v.risk_level not in ("critical",) else v.risk_level
            elif max_risk > 0 and v.risk_level == "low":
                v.risk_level = "medium"

            # win_rate = total_wins / total tenders in vendor's won ministries * 100
            ministry_rows = await db.execute(
                select(Tender.ministry).where(Tender.winner_vendor_id == vendor_id).distinct()
            )
            ministries = [row[0] for row in ministry_rows.all()]
            if ministries:
                total_in_ministries = (await db.execute(
                    select(func.count(Tender.id)).where(Tender.ministry.in_(ministries))
                )).scalar_one()
                v.win_rate = round(v.total_wins / total_in_ministries * 100, 2) if total_in_ministries > 0 else 0.0
            else:
                v.win_rate = 0.0

    await db.commit()

    log.info("ingest_complete", saved=saved, skipped=skipped, split_anomalies=len(split_anomalies))
    return {"saved": saved, "skipped": skipped, "split_anomalies": len(split_anomalies)}


@router.post("/seed")
async def seed_database(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Seed DB with synthetic data. Call once on first boot."""
    existing = await db.execute(select(func.count()).select_from(Tender))
    count = existing.scalar_one()
    if count >= 100:
        return {"status": "already_seeded", "count": count}

    scraper = GEMScraper()
    raw_orders = generate_synthetic_orders(605)
    normalized = [scraper.normalize(o) for o in raw_orders]

    ingest_payload = [RawTenderIngest(**n) for n in normalized]
    result = await ingest_tenders(ingest_payload, db)
    return {"status": "seeded", **result}
