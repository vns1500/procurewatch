from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.vendor import Vendor
from models.tender import Tender

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/vendors", tags=["vendors"])


class VendorSummary(BaseModel):
    id: uuid.UUID
    name: str
    gstin: str | None
    state: str | None
    total_wins: int
    total_value: int
    win_rate: float
    risk_level: str

    class Config:
        from_attributes = True


class ContractSummary(BaseModel):
    tender_id: uuid.UUID
    title: str
    value: int
    date: Any
    risk_score: int
    anomaly_flags: list[str]


class VendorProfile(BaseModel):
    id: uuid.UUID
    name: str
    gstin: str | None
    state: str | None
    incorporation_date: Any
    total_wins: int
    total_value: int
    win_rate: float
    risk_level: str
    mca_verified: bool
    recent_contracts: list[ContractSummary]

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    vendors: list[VendorSummary]
    total: int
    page: int
    limit: int


@router.get("", response_model=VendorListResponse)
async def list_vendors(
    state: str | None = Query(None),
    risk_level: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> VendorListResponse:
    conditions = []
    if state:
        conditions.append(Vendor.state.ilike(f"%{state}%"))
    if risk_level:
        conditions.append(Vendor.risk_level == risk_level)

    from sqlalchemy import and_
    count_q = select(func.count()).select_from(Vendor)
    if conditions:
        count_q = count_q.where(and_(*conditions))
    total = (await db.execute(count_q)).scalar_one()

    q = (
        select(Vendor)
        .order_by(Vendor.total_wins.desc(), Vendor.total_value.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    if conditions:
        q = q.where(and_(*conditions))

    rows = (await db.execute(q)).scalars().all()

    return VendorListResponse(
        vendors=[VendorSummary(
            id=v.id,
            name=v.name,
            gstin=v.gstin,
            state=v.state,
            total_wins=v.total_wins,
            total_value=v.total_value,
            win_rate=v.win_rate or 0.0,
            risk_level=v.risk_level or "low",
        ) for v in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{vendor_id}", response_model=VendorProfile)
async def get_vendor(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VendorProfile:
    v_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = v_result.scalar_one_or_none()
    if vendor is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Vendor not found")

    contracts_q = (
        select(Tender)
        .where(Tender.winner_vendor_id == vendor_id)
        .order_by(Tender.tender_date.desc())
        .limit(10)
    )
    contracts = (await db.execute(contracts_q)).scalars().all()

    return VendorProfile(
        id=vendor.id,
        name=vendor.name,
        gstin=vendor.gstin,
        state=vendor.state,
        incorporation_date=vendor.incorporation_date,
        total_wins=vendor.total_wins,
        total_value=vendor.total_value,
        win_rate=vendor.win_rate or 0.0,
        risk_level=vendor.risk_level or "low",
        mca_verified=vendor.mca_verified or False,
        recent_contracts=[
            ContractSummary(
                tender_id=t.id,
                title=t.title,
                value=t.value,
                date=t.tender_date,
                risk_score=t.risk_score or 0,
                anomaly_flags=t.anomaly_flags or [],
            )
            for t in contracts
        ],
    )


@router.get("/{vendor_id}/network")
async def get_vendor_network(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    v_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = v_result.scalar_one_or_none()
    if vendor is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Return cached director_network_json if already enriched (has nodes key)
    if vendor.director_network_json and vendor.director_network_json.get("nodes"):
        return vendor.director_network_json

    try:
        from pipeline.mca_enrichment import MCA21Enricher
        enricher = MCA21Enricher()
        enrichment = await enricher.enrich_vendor(vendor, db)
        await db.commit()
        return enrichment.director_network_json
    except Exception:
        logger.exception("vendor_network_error", vendor_id=str(vendor_id))
        return {"vendor_id": str(vendor_id), "nodes": [], "edges": []}


@router.get("/{vendor_id}/contracts")
async def get_vendor_contracts(
    vendor_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    v_result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = v_result.scalar_one_or_none()
    if vendor is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Vendor not found")

    count_q = select(func.count()).where(Tender.winner_vendor_id == vendor_id)
    total = (await db.execute(count_q)).scalar_one()

    contracts_q = (
        select(Tender)
        .where(Tender.winner_vendor_id == vendor_id)
        .order_by(Tender.tender_date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    contracts = (await db.execute(contracts_q)).scalars().all()

    return {
        "vendor_id": str(vendor_id),
        "vendor_name": vendor.name,
        "total": total,
        "page": page,
        "limit": limit,
        "contracts": [
            {
                "tender_id": str(t.id),
                "title": t.title,
                "ministry": t.ministry,
                "state": t.state,
                "value": t.value,
                "tender_date": t.tender_date.isoformat() if t.tender_date else None,
                "risk_score": t.risk_score or 0,
                "anomaly_flags": t.anomaly_flags or [],
            }
            for t in contracts
        ],
    }
