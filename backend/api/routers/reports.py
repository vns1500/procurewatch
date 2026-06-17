"""AI-generated investigative report engine."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import AsyncSessionLocal, get_db
from ...models.anomaly import Anomaly
from ...models.report import Report
from ...models.tender import Tender
from ...models.vendor import Vendor
from ...models.price_benchmark import PriceBenchmark

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_PROMPT = """
You are an investigative journalist and certified fraud examiner
specializing in Indian government procurement corruption.

Analyze the following procurement data and write a structured
investigation brief. Be precise, factual, and data-driven.
Every claim must reference the evidence provided.

TENDER DATA:
{tender_data}

ANOMALIES DETECTED:
{anomaly_evidence}

VENDOR PROFILES:
{vendor_profiles}

PRICE BENCHMARKS:
{price_benchmarks}

DIRECTOR NETWORK:
{director_network}

STRICT OUTPUT RULES — violating any of these will break the parser:
1. Return ONLY valid JSON. No markdown fences, no preamble, no trailing text.
2. All string values must be plain natural language prose. Do NOT embed raw JSON, \
Python dicts, code snippets, or curly-brace structures inside any string value. \
If you need to reference a data point, describe it in words \
(e.g. "bid window of 2 days" not '{{"days_open": 2}}').
3. All monetary amounts must be written in human-readable form: \
"Rs.83.12 Cr" or "Rs.14.8L" — never raw paise integers.
4. The "evidence_analysis" field must be 3-4 natural language paragraphs. \
No JSON fragments, no bullet points, no code.

