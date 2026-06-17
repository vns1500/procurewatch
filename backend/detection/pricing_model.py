"""Isolation Forest pricing anomaly detector."""
from __future__ import annotations

import math
import os
import pickle
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog

if TYPE_CHECKING:
    from models.tender import Tender
    from models.price_benchmark import PriceBenchmark

logger = structlog.get_logger(__name__)

MODEL_PATH = Path("/app/models/isolation_forest.pkl")
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

ITEM_BENCHMARKS: list[dict[str, Any]] = [
    # (item_name, unit, avg_rupees, min_rupees, max_rupees)
    {"item": "A4 Paper", "unit": "ream", "avg": 280, "min": 200, "max": 450},
    {"item": "Laptop - Standard", "unit": "unit", "avg": 52000, "min": 35000, "max": 90000},
    {"item": "Laptop - High Performance", "unit": "unit", "avg": 85000, "min": 60000, "max": 150000},
    {"item": "Desktop Computer", "unit": "unit", "avg": 35000, "min": 25000, "max": 65000},
    {"item": "Laser Printer", "unit": "unit", "avg": 18000, "min": 8000, "max": 45000},
    {"item": "UPS 1KVA", "unit": "unit", "avg": 8500, "min": 5000, "max": 18000},
    {"item": "Office Chair", "unit": "unit", "avg": 9500, "min": 4500, "max": 22000},
    {"item": "Office Table", "unit": "unit", "avg": 12000, "min": 6000, "max": 28000},
    {"item": "Steel Almirah", "unit": "unit", "avg": 14000, "min": 8000, "max": 30000},
    {"item": "CCTV Camera", "unit": "unit", "avg": 6500, "min": 3500, "max": 15000},
    {"item": "NVR 16 Channel", "unit": "unit", "avg": 18000, "min": 10000, "max": 35000},
    {"item": "Air Conditioner 1.5T", "unit": "unit", "avg": 38000, "min": 28000, "max": 65000},
    {"item": "Air Conditioner 2T", "unit": "unit", "avg": 48000, "min": 35000, "max": 80000},
    {"item": "Server - Rack Mount", "unit": "unit", "avg": 350000, "min": 180000, "max": 800000},
    {"item": "Network Switch 24-port", "unit": "unit", "avg": 22000, "min": 12000, "max": 55000},
    {"item": "Router Enterprise", "unit": "unit", "avg": 45000, "min": 25000, "max": 100000},
    {"item": "Solar Panel 250W", "unit": "unit", "avg": 8500, "min": 6000, "max": 14000},
    {"item": "Solar Inverter 10kW", "unit": "unit", "avg": 95000, "min": 60000, "max": 180000},
    {"item": "Diesel Generator 15kVA", "unit": "unit", "avg": 180000, "min": 120000, "max": 350000},
    {"item": "Ambulance Type B", "unit": "unit", "avg": 850000, "min": 600000, "max": 1500000},
    {"item": "Ambulance Type C", "unit": "unit", "avg": 2500000, "min": 1800000, "max": 4000000},
    {"item": "Ventilator ICU", "unit": "unit", "avg": 1200000, "min": 800000, "max": 2500000},
    {"item": "ECG Machine", "unit": "unit", "avg": 85000, "min": 55000, "max": 200000},
    {"item": "PPE Kit", "unit": "kit", "avg": 850, "min": 500, "max": 2500},
    {"item": "N95 Mask", "unit": "unit", "avg": 85, "min": 45, "max": 250},
    {"item": "Uniform - Cotton", "unit": "set", "avg": 1200, "min": 700, "max": 2500},
    {"item": "Safety Boot", "unit": "pair", "avg": 1800, "min": 1000, "max": 4500},
    {"item": "Cement OPC 53 Grade", "unit": "bag", "avg": 380, "min": 320, "max": 480},
    {"item": "TMT Steel Bar Fe500", "unit": "MT", "avg": 58000, "min": 48000, "max": 72000},
    {"item": "Bitumen VG30", "unit": "MT", "avg": 42000, "min": 35000, "max": 55000},
    {"item": "Sand (River)", "unit": "cubic_m", "avg": 2500, "min": 1500, "max": 5000},
    {"item": "Aggregate 20mm", "unit": "cubic_m", "avg": 1800, "min": 1200, "max": 3500},
    {"item": "GPS Tracking Device", "unit": "unit", "avg": 8500, "min": 5000, "max": 18000},
    {"item": "Fire Extinguisher 9L", "unit": "unit", "avg": 2500, "min": 1500, "max": 5000},
    {"item": "Water Purifier RO", "unit": "unit", "avg": 18000, "min": 8000, "max": 45000},
    {"item": "Tractor 45HP", "unit": "unit", "avg": 650000, "min": 500000, "max": 900000},
    {"item": "Power Tiller", "unit": "unit", "avg": 95000, "min": 70000, "max": 140000},
    {"item": "Light Commercial Vehicle", "unit": "unit", "avg": 850000, "min": 650000, "max": 1400000},
    {"item": "Heavy Truck 16T", "unit": "unit", "avg": 2200000, "min": 1600000, "max": 3500000},
    {"item": "Printing Services", "unit": "ream_equiv", "avg": 4500, "min": 2500, "max": 9000},
]


