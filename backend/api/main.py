import structlog
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.database import engine, Base
from core.config import settings
from models import *  # noqa: F401, F403
from api.routers import tenders, dashboard, vendors, anomalies, reports, alerts, detection, billing, auth, export

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger(__name__)

# Sentry (no-op when DSN is empty)
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), AsyncioIntegration()],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )
    logger.info("sentry_enabled", environment=settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", msg="ProcureWatch API starting", environment=settings.ENVIRONMENT)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("db_ready", msg="Tables created or verified")
    yield
    await engine.dispose()
    logger.info("shutdown", msg="ProcureWatch API stopped")


app = FastAPI(
    title="ProcureWatch API",
    description="Government procurement anomaly detection system",
    version="1.0.0",
    lifespan=lifespan,
    # Hide docs in production
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    log = logger.bind(method=request.method, path=request.url.path)
    log.info("request_start")
    response = await call_next(request)
    log.info("request_end", status=response.status_code)
    return response


app.include_router(tenders.router)
app.include_router(dashboard.router)
app.include_router(vendors.router)
app.include_router(anomalies.router)
app.include_router(reports.router)
app.include_router(alerts.router)
app.include_router(detection.router)
app.include_router(billing.router)
app.include_router(auth.router)
app.include_router(export.router)


@app.get("/health")
async def health() -> dict[str, Any]:
    from sqlalchemy import text
    from ..core.database import AsyncSessionLocal
    import redis.asyncio as aioredis
    from ..models.tender import Tender
    from ..models.anomaly import Anomaly
    from sqlalchemy import select, func

    db_status = "connected"
    redis_status = "connected"
    total_tenders = 0
    total_anomalies = 0

    try:
        async with AsyncSessionLocal() as db:
            total_tenders = (await db.execute(select(func.count(Tender.id)))).scalar_one()
            total_anomalies = (await db.execute(select(func.count(Anomaly.id)))).scalar_one()
    except Exception as e:
        db_status = f"error: {e}"

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception as e:
        redis_status = f"error: {e}"

    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "db": db_status,
        "redis": redis_status,
        "total_tenders": total_tenders,
        "total_anomalies": total_anomalies,
    }
