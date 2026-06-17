"""Geographic mismatch detector — flags vendors supplying to distant states with no prior history."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..models.tender import Tender
    from ..models.vendor import Vendor

logger = structlog.get_logger(__name__)

# Approximate distances (km) between state capitals — representative, not exact.
# Used as a heuristic for cross-state suspicion scoring.
STATE_DISTANCES: dict[tuple[str, str], int] = {}

_RAW_DISTANCES = [
    ("Kerala", "Jammu and Kashmir", 3200),
    ("Kerala", "Himachal Pradesh", 3000),
    ("Kerala", "Punjab", 2900),
    ("Kerala", "Uttarakhand", 2700),
    ("Kerala", "Rajasthan", 2200),
    ("Kerala", "Haryana", 2800),
    ("Tamil Nadu", "Jammu and Kashmir", 3000),
    ("Tamil Nadu", "Punjab", 2700),
    ("Tamil Nadu", "Rajasthan", 2100),
    ("Tamil Nadu", "Himachal Pradesh", 2900),
    ("Andhra Pradesh", "Jammu and Kashmir", 2700),
    ("Andhra Pradesh", "Punjab", 2400),
    ("Telangana", "Jammu and Kashmir", 2600),
    ("Telangana", "Punjab", 2300),
    ("Karnataka", "Jammu and Kashmir", 2800),
    ("Karnataka", "Punjab", 2500),
    ("Karnataka", "Rajasthan", 1900),
    ("Maharashtra", "Jammu and Kashmir", 2200),
    ("Maharashtra", "Manipur", 2700),
    ("Maharashtra", "Assam", 2400),
    ("Gujarat", "Manipur", 2800),
    ("Gujarat", "Assam", 2500),
    ("West Bengal", "Rajasthan", 1900),
    ("West Bengal", "Gujarat", 2000),
    ("Odisha", "Rajasthan", 1700),
    ("Bihar", "Kerala", 2500),
    ("Bihar", "Tamil Nadu", 2400),
    ("Uttar Pradesh", "Kerala", 2300),
    ("Uttar Pradesh", "Tamil Nadu", 2200),
    ("Delhi", "Tamil Nadu", 2200),
    ("Delhi", "Kerala", 2400),
    ("Delhi", "Manipur", 2500),
]

for state_a, state_b, dist in _RAW_DISTANCES:
    STATE_DISTANCES[(state_a, state_b)] = dist
    STATE_DISTANCES[(state_b, state_a)] = dist

# Adjacent/nearby states (distance < 300km) — considered low risk even without prior history
_ADJACENT = [
    ("Maharashtra", "Goa"), ("Maharashtra", "Gujarat"), ("Maharashtra", "Karnataka"),
    ("Gujarat", "Rajasthan"), ("Rajasthan", "Haryana"), ("Haryana", "Punjab"),
    ("Haryana", "Delhi"), ("Delhi", "Uttar Pradesh"), ("Uttar Pradesh", "Bihar"),
    ("Bihar", "Jharkhand"), ("Jharkhand", "West Bengal"), ("West Bengal", "Odisha"),
    ("Odisha", "Andhra Pradesh"), ("Andhra Pradesh", "Telangana"), ("Andhra Pradesh", "Karnataka"),
    ("Telangana", "Karnataka"), ("Karnataka", "Tamil Nadu"), ("Tamil Nadu", "Kerala"),
    ("Karnataka", "Goa"), ("Assam", "Meghalaya"), ("Assam", "Manipur"),
    ("Uttarakhand", "Himachal Pradesh"), ("Himachal Pradesh", "Punjab"),
    ("Punjab", "Jammu and Kashmir"),
]

ADJACENT_PAIRS: set[tuple[str, str]] = set()
for a, b in _ADJACENT:
    ADJACENT_PAIRS.add((a, b))
    ADJACENT_PAIRS.add((b, a))

FIFTY_L_PAISE = 50_00_000 * 100  # ₹50L threshold
DISTANCE_THRESHOLD_KM = 1000


def _estimated_distance(state_a: str, state_b: str) -> int:
    if not state_a or not state_b or state_a == state_b:
        return 0
    if (state_a, state_b) in ADJACENT_PAIRS:
        return 200
    return STATE_DISTANCES.get((state_a, state_b), STATE_DISTANCES.get((state_b, state_a), 1500))


def detect_geo_mismatch(
    vendor: "Vendor",
    tender: "Tender",
    prior_tenders_in_state: int,
) -> dict | None:
    if not vendor.state or not tender.state:
        return None
    if vendor.state == tender.state:
        return None
    if (vendor.state, tender.state) in ADJACENT_PAIRS:
        return None
    if tender.value >= FIFTY_L_PAISE:
        return None  # Large contracts cross-state are normal
    if prior_tenders_in_state > 0:
        return None  # Vendor has history there

    dist = _estimated_distance(vendor.state, tender.state)
    if dist < DISTANCE_THRESHOLD_KM:
        return None

    evidence = {
        "vendor_state": vendor.state,
        "tender_state": tender.state,
        "prior_tenders_in_state": prior_tenders_in_state,
        "estimated_distance_km": dist,
        "value": tender.value,
        "value_rupees": tender.value / 100,
        "threshold_km": DISTANCE_THRESHOLD_KM,
    }

    logger.info("anomaly_detected", type="geo_mismatch", tender_id=str(tender.id), distance=dist)
    return {
        "id": uuid.uuid4(),
        "tender_id": tender.id,
        "type": "geo_mismatch",
        "severity": "medium",
        "evidence": evidence,
        "status": "open",
        "_risk_delta": 20,
    }
