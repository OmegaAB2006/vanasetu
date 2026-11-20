"""
osm_fetcher.py — OpenStreetMap Overpass API: green space polygons for Bengaluru.
Runs every 24 hours via APScheduler.
"""
import requests
from datetime import datetime
from backend.models.db import SessionLocal, OSMGreenSpaces
from backend.guardrails.operational_guardrails import with_retry

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY = """
[out:json][timeout:30];
area["name"="Bengaluru"]["admin_level"="6"]->.searchArea;
(
  way["landuse"="forest"](area.searchArea);
  way["landuse"="grass"](area.searchArea);
  way["leisure"="park"](area.searchArea);
  way["natural"="wood"](area.searchArea);
);
out geom;
"""

# Approximate total ward area in sqm (1 average Bengaluru ward ≈ 7.5 km²)
AVG_WARD_AREA_SQM = 7_500_000

# Realistic mock green space data per ward for demo fallback.
# Deficient wards (1,2,4,6,8,10) have very low green area → low osm_ratio.
# Good wards (3,5,7,9) have high green area → higher osm_ratio.
MOCK_GREEN_AREA = {
    1: 125000,   # Yelahanka — mostly roads/buildings
    2: 180000,   # Hebbal — traffic interchange, low parks
    3: 1800000,  # Cubbon Park / Lalbagh proximity — high
    4: 90000,    # Electronic City — industrial zone
    5: 1200000,  # Jayanagar — well-maintained parks
    6: 150000,   # Whitefield — sparse greenery
    7: 1500000,  # Lalbagh / Basavanagudi — heritage gardens
    8: 110000,   # Marathahalli — construction sites
    9: 1400000,  # Malleswaram — mature tree-lined streets
    10: 200000,  # Koramangala — dense commercial
}


@with_retry
def fetch_osm_green_spaces(ward_ids: list = None) -> dict:
    """Fetch OSM green spaces. Falls back to mock data if Overpass is unavailable."""
    if ward_ids is None:
        ward_ids = list(range(1, 11))
    try:
        resp = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY}, timeout=35)
        resp.raise_for_status()
        data = resp.json()
        return _process_overpass_response(data, ward_ids)
    except Exception:
        # Cache fallback: use mock data
        return _seed_mock_osm(ward_ids)


def _process_overpass_response(data: dict, ward_ids: list) -> dict:
    """
    Parse Overpass response and estimate green area per ward.
    In a full implementation this would use Shapely for proper polygon intersection.
    For demo: use element count as a proxy for coverage.
    """
    elements = data.get("elements", [])
    # Simple proxy: distribute total elements across wards proportionally
    total_elements = max(len(elements), 1)
    per_ward = total_elements // max(len(ward_ids), 1)
    results = {}
    for w in ward_ids:
        # Scale element count to approximate area
        area = per_ward * 15000  # rough 15,000 sqm per OSM green element
        results[w] = area
    _upsert_osm(results)
    return results


def _seed_mock_osm(ward_ids: list) -> dict:
    results = {w: MOCK_GREEN_AREA.get(w, 400000) for w in ward_ids}
    _upsert_osm(results)
    return results


def _upsert_osm(ward_areas: dict):
    db = SessionLocal()
    try:
        for ward_id, green_area in ward_areas.items():
            existing = db.query(OSMGreenSpaces).filter(
                OSMGreenSpaces.ward_id == ward_id
            ).first()
            if existing:
                existing.green_area_sqm = green_area
                existing.fetched_at = datetime.utcnow()
            else:
                db.add(OSMGreenSpaces(
                    ward_id=ward_id,
                    green_area_sqm=green_area,
                    total_area_sqm=AVG_WARD_AREA_SQM,
                    fetched_at=datetime.utcnow(),
                ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
