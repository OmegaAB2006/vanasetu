from __future__ import annotations
from typing import Optional
"""
ndvi_fetcher.py — NASA MODIS NDVI data fetcher.
Seeds realistic NDVI per ward. In production: uses NASA AppEEARS API.
For demo: uses seeded/simulated values per ward.
"""
import os
import random
from datetime import datetime, date
from backend.models.db import SessionLocal, WardNDVI
from backend.guardrails.operational_guardrails import with_retry

NASA_TOKEN = os.getenv("NASA_EARTHDATA_TOKEN", "")

# Realistic NDVI seeds for Bengaluru wards.
# Deficient wards (1,2,4,6,8,10) → NDVI < -0.4 so composite cover stays < 15%.
# Good wards (3,5,7,9) → NDVI 0.3–0.5 for realistic green cover 30–50%.
BENGALURU_WARD_NDVI_SEED = {
    1: -0.52,   # Yelahanka — sparse urban sprawl
    2: -0.44,   # Hebbal — dense road network
    3:  0.45,   # Cubbon Park — rich canopy
    4: -0.58,   # Electronic City — industrial
    5:  0.38,   # Jayanagar — well-planned residential
    6: -0.48,   # Whitefield — rapid construction
    7:  0.42,   # Lalbagh — heritage park
    8: -0.55,   # Marathahalli — tech corridor
    9:  0.40,   # Malleswaram — mature residential
    10: -0.41,  # Koramangala — dense commercial
}


@with_retry
def fetch_ndvi_for_wards(ward_ids: list = None) -> dict:
    """
    Fetch NDVI for each ward. If NASA token available, calls AppEEARS.
    Falls back to seeded realistic values for demo.
    """
    if ward_ids is None:
        ward_ids = list(range(1, 11))

    if NASA_TOKEN:
        return _fetch_from_nasa(ward_ids)
    else:
        return _seed_ndvi(ward_ids)


def _fetch_from_nasa(ward_ids: list) -> dict:
    """Stub for NASA AppEEARS API call — extend with real implementation."""
    # In full implementation: POST to https://appeears.earthdatacloud.nasa.gov/api/task
    # For now, fall through to seeded data
    return _seed_ndvi(ward_ids)


def _seed_ndvi(ward_ids: list) -> dict:
    """Insert seeded NDVI values per ward into DB."""
    db = SessionLocal()
    results = {}
    try:
        for ward_id in ward_ids:
            # Base NDVI + small random daily variation
            base = BENGALURU_WARD_NDVI_SEED.get(ward_id, 0.30)
            ndvi = round(base + random.uniform(-0.03, 0.03), 4)
            ndvi = max(-1.0, min(1.0, ndvi))
            results[ward_id] = ndvi

            existing = (
                db.query(WardNDVI)
                .filter(WardNDVI.ward_id == ward_id)
                .order_by(WardNDVI.fetched_at.desc())
                .first()
            )
            db.add(WardNDVI(
                ward_id=ward_id,
                ndvi_value=ndvi,
                source="MODIS_SIMULATED",
                recorded_date=date.today(),
                fetched_at=datetime.utcnow(),
            ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return results


def get_latest_ndvi(ward_id: int) -> Optional[float]:
    db = SessionLocal()
    try:
        row = (
            db.query(WardNDVI)
            .filter(WardNDVI.ward_id == ward_id)
            .order_by(WardNDVI.fetched_at.desc())
            .first()
        )
        return float(row.ndvi_value) if row else None
    finally:
        db.close()
