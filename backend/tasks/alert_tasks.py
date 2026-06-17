"""Alert matching and email dispatch via Resend."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..models.alert import Alert
    from ..models.anomaly import Anomaly

logger = structlog.get_logger(__name__)


ALERT_EMAIL_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ margin:0; padding:0; background:#0a0a0a; font-family: 'JetBrains Mono', monospace; color:#e4e4e4; }}
  .container {{ max-width:600px; margin:0 auto; background:#111; border:1px solid #222; }}
  .header {{ background:#c0392b; padding:20px 28px; }}
  .header-title {{ font-size:11px; letter-spacing:0.12em; text-transform:uppercase; color:#fff; opacity:0.8; }}
  .header-h {{ font-size:20px; font-weight:700; color:#fff; margin:6px 0 0; }}
  .body {{ padding:24px 28px; }}
  .summary {{ font-size:12px; color:#888; margin-bottom:20px; }}
  .anomaly-card {{ border:1px solid #222; border-left:3px solid #c0392b; border-radius:2px;
                   padding:12px 16px; margin-bottom:12px; background:#161616; }}
  .anomaly-type {{ font-size:10px; letter-spacing:0.1em; text-transform:uppercase; color:#c0392b; font-weight:700; }}
  .anomaly-title {{ font-size:13px; color:#e4e4e4; margin:4px 0; }}
  .anomaly-meta {{ font-size:11px; color:#666; }}
  .risk-score {{ font-size:18px; font-weight:700; color:#e74c3c; font-family:monospace; }}
  .cta {{ display:block; background:#c0392b; color:#fff; text-decoration:none; text-align:center;
          padding:12px 20px; border-radius:2px; font-size:12px; font-weight:700;
          letter-spacing:0.06em; margin:24px 0 0; }}
  .footer {{ padding:16px 28px; border-top:1px solid #1a1a1a; }}
  .footer-text {{ font-size:10px; color:#444; }}
  a.manage {{ color:#555; font-size:10px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-title">PROCUREWATCH ALERT</div>
    <div class="header-h">{count} new anomaly{plural} detected</div>
  </div>
  <div class="body">
    <div class="summary">
      Your alert matched {count} new procurement anomaly{plural} that require attention.
    </div>
    {anomaly_cards}
    <a href="https://procurewatch.in/anomalies" class="cta">VIEW ALL ANOMALIES &rarr;</a>
  </div>
  <div class="footer">
    <div class="footer-text">
      ProcureWatch monitors Indian government procurement for fraud patterns.<br>
      <a href="https://procurewatch.in/alerts" class="manage">Manage alert preferences</a>
    </div>
  </div>
</div>
</body>
</html>"""

ANOMALY_CARD_TEMPLATE = """\
<div class="anomaly-card">
  <div class="anomaly-type">{anomaly_type}</div>
  <div class="anomaly-title">{title}</div>
  <div class="anomaly-meta">{ministry} &middot; Risk Score: <span class="risk-score">{risk_score}</span></div>
</div>"""


class AlertMatcher:
    async def check_new_anomalies(
        self,
        anomalies: list["Anomaly"],
        tender_lookup: dict[str, dict],
    ) -> None:
        """Match new anomalies against active alerts and dispatch emails."""
        from ..core.database import AsyncSessionLocal
        from ..models.alert import Alert
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            active_alerts = (await db.execute(
                select(Alert).where(Alert.status == "active")
            )).scalars().all()

            for alert in active_alerts:
                # Throttle: max 1 email per alert per hour
                if alert.last_triggered:
                    since = datetime.now(timezone.utc) - alert.last_triggered
                    if since < timedelta(hours=1):
                        continue

                matched = self._match_anomalies(alert, anomalies, tender_lookup)
                if not matched:
                    continue

                try:
                    await self.send_alert_email(alert, matched, tender_lookup)
                    alert.last_triggered = datetime.now(timezone.utc)
                    alert.trigger_count = (alert.trigger_count or 0) + 1
                    await db.commit()
                    logger.info("alert_email_sent", alert_id=str(alert.id), email=alert.email, count=len(matched))
                except Exception as exc:
                    logger.error("alert_email_failed", alert_id=str(alert.id), error=str(exc))

    def _match_anomalies(
        self,
        alert: "Alert",
        anomalies: list["Anomaly"],
        tender_lookup: dict[str, dict],
    ) -> list["Anomaly"]:
        matched = []
        ministries = {m.lower() for m in (alert.ministries or [])}
        keywords = [k.lower() for k in (alert.keywords or [])]

        for anomaly in anomalies:
            tender = tender_lookup.get(str(anomaly.tender_id), {})
            ministry = (tender.get("ministry") or "").lower()
            title = (tender.get("title") or "").lower()

            ministry_match = any(m in ministry for m in ministries) if ministries else False
            keyword_match = any(kw in title for kw in keywords) if keywords else False

            if ministry_match or keyword_match:
                matched.append(anomaly)

        return matched

    async def send_alert_email(
        self,
        alert: "Alert",
        anomalies: list["Anomaly"],
        tender_lookup: dict[str, dict],
    ) -> None:
        from ..core.config import settings

        if not settings.RESEND_API_KEY:
            logger.warning("resend_not_configured_skipping_email")
            return

        count = len(anomalies)
        plural = "ies" if count != 1 else "y"

        cards = []
        for a in anomalies[:5]:
            tender = tender_lookup.get(str(a.tender_id), {})
            cards.append(ANOMALY_CARD_TEMPLATE.format(
                anomaly_type=a.type.replace("_", " ").upper(),
                title=tender.get("title", "Unknown Tender")[:80],
                ministry=tender.get("ministry", "Unknown Ministry"),
                risk_score=tender.get("risk_score", 0),
            ))

        html = ALERT_EMAIL_TEMPLATE.format(
            count=count,
            plural=plural,
            anomaly_cards="\n".join(cards),
        )

        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": alert.email,
            "subject": f"ProcureWatch Alert — {count} new anomaly{plural} detected",
            "html": html,
        })


async def check_alerts_after_detection(new_anomaly_ids: list[str]) -> None:
    """Called after detection pipeline; fetches new anomalies and dispatches alert emails."""
    if not new_anomaly_ids:
        return

    from ..core.database import AsyncSessionLocal
    from ..models.anomaly import Anomaly
    from ..models.tender import Tender
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        ids = [uuid.UUID(a_id) for a_id in new_anomaly_ids]
        anomalies = (await db.execute(
            select(Anomaly).where(Anomaly.id.in_(ids))
        )).scalars().all()

        if not anomalies:
            return

        tender_ids = list({a.tender_id for a in anomalies})
        tenders = (await db.execute(
            select(Tender).where(Tender.id.in_(tender_ids))
        )).scalars().all()

        tender_lookup = {
            str(t.id): {
                "title": t.title,
                "ministry": t.ministry,
                "risk_score": t.risk_score,
            }
            for t in tenders
        }

    matcher = AlertMatcher()
    await matcher.check_new_anomalies(list(anomalies), tender_lookup)
