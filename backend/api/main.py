import structlog
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.database import engine, Base
from ..models import *  # noqa: F401, F403
from .routers import tenders, dashboard, vendors, anomalies, reports, alerts, detection, billing, auth, export

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", msg="ProcureWatch API starting")
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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "procurewatch-api"}
