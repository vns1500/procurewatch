"""API key authentication and user management."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str


class RegisterResponse(BaseModel):
    api_key: str
    email: str
    plan: str


class MeResponse(BaseModel):
    email: str
    plan: str
    reports_used_this_month: int
    api_key: str
    is_admin: bool


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=422, detail="Valid email required")

    existing = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if existing:
        return RegisterResponse(api_key=existing.api_key, email=existing.email, plan=existing.plan)

    user = User(email=req.email)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", email=req.email, api_key=user.api_key[:12] + "…")
    return RegisterResponse(api_key=user.api_key, email=user.email, plan=user.plan)


@router.get("/me", response_model=MeResponse)
async def get_me(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    if x_api_key == settings.ADMIN_API_KEY:
        return MeResponse(
            email="admin@procurewatch.in",
            plan="enterprise",
            reports_used_this_month=0,
            api_key=x_api_key,
            is_admin=True,
        )

    result = await db.execute(select(User).where(User.api_key == x_api_key))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return MeResponse(
        email=user.email,
        plan=user.plan,
        reports_used_this_month=user.reports_used_this_month,
        api_key=user.api_key,
        is_admin=False,
    )


async def get_current_user(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Dependency: returns User if API key is valid, None for anonymous/admin."""
    if not x_api_key:
        return None
    if x_api_key == settings.ADMIN_API_KEY:
        return None  # Admin bypasses all limits

    result = await db.execute(select(User).where(User.api_key == x_api_key))
    return result.scalar_one_or_none()


async def require_report_quota(
    user: User | None = Depends(get_current_user),
) -> None:
    """Raises 402 if free user has exhausted monthly report quota."""
    if user is None:
        return  # Admin or anonymous — no limit
    if user.plan in ("pro", "enterprise"):
        return
    from api.routers.billing import PLANS
    limit = PLANS["free"]["reports_per_month"]
    if user.reports_used_this_month >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "report_quota_exceeded",
                "message": f"Free plan allows {limit} reports/month. Upgrade to Pro for unlimited reports.",
                "upgrade_url": "/pricing",
            },
        )