def get_benchmark_seeds() -> list[dict[str, Any]]:
    """Return seeding data for price_benchmarks table."""
    seeds = []
    for b in ITEM_BENCHMARKS:
        seeds.append({
            "item_name": b["item"],
            "unit": b["unit"],
            "avg_price": int(b["avg"] * 100),
            "min_price": int(b["min"] * 100),
            "max_price": int(b["max"] * 100),
            "source": "market_survey_2024",
        })
    return seeds


class PricingAnomalyDetector:
    def __init__(self) -> None:
        self._model: Any = None
        self._ministry_stats: dict[str, dict[str, float]] = {}
        self._trained = False

    def _extract_features(self, tenders: list["Tender"]) -> np.ndarray:
        features = []
        for t in tenders:
            value_lakhs = t.value / (1_00_000 * 100) if t.value else 1
            log_value = math.log1p(value_lakhs)
            bid_count = float(t.bid_count or 1)
            try:
                days_open = float((t.close_date - t.tender_date).days) if t.close_date and t.tender_date else 7.0
            except Exception:
                days_open = 7.0
            features.append([log_value, bid_count, max(days_open, 0)])
        return np.array(features, dtype=np.float32)

    def _build_ministry_stats(self, tenders: list["Tender"]) -> None:
        from collections import defaultdict
        groups: dict[str, list[float]] = defaultdict(list)
        for t in tenders:
            if t.value:
                groups[t.ministry].append(math.log1p(t.value / (1_00_000 * 100)))
        for ministry, vals in groups.items():
            arr = np.array(vals)
            self._ministry_stats[ministry] = {"mean": float(arr.mean()), "std": max(float(arr.std()), 0.01)}

    def train(self, tenders: list["Tender"]) -> None:
        if len(tenders) < 10:
            logger.warning("insufficient_data_for_training", count=len(tenders))
            return

        from sklearn.ensemble import IsolationForest

        self._build_ministry_stats(tenders)
        X = self._extract_features(tenders)

        model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)
        self._model = model
        self._trained = True

        MODEL_PATH.write_bytes(pickle.dumps({"model": model, "ministry_stats": self._ministry_stats}))
        logger.info("isolation_forest_trained", samples=len(tenders), model_path=str(MODEL_PATH))

    def load(self) -> bool:
        if not MODEL_PATH.exists():
            return False
        try:
            data = pickle.loads(MODEL_PATH.read_bytes())
            self._model = data["model"]
            self._ministry_stats = data.get("ministry_stats", {})
            self._trained = True
            logger.info("isolation_forest_loaded", path=str(MODEL_PATH))
            return True
        except Exception as exc:
            logger.warning("model_load_failed", error=str(exc))
            return False

    def score_tender(self, tender: "Tender", benchmarks: list["PriceBenchmark"]) -> dict | None:
        if not self._trained or self._model is None:
            return None

        X = self._extract_features([tender])
        score = self._model.score_samples(X)[0]
        is_outlier = self._model.predict(X)[0] == -1

        # Also check against price benchmarks
        best_deviation = 0.0
        benchmark_info: dict[str, Any] = {}
        for bm in benchmarks:
            if bm.avg_price and bm.avg_price > 0:
                deviation = tender.value / bm.avg_price
                if deviation > best_deviation:
                    best_deviation = deviation
                    benchmark_info = {
                        "benchmark_item": bm.item_name,
                        "benchmark_avg": bm.avg_price,
                        "benchmark_min": bm.min_price,
                        "benchmark_max": bm.max_price,
                        "deviation_factor": round(deviation, 2),
                    }

        # Flag if IsolationForest says outlier OR if price is >3x any benchmark avg
        significant_deviation = best_deviation > 3.0

        if not (is_outlier or significant_deviation):
            return None

        # Choose highest signal
        if best_deviation > 5.0:
            severity = "critical"
        elif best_deviation > 3.0 or (is_outlier and score < -0.15):
            severity = "high"
        else:
            severity = "medium"

        evidence = {
            "isolation_score": round(float(score), 4),
            "is_statistical_outlier": bool(is_outlier),
            "tender_value_paise": tender.value,
            "tender_value_rupees": tender.value / 100,
            **benchmark_info,
        }

        logger.info("pricing_anomaly", tender_id=str(tender.id), severity=severity, score=score)
        return {
            "id": uuid.uuid4(),
            "tender_id": tender.id,
            "type": "inflated_pricing",
            "severity": severity,
            "evidence": evidence,
            "status": "open",
            "_risk_delta": 40,
        }

    def find_similar_tenders_by_value(
        self,
        tender: "Tender",
        all_tenders: list["Tender"],
    ) -> list[dict[str, Any]]:
        """Find tenders with similar value in same ministry for comparison."""
        target_log = math.log1p(tender.value / (1_00_000 * 100))
        similar = []
        for t in all_tenders:
            if t.id == tender.id:
                continue
            if t.ministry == tender.ministry and t.value:
                t_log = math.log1p(t.value / (1_00_000 * 100))
                if abs(t_log - target_log) < 0.5:
                    similar.append({"tender_id": str(t.id), "value": t.value, "ministry": t.ministry})
        return similar[:5]
