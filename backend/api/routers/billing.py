"""Stripe billing integration."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

PLANS: dict[str, dict] = {
    "free": {
        "price_id": None,
        "reports_per_month": 10,
        "api_calls_per_day": 100,
        "features": ["basic_detection", "csv_export"],
        "label": "Free",
        "price_inr": 0,
    },
    "pro": {
        "price_id": settings.STRIPE_PRO_PRICE_ID,
        "reports_per_month": -1,
        "api_calls_per_day": 10000,
        "features": ["all_detection", "pdf_export", "api_access", "email_alerts"],
        "label": "Pro",
        "price_inr": 2999,
    },
    "enterprise": {
        "price_id": None,
        "reports_per_month": -1,
        "api_calls_per_day": -1,
        "features": ["all", "custom_scrapers", "dedicated_support", "white_label"],
        "label": "Enterprise",
        "price_inr": None,
    },
}


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str
    email: str | None = None


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    if req.plan not in ("pro", "enterprise"):
        raise HTTPException(status_code=422, detail="Plan must be 'pro' or 'enterprise'")
    if req.plan == "enterprise":
        raise HTTPException(status_code=422, detail="Enterprise plan requires contacting sales")
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer_id: str | None = None
    if req.email:
        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()
        if user and user.stripe_customer_id:
            customer_id = user.stripe_customer_id

    session_params: dict = {
        "mode": "subscription",
        "line_items": [{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        "success_url": req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": req.cancel_url,
        "metadata": {"plan": req.plan},
    }
    if customer_id:
        session_params["customer"] = customer_id
    elif req.email:
        session_params["customer_email"] = req.email

    session = stripe.checkout.Session.create(**session_params)
    logger.info("checkout_session_created", plan=req.plan)
    return CheckoutResponse(checkout_url=session.url)


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="stripe-signature")) -> dict:
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    async with __import__("core.database", fromlist=["AsyncSessionLocal"]).AsyncSessionLocal() as db:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
            customer_id = session.get("customer")
            plan = session.get("metadata", {}).get("plan", "pro")

            if customer_email:
                result = await db.execute(select(User).where(User.email == customer_email))
                user = result.scalar_one_or_none()
                if user:
                    user.plan = plan
                    if customer_id:
                        user.stripe_customer_id = customer_id
                    await db.commit()
                    logger.info("user_upgraded", email=customer_email, plan=plan)

        elif event["type"] == "customer.subscription.deleted":
            customer_id = event["data"]["object"].get("customer")
            if customer_id:
                result = await db.execute(
                    select(User).where(User.stripe_customer_id == customer_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.plan = "free"
                    await db.commit()
                    logger.info("user_downgraded", customer_id=customer_id)

    return {"received": True}


@router.get("/portal")
async def customer_portal(
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    result = await db.execute(select(User).where(User.api_key == x_api_key))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not user.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No Stripe customer found for this account")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.billing_portal.Session.create(customer=user.stripe_customer_id)
    return {"portal_url": session.url}


@router.get("/plans")
async def list_plans() -> dict:
    return {"plans": PLANS}