Write EXACTLY in this JSON structure:
{{
  "title": "Investigation Brief: [descriptive title based on the specific tenders]",
  "risk_level": "CRITICAL|HIGH|MEDIUM",
  "executive_summary": "2-3 sentence summary of what happened and why it is suspicious",
  "red_flags": [
    {{"flag": "flag name", "description": "specific evidence described in plain English with key figures", "severity": "critical|high|medium"}}
  ],
  "evidence_analysis": "3-4 paragraph narrative analysis. Write in prose only. Cite specific tender IDs, values in Cr/L, and anomaly patterns by name. No JSON inside this field.",
  "comparative_analysis": "How prices/patterns compare to similar tenders, market benchmarks, and GFR 2017 procurement norms",
  "rti_questions": [
    "Specific RTI question 1 referencing actual tender IDs and ministries",
    "Specific RTI question 2",
    "Specific RTI question 3",
    "Specific RTI question 4",
    "Specific RTI question 5"
  ],
  "recommended_actions": [
    "Specific action for journalist/NGO 1",
    "Specific action 2",
    "Specific action 3"
  ],
  "estimated_loss": "Estimated public money at risk in crores (e.g. Rs.4.2 Cr)"
}}
"""


# Pydantic schemas

class RedFlag(BaseModel):
    flag: str
    description: str
    severity: str


class ReportSections(BaseModel):
    executive_summary: str
    red_flags: list[RedFlag]
    evidence_analysis: str
    comparative_analysis: str
    rti_questions: list[str]
    recommended_actions: list[str]
    estimated_loss: str


class ReportSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    risk_level: str | None
    report_type: str
    tender_count: int
    created_at: Any
    status: str
    summary_preview: str | None


class ReportDetail(BaseModel):
    id: uuid.UUID
    title: str | None
    risk_level: str | None
    report_type: str
    sections: ReportSections | None
    raw_markdown: str | None
    created_at: Any
    status: str


class GenerateReportRequest(BaseModel):
    tender_ids: list[uuid.UUID]
    report_type: str = "quick"


class GenerateReportResponse(BaseModel):
    report_id: uuid.UUID
    status: str


# Prompt assembly

async def _assemble_prompt(
    tenders: list[Tender],
    anomalies: list[Anomaly],
    db: AsyncSession,
) -> str:
    tender_lines = []
    for t in tenders:
        tender_lines.append(
            f"- GEM ID: {t.gem_id}\n"
            f"  Title: {t.title}\n"
            f"  Ministry: {t.ministry} | State: {t.state}\n"
            f"  Value: Rs.{t.value / 100:,.2f} | Bids: {t.bid_count}\n"
            f"  Dates: {t.tender_date} to {t.close_date} "
            f"({(t.close_date - t.tender_date).days} days window)\n"
            f"  Risk Score: {t.risk_score}/100 | Flags: {', '.join(t.anomaly_flags or [])}"
        )

    anomaly_lines = []
    for a in anomalies:
        ev = json.dumps(a.evidence, default=str) if a.evidence else "{}"
        anomaly_lines.append(f"- [{a.severity.upper()}] {a.type}: {ev}")

    vendor_ids = [t.winner_vendor_id for t in tenders if t.winner_vendor_id]
    vendor_lines: list[str] = []
    vrows: list[Vendor] = []
    if vendor_ids:
        vrows = (await db.execute(
            select(Vendor).where(Vendor.id.in_(vendor_ids))
        )).scalars().all()
        for v in vrows:
            vendor_lines.append(
                f"- {v.name} (GSTIN: {v.gstin or 'N/A'}) | State: {v.state or 'N/A'}\n"
                f"  Wins: {v.total_wins} | Win Rate: {v.win_rate or 0:.1f}%"
                f" | Risk Level: {v.risk_level or 'unknown'}\n"
                f"  Total Contract Value: Rs.{(v.total_value or 0) / 100:,.2f}"
            )

    benchmarks_result = (await db.execute(
        select(PriceBenchmark).limit(10)
    )).scalars().all()
    benchmark_lines = [
        f"- {b.item_name}: avg Rs.{b.avg_price / 100:,.2f}/{b.unit} "
        f"(range Rs.{b.min_price / 100:,.2f} to Rs.{b.max_price / 100:,.2f})"
        for b in benchmarks_result
    ] or ["- No benchmark data available"]

    director_lines: list[str] = []
    for v in vrows:
        net = v.director_network_json or {}
        if net.get("nodes"):
            directors = [n["label"] for n in net["nodes"] if n.get("type") == "director"]
            director_lines.append(f"- {v.name}: directors - {', '.join(directors[:5])}")

    return REPORT_PROMPT.format(
        tender_data="\n".join(tender_lines) or "No tender data",
        anomaly_evidence="\n".join(anomaly_lines) or "No anomalies",
        vendor_profiles="\n".join(vendor_lines) or "No vendor data",
        price_benchmarks="\n".join(benchmark_lines),
        director_network="\n".join(director_lines) or "No director network data",
    )


def _flag_description(a: "Anomaly") -> str:
    ev = a.evidence or {}
    t = a.type
    if t == "single_bid":
        raw = ev.get("value_rupees")
        if raw and raw >= 1_00_00_000:
            v = f"Rs.{raw / 1_00_00_000:.2f} Cr"
        elif raw and raw >= 1_00_000:
            v = f"Rs.{raw / 1_00_000:.2f}L"
        elif raw:
            v = f"Rs.{raw:,.0f}"
        else:
            v = ""
        return f"Only one vendor bid on this tender.{f' Contract value: {v}.' if v else ''} Single-bid procurements bypass competitive pricing guarantees under GFR 2017 Rule 161."
    if t == "rushed_timeline":
        days = ev.get("days_open", ev.get("timeline_days", ev.get("days", "?")))
        return f"Bid window was {days} day(s) — below the GFR 2017 minimum of 7 days for competitive tenders. Short windows systematically exclude legitimate bidders."
    if t == "bid_splitting":
        dates = ev.get("split_dates") or ev.get("dates") or []
        n = len(dates) if isinstance(dates, list) else ev.get("count", "multiple")
        return f"{n} related awards to the same vendor in the same ministry within a 30-day window, each below the single-tender limit. Aggregate value exceeds threshold."
    if t == "inflated_pricing":
        score = ev.get("outlier_score", "")
        return f"Statistical outlier: contract price significantly exceeds benchmark pricing for comparable items. Isolation Forest anomaly score: {score:.3f}." if score else "Price identified as statistical outlier against market benchmarks for comparable procurement."
    if t == "shell_vendor":
        age = ev.get("company_age_days", "?")
        return f"Vendor incorporated {age} days before winning this contract. Shell company risk: newly registered entities winning high-value contracts indicate possible conduit arrangements."
    if t == "director_overlap":
        vendors = ev.get("overlapping_vendors", [])
        return f"Shared directors identified across {len(vendors)} competing vendors. Director network overlap undermines bid independence and may indicate cartel behaviour."
    return "Anomaly detected. Review evidence section for details."


def _synthetic_sections(tenders: list[Tender], anomalies: list[Anomaly]) -> dict[str, Any]:
    ministry = tenders[0].ministry if tenders else "Unknown Ministry"
    total_value = sum(t.value for t in tenders)
    flag_types = list({a.type for a in anomalies})
    gem_ids = ", ".join(t.gem_id for t in tenders[:3])
    max_risk = max((t.risk_score or 0) for t in tenders) if tenders else 0
    risk_level = "CRITICAL" if max_risk >= 80 else "HIGH" if max_risk >= 50 else "MEDIUM"

    return {
        "title": f"Investigation Brief: {ministry} — {', '.join(flag_types[:2]) or 'Procurement Irregularities'}",
        "risk_level": risk_level,
        "executive_summary": (
            f"Analysis of {len(tenders)} tender(s) from {ministry} with combined value "
            f"Rs.{total_value / 100:,.2f} reveals {len(anomalies)} anomaly instance(s) across "
            f"{len(flag_types)} distinct pattern type(s): {', '.join(flag_types)}. "
            f"The aggregate risk score of {max_risk}/100 warrants immediate investigative attention "
            f"by the Comptroller and Auditor General (CAG) or relevant vigilance committee."
        ),
        "red_flags": [
            {
                "flag": a.type.replace("_", " ").title(),
                "description": _flag_description(a),
                "severity": a.severity,
            }
            for a in anomalies[:6]
        ],
        "evidence_analysis": (
            f"Procurement pattern analysis for {ministry} tenders ({gem_ids}) reveals "
            f"systematic deviations from GFR 2017 norms. The combination of anomaly types "
            f"({', '.join(flag_types)}) is consistent with known rent-seeking behavior. "
            + " ".join(
                f"[{a.severity.upper()}] {a.type.replace('_', ' ').title()}: "
                f"{json.dumps(a.evidence, default=str)[:150]}."
                for a in anomalies[:4]
            )
        ),
        "comparative_analysis": (
            "GFR 2017 mandates minimum 7-day bid windows for sub-Rs.25L tenders "
            "and minimum 3 bidders for competitive procurement above Rs.1L. "
            f"{sum(1 for t in tenders if (t.close_date - t.tender_date).days < 7)} tender(s) "
            f"used compressed bid windows; "
            f"{sum(1 for t in tenders if t.bid_count == 1)} had single bids."
        ),
        "rti_questions": [
            f"Provide all bid documents, NIT, and corrigenda for tenders {gem_ids}.",
            "List all vendors invited to bid and those who submitted bids with timestamps.",
            "Provide TEC and Financial Bid opening minutes.",
            "Provide justification for compressed bid windows below 7 days.",
            f"Disclose the approved demand note triggering each procurement in {ministry}.",
        ],
        "recommended_actions": [
            f"File RTI with {ministry} procurement cell — 30-day statutory response window.",
            "Cross-reference winning vendor GSTIN against MCA21 director database.",
            "Request CAG audit inclusion in next annual compliance review cycle.",
        ],
        "estimated_loss": f"Rs.{total_value / 100 / 1_00_00_000:.2f} Cr (gross contract value at risk)",
    }


# Background generation

async def _generate_report_background(
    report_id: uuid.UUID,
    tender_ids: list[uuid.UUID],
    report_type: str,
) -> None:
    log = logger.bind(report_id=str(report_id))
    try:
        async with AsyncSessionLocal() as db:
            tenders = (await db.execute(
                select(Tender).where(Tender.id.in_(tender_ids))
            )).scalars().all()
            anomalies = (await db.execute(
                select(Anomaly).where(Anomaly.tender_id.in_(tender_ids))
            )).scalars().all()

            sections_dict: dict[str, Any]
            raw_text = ""

            if settings.ANTHROPIC_API_KEY:
                try:
                    import anthropic
                    import redis.asyncio as aioredis
                    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                    prompt = await _assemble_prompt(list(tenders), list(anomalies), db)
                    redis_client = aioredis.from_url(settings.REDIS_URL)
                    stream_key = f"report_stream:{report_id}"
                    max_tokens = 8192 if report_type == "full" else 4096

                    async with client.messages.stream(
                        model="claude-sonnet-4-6",
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}],
                    ) as stream:
                        async for chunk in stream.text_stream:
                            raw_text += chunk
                            await redis_client.setex(stream_key, 600, raw_text)

                    await redis_client.delete(stream_key)
                    await redis_client.aclose()

                    sections_dict = json.loads(raw_text.strip())
                    log.info("claude_generation_success", chars=len(raw_text))
                except json.JSONDecodeError as e:
                    log.warning("claude_json_parse_failed", error=str(e))
                    sections_dict = _synthetic_sections(list(tenders), list(anomalies))
                    raw_text = json.dumps(sections_dict)
                except Exception as e:
                    log.error("claude_generation_failed", error=str(e))
                    sections_dict = _synthetic_sections(list(tenders), list(anomalies))
                    raw_text = json.dumps(sections_dict)
            else:
                log.info("no_api_key_using_synthetic")
                sections_dict = _synthetic_sections(list(tenders), list(anomalies))
                raw_text = json.dumps(sections_dict)

            title = sections_dict.pop("title", "Investigation Brief")
            risk_level = sections_dict.pop("risk_level", "HIGH")

            report_q = await db.execute(select(Report).where(Report.id == report_id))
            report = report_q.scalar_one()
            report.title = title
            report.risk_level = risk_level
            report.sections = sections_dict
            report.raw_markdown = raw_text
            report.summary_preview = sections_dict.get("executive_summary", "")[:300]
            report.status = "ready"
            await db.commit()
            log.info("report_ready", title=title)

    except Exception as exc:
        log.error("report_generation_failed", error=str(exc))
        async with AsyncSessionLocal() as db:
            r = (await db.execute(
                select(Report).where(Report.id == report_id)
            )).scalar_one_or_none()
            if r:
                r.status = "failed"
                await db.commit()


# Routes

@router.get("", response_model=list[ReportSummary])
async def list_reports(db: AsyncSession = Depends(get_db)) -> list[ReportSummary]:
    rows = (await db.execute(
        select(Report)
        .where(Report.deleted_at.is_(None))
        .order_by(Report.created_at.desc())
        .limit(50)
    )).scalars().all()
    return [
        ReportSummary(
            id=r.id,
            title=r.title,
            risk_level=r.risk_level,
            report_type=r.report_type or "quick",
            tender_count=len(r.tender_ids or []),
            created_at=r.created_at,
            status=r.status,
            summary_preview=r.summary_preview,
        )
        for r in rows
    ]


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    req: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> GenerateReportResponse:
    if not req.tender_ids:
        raise HTTPException(status_code=422, detail="At least one tender_id required")

    report = Report(
        tender_ids=req.tender_ids,
        report_type=req.report_type,
        status="generating",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    background_tasks.add_task(
        _generate_report_background,
        report.id,
        req.tender_ids,
        req.report_type,
    )

    logger.info("report_queued", report_id=str(report.id), tender_count=len(req.tender_ids))
    return GenerateReportResponse(report_id=report.id, status="generating")


@router.get("/{report_id}/stream")
async def stream_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """SSE endpoint streaming Claude text chunks as they arrive."""
    from sse_starlette.sse import EventSourceResponse
    import redis.asyncio as aioredis

    async def generator():
        redis_client = aioredis.from_url(settings.REDIS_URL)
        stream_key = f"report_stream:{report_id}"
        sent_len = 0
        try:
            while True:
                result = await db.execute(select(Report).where(Report.id == report_id))
                report = result.scalar_one_or_none()
                if report is None:
                    yield {"event": "error", "data": "not_found"}
                    break

                partial = await redis_client.get(stream_key)
                if partial:
                    text = partial.decode("utf-8")
                    if len(text) > sent_len:
                        yield {"event": "chunk", "data": text[sent_len:]}
                        sent_len = len(text)

                if report.status == "ready":
                    yield {"event": "done", "data": json.dumps({
                        "status": "ready",
                        "report_id": str(report_id),
                    })}
                    break
                elif report.status == "failed":
                    yield {"event": "error", "data": "failed"}
                    break

                await asyncio.sleep(0.3)
        finally:
            await redis_client.aclose()

    return EventSourceResponse(generator())


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReportDetail:
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.deleted_at.is_(None))
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    sections = None
    if report.sections and report.status == "ready":
        try:
            sections = ReportSections(**report.sections)
        except Exception:
            pass

    return ReportDetail(
        id=report.id,
        title=report.title,
        risk_level=report.risk_level,
        report_type=report.report_type or "quick",
        sections=sections,
        raw_markdown=report.raw_markdown,
        created_at=report.created_at,
        status=report.status,
    )


@router.delete("/{report_id}", status_code=204, response_model=None)
async def delete_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    from sqlalchemy import update
    from datetime import datetime, timezone
    result = await db.execute(
        update(Report)
        .where(Report.id == report_id, Report.deleted_at.is_(None))
        .values(deleted_at=datetime.now(timezone.utc))
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.commit()
