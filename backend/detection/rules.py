from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from models.tender import Tender
    from models.vendor import Vendor

logger = structlog.get_logger(__name__)

ONE_CR_PAISE  = 100_00_00_000  # ₹1 Cr
FIVE_L_PAISE  = 5_00_00_000    # ₹5L
TWO_L_PAISE   = 2_00_00_000    # ₹2L
FIFTY_L_PAISE = 50_00_00_000   # ₹50L (shell vendor threshold)


def _make_anomaly(tender_id: uuid.UUID, atype: str, severity: str, evidence: dict, risk_delta: int) -> dict:
    return {
        "id": uuid.uuid4(),
        "tender_id": tender_id,
        "type": atype,
        "severity": severity,
        "evidence": evidence,
        "status": "open",
        "_risk_delta": risk_delta,
    }


# ── Original rules ────────────────────────────────────────────────────────────

def detect_single_bid(tender: "Tender") -> dict | None:
    if tender.bid_count != 1:
        return None
    if tender.value < FIVE_L_PAISE:
        return None

    severity = "high" if tender.value >= ONE_CR_PAISE else "medium"
    evidence = {
        "bid_count": tender.bid_count,
        "value": tender.value,
        "value_rupees": tender.value / 100,
        "ministry": tender.ministry,
        "threshold_used": f"₹{FIVE_L_PAISE // 100:,}",
    }
    logger.info("anomaly_detected", type="single_bid", tender_id=str(tender.id), severity=severity)
    return _make_anomaly(tender.id, "single_bid", severity, evidence, 35)


def detect_rushed_timeline(tender: "Tender") -> dict | None:
    if tender.close_date is None or tender.tender_date is None:
        return None
    days_open = (tender.close_date - tender.tender_date).days
    if days_open >= 3:
        return None

    severity = "critical" if days_open < 1 else "high"
    evidence = {
        "open_date": tender.tender_date.isoformat(),
        "close_date": tender.close_date.isoformat(),
        "days_open": days_open,
        "standard_minimum": 7,
    }
    logger.info("anomaly_detected", type="rushed_timeline", tender_id=str(tender.id), days_open=days_open)
    return _make_anomaly(tender.id, "rushed_timeline", severity, evidence, 30)


def detect_bid_splitting(tenders: list["Tender"]) -> list[dict]:
    from collections import defaultdict

    results: list[dict] = []
    groups: dict[tuple, list["Tender"]] = defaultdict(list)
    for t in tenders:
        if t.winner_vendor_id is not None:
            groups[(t.ministry, str(t.winner_vendor_id))].append(t)

    for (ministry, vendor_id), group in groups.items():
        group.sort(key=lambda t: t.tender_date)
        n = len(group)
        for i in range(n):
            window = [group[i]]
            window_start = group[i].tender_date
            for j in range(i + 1, n):
                if (group[j].tender_date - window_start).days <= 30:
                    window.append(group[j])
                else:
                    break

            below = [t for t in window if t.value < TWO_L_PAISE]
            if len(below) < 3:
                continue
            combined = sum(t.value for t in below)
            if combined < FIVE_L_PAISE:
                continue

            evidence = {
                "tender_ids": [str(t.id) for t in below],
                "dates": [t.tender_date.isoformat() for t in below],
                "individual_values": [t.value for t in below],
                "combined_value": combined,
                "combined_rupees": combined / 100,
                "threshold": f"₹{TWO_L_PAISE // 100:,} per tender",
                "vendor_id": vendor_id,
                "ministry": ministry,
            }
            for t in below:
                logger.info("anomaly_detected", type="bid_splitting", tender_id=str(t.id))
                results.append(_make_anomaly(t.id, "bid_splitting", "high", evidence, 40))
            break

    return results


# ── Phase 2b rules ────────────────────────────────────────────────────────────

def detect_shell_vendor(vendor: "Vendor", tender: "Tender") -> dict | None:
    """Flag vendors registered <6 months before their first large win."""
    if not vendor.registration_date or not tender.tender_date:
        return None

    age_days = (tender.tender_date - vendor.registration_date).days
    if age_days >= 180:
        return None
    if tender.value < FIFTY_L_PAISE:
        return None

    severity = "critical" if age_days < 30 else "high"
    evidence = {
        "vendor_id": str(vendor.id),
        "vendor_name": vendor.name,
        "registration_date": vendor.registration_date.isoformat(),
        "tender_date": tender.tender_date.isoformat(),
        "days_since_registration": age_days,
        "value": tender.value,
        "value_rupees": tender.value / 100,
        "threshold_value": f"₹{FIFTY_L_PAISE // 100:,}",
    }
    logger.info("anomaly_detected", type="shell_vendor", tender_id=str(tender.id), age_days=age_days)
    return _make_anomaly(tender.id, "shell_vendor", severity, evidence, 50)


def detect_repeat_monopoly(
    vendor: "Vendor",
    ministry: str,
    ministry_wins: int,
    total_ministry_tenders: int,
) -> dict | None:
    """Flag vendor winning >70% of tenders in a single ministry."""
    if total_ministry_tenders < 5:
        return None
    win_rate = ministry_wins / total_ministry_tenders
    if win_rate < 0.70:
        return None

    severity = "critical" if win_rate >= 0.90 else "high"
    evidence = {
        "vendor_id": str(vendor.id),
        "vendor_name": vendor.name,
        "ministry": ministry,
        "wins_in_ministry": ministry_wins,
        "total_ministry_tenders": total_ministry_tenders,
        "win_rate": round(win_rate, 3),
        "threshold": "70%",
    }
    logger.info("anomaly_detected", type="repeat_monopoly", vendor_id=str(vendor.id), win_rate=win_rate)
    return evidence  # returned as dict; caller creates anomaly per-tender


def detect_post_award_inflation(
    original_value: int,
    current_value: int,
    tender_id: uuid.UUID,
    amendments: list[dict],
) -> dict | None:
    """Flag contracts whose current value exceeds original by >25%."""
    if original_value <= 0:
        return None
    inflation = (current_value - original_value) / original_value
    if inflation < 0.25:
        return None

    severity = "critical" if inflation >= 1.0 else "high"
    evidence = {
        "original_value": original_value,
        "current_value": current_value,
        "original_rupees": original_value / 100,
        "current_rupees": current_value / 100,
        "inflation_pct": round(inflation * 100, 1),
        "num_amendments": len(amendments),
        "amendments": amendments[:5],  # cap evidence size
    }
    logger.info("anomaly_detected", type="post_award_inflation", tender_id=str(tender_id), pct=inflation)
    return _make_anomaly(tender_id, "post_award_inflation", severity, evidence, 55)


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_all_rules(tender: "Tender", recent_tenders: list["Tender"]) -> tuple[int, list[dict]]:
    anomalies: list[dict] = []
    total_risk = 0

    a1 = detect_single_bid(tender)
    if a1:
        anomalies.append(a1)
        total_risk += a1["_risk_delta"]

    a2 = detect_rushed_timeline(tender)
    if a2:
        anomalies.append(a2)
        total_risk += a2["_risk_delta"]

    return min(total_risk, 100), anomalies
