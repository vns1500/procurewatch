"""Unit tests for detection rules — no DB required."""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
import uuid


def make_tender(bid_count=3, value=10_000_00, days_open=10):
    t = MagicMock()
    t.id = uuid.uuid4()
    t.bid_count = bid_count
    t.value = value
    t.tender_date = date.today() - timedelta(days=days_open)
    t.close_date = date.today()
    t.ministry = "Ministry of Test"
    t.gem_id = "TEST001"
    return t


def test_single_bid_flag_above_threshold():
    """single_bid fires when bid_count == 1 AND value > ₹5L."""
    from backend.detection.rules import detect_single_bid
    tender = make_tender(bid_count=1, value=6_00_00_000)  # ₹6L in paise
    result = detect_single_bid(tender)
    assert result is not None
    assert result["type"] == "single_bid"
    assert result["evidence"]["bid_count"] == 1


def test_single_bid_no_flag_low_value():
    """single_bid does NOT fire when value is below ₹5L threshold."""
    from backend.detection.rules import detect_single_bid
    tender = make_tender(bid_count=1, value=1_00_00_000)  # ₹1L
    result = detect_single_bid(tender)
    assert result is None


def test_single_bid_no_flag_multiple_bids():
    """single_bid does NOT fire when bid_count > 1."""
    from backend.detection.rules import detect_single_bid
    tender = make_tender(bid_count=3, value=10_00_00_000)
    result = detect_single_bid(tender)
    assert result is None


def test_rushed_timeline_flag():
    """rushed_timeline fires when bid window < 3 days."""
    from backend.detection.rules import detect_rushed_timeline
    tender = make_tender(days_open=2)
    result = detect_rushed_timeline(tender)
    assert result is not None
    assert result["type"] == "rushed_timeline"
    assert result["evidence"]["days_open"] == 2


def test_rushed_timeline_critical_zero_days():
    """rushed_timeline is CRITICAL when bid window < 1 day."""
    from backend.detection.rules import detect_rushed_timeline
    tender = make_tender(days_open=0)
    result = detect_rushed_timeline(tender)
    assert result is not None
    assert result["severity"] == "critical"


def test_rushed_timeline_no_flag_normal_window():
    """rushed_timeline does NOT fire for normal bid windows."""
    from backend.detection.rules import detect_rushed_timeline
    tender = make_tender(days_open=14)
    result = detect_rushed_timeline(tender)
    assert result is None


def test_risk_contributions_values_are_reasonable():
    """Every risk contribution is between 1 and 100."""
    from backend.detection.risk_aggregator import RISK_CONTRIBUTIONS
    for anomaly_type, score in RISK_CONTRIBUTIONS.items():
        assert 1 <= score <= 100, f"{anomaly_type} score {score} out of range"


def test_risk_contributions_known_types():
    """Core anomaly types are all present."""
    from backend.detection.risk_aggregator import RISK_CONTRIBUTIONS
    for expected in ("single_bid", "rushed_timeline", "bid_splitting", "inflated_pricing", "shell_vendor"):
        assert expected in RISK_CONTRIBUTIONS, f"Missing risk type: {expected}"
