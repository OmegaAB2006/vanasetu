"""
mapping_agent.py — Agent 3: Green Cover Mapping Agent
Calculates composite green_cover_pct per ward and serves enriched GeoJSON.
"""
import json
import os
from datetime import datetime
from backend.models.db import SessionLocal, WardGreenCover, WardNDVI, OSMGreenSpaces, LiveWeather

GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "bengaluru_wards.geojson"
)


def calculate_composite_green_cover(ward_id: int, db) -> float:
    """
    green_cover_pct = (NDVI_normalized * 0.5) + (OSM_ratio * 0.3) + (rainfall_bonus * 0.2)
    """
    ndvi_row = (
        db.query(WardNDVI)
        .filter(WardNDVI.ward_id == ward_id)
        .order_by(WardNDVI.fetched_at.desc())
        .first()
    )
    osm_row = (
        db.query(OSMGreenSpaces)
        .filter(OSMGreenSpaces.ward_id == ward_id)
        .order_by(OSMGreenSpaces.fetched_at.desc())
        .first()
    )
    weather_row = (
        db.query(LiveWeather)
        .order_by(LiveWeather.fetched_at.desc())
        .first()
    )

    ndvi_normalized = 0.3
    if ndvi_row and ndvi_row.ndvi_value is not None:
        raw = float(ndvi_row.ndvi_value)
        ndvi_normalized = max(0.0, min(1.0, (raw + 1) / 2))

    osm_ratio = 0.1
    if osm_row and osm_row.total_area_sqm and float(osm_row.total_area_sqm) > 0:
        osm_ratio = float(osm_row.green_area_sqm) / float(osm_row.total_area_sqm)

    rainfall_bonus = 0.0
    if weather_row and weather_row.rainfall and float(weather_row.rainfall) > 50:
        rainfall_bonus = 0.1

    pct = (ndvi_normalized * 0.5 + osm_ratio * 0.3 + rainfall_bonus * 0.2) * 100
    return round(min(pct, 100.0), 2)


def recalculate_all_wards():
    """Triggered by scheduler every 30 min — recomputes all wards."""
    db = SessionLocal()
    try:
        ward_ids = [row[0] for row in db.query(WardNDVI.ward_id).distinct()]
        for w in ward_ids:
            pct = calculate_composite_green_cover(w, db)
            existing = db.query(WardGreenCover).filter(WardGreenCover.ward_id == w).first()
            if existing:
                existing.green_cover_pct = pct
                existing.calculated_at = datetime.utcnow()
            else:
                db.add(WardGreenCover(ward_id=w, green_cover_pct=pct))
        db.commit()
    finally:
        db.close()


def get_wards_geojson() -> dict:
    """
    Load ward boundary GeoJSON and merge live green_cover_pct into each feature's properties.
    If the GeoJSON file doesn't exist, return a minimal placeholder.
    """
    db = SessionLocal()
    try:
        cover_map = {
            row.ward_id: float(row.green_cover_pct)
            for row in db.query(WardGreenCover).all()
        }
    finally:
        db.close()

    if not os.path.exists(GEOJSON_PATH):
        # Return synthetic GeoJSON for development / demo
        return _synthetic_geojson(cover_map)

    with open(GEOJSON_PATH, "r") as f:
        geojson = json.load(f)

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        ward_id = props.get("ward_no") or props.get("WARD_NO") or props.get("id")
        if ward_id:
            props["green_cover_pct"] = cover_map.get(int(ward_id), 0.0)
            props["last_updated"] = datetime.utcnow().isoformat()

    return geojson


def get_deficient_wards(threshold: float = 15.0) -> list:
    """Return wards whose green_cover_pct is below threshold."""
    db = SessionLocal()
    try:
        rows = (
            db.query(WardGreenCover)
            .filter(WardGreenCover.green_cover_pct < threshold)
            .order_by(WardGreenCover.green_cover_pct)
            .all()
        )
        return [
            {
                "ward_id": r.ward_id,
                "green_cover_pct": float(r.green_cover_pct),
                "calculated_at": r.calculated_at.isoformat(),
            }
            for r in rows
        ]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Realistic ward boundaries — hand-crafted polygons that tile across
# Bengaluru's actual footprint (12.83–13.14 N, 77.46–77.78 E).
# Each ward covers ~40–60 km² with irregular, map-realistic boundaries.
# Named after the actual Bengaluru neighbourhoods they approximate.
# ---------------------------------------------------------------------------
_BENGALURU_WARDS = [
    # Ward 1 — Yelahanka / North Bengaluru (large, low density — typically deficient)
    {
        "ward_no": 1, "ward_name": "Yelahanka",
        "coords": [
            [77.5950, 13.0800], [77.6300, 13.0820], [77.6520, 13.0750],
            [77.6600, 13.0600], [77.6450, 13.0400], [77.6150, 13.0350],
            [77.5900, 13.0450], [77.5780, 13.0620], [77.5850, 13.0750],
            [77.5950, 13.0800],
        ],
    },
    # Ward 2 — Hebbal / Byatarayanapura (north, mixed — often deficient)
    {
        "ward_no": 2, "ward_name": "Hebbal–Byatarayanapura",
        "coords": [
            [77.5900, 13.0450], [77.6150, 13.0350], [77.6450, 13.0400],
            [77.6550, 13.0280], [77.6450, 13.0100], [77.6200, 13.0050],
            [77.5950, 13.0100], [77.5750, 13.0200], [77.5700, 13.0350],
            [77.5900, 13.0450],
        ],
    },
    # Ward 3 — Cubbon Park / Shivajinagar (central, well-forested — good)
    {
        "ward_no": 3, "ward_name": "Cubbon Park–Shivajinagar",
        "coords": [
            [77.5800, 12.9800], [77.6100, 12.9820], [77.6300, 12.9780],
            [77.6380, 12.9680], [77.6250, 12.9560], [77.6050, 12.9520],
            [77.5820, 12.9560], [77.5680, 12.9680], [77.5700, 12.9780],
            [77.5800, 12.9800],
        ],
    },
    # Ward 4 — Electronic City / Bommanahalli (south-east, industrial — critical)
    {
        "ward_no": 4, "ward_name": "Electronic City",
        "coords": [
            [77.6400, 12.8450], [77.6800, 12.8500], [77.7050, 12.8400],
            [77.7100, 12.8200], [77.6950, 12.8000], [77.6650, 12.7950],
            [77.6350, 12.8050], [77.6200, 12.8250], [77.6300, 12.8400],
            [77.6400, 12.8450],
        ],
    },
    # Ward 5 — Jayanagar / JP Nagar (south, well-planned — good)
    {
        "ward_no": 5, "ward_name": "Jayanagar–JP Nagar",
        "coords": [
            [77.5600, 12.9200], [77.5900, 12.9250], [77.6100, 12.9200],
            [77.6200, 12.9050], [77.6100, 12.8880], [77.5850, 12.8820],
            [77.5600, 12.8880], [77.5450, 12.9000], [77.5480, 12.9150],
            [77.5600, 12.9200],
        ],
    },
    # Ward 6 — Whitefield / ITPL (east, rapid development — deficient)
    {
        "ward_no": 6, "ward_name": "Whitefield–ITPL",
        "coords": [
            [77.7200, 12.9800], [77.7600, 12.9850], [77.7800, 12.9700],
            [77.7820, 12.9500], [77.7650, 12.9300], [77.7350, 12.9250],
            [77.7100, 12.9380], [77.7050, 12.9600], [77.7150, 12.9750],
            [77.7200, 12.9800],
        ],
    },
    # Ward 7 — Lalbagh / Basavanagudi (south-central, heritage parks — good)
    {
        "ward_no": 7, "ward_name": "Lalbagh–Basavanagudi",
        "coords": [
            [77.5700, 12.9500], [77.5900, 12.9550], [77.6100, 12.9520],
            [77.6250, 12.9380], [77.6180, 12.9220], [77.5980, 12.9150],
            [77.5750, 12.9170], [77.5600, 12.9280], [77.5620, 12.9430],
            [77.5700, 12.9500],
        ],
    },
    # Ward 8 — Marathahalli / Varthur (east, construction boom — deficient)
    {
        "ward_no": 8, "ward_name": "Marathahalli–Varthur",
        "coords": [
            [77.6900, 12.9500], [77.7200, 12.9550], [77.7400, 12.9450],
            [77.7450, 12.9280], [77.7300, 12.9100], [77.7050, 12.9050],
            [77.6800, 12.9150], [77.6700, 12.9330], [77.6800, 12.9470],
            [77.6900, 12.9500],
        ],
    },
    # Ward 9 — Malleswaram / Rajajinagar (west, residential & green — good)
    {
        "ward_no": 9, "ward_name": "Malleswaram–Rajajinagar",
        "coords": [
            [77.5350, 13.0000], [77.5650, 13.0050], [77.5850, 12.9950],
            [77.5900, 12.9800], [77.5800, 12.9650], [77.5600, 12.9600],
            [77.5350, 12.9680], [77.5200, 12.9800], [77.5250, 12.9950],
            [77.5350, 13.0000],
        ],
    },
    # Ward 10 — Koramangala / HSR Layout (south-east, dense — marginally deficient)
    {
        "ward_no": 10, "ward_name": "Koramangala–HSR Layout",
        "coords": [
            [77.6200, 12.9200], [77.6500, 12.9250], [77.6700, 12.9150],
            [77.6750, 12.8980], [77.6600, 12.8820], [77.6350, 12.8780],
            [77.6100, 12.8880], [77.6000, 12.9050], [77.6100, 12.9180],
            [77.6200, 12.9200],
        ],
    },
]


def _synthetic_geojson(cover_map: dict) -> dict:
    """
    Realistic ward GeoJSON spanning Bengaluru's actual geography.
    Each ward is an irregular polygon based on real neighbourhood boundaries.
    """
    now = datetime.utcnow().isoformat()
    features = []
    for wd in _BENGALURU_WARDS:
        w = wd["ward_no"]
        pct = cover_map.get(w, 20.0)
        features.append({
            "type": "Feature",
            "properties": {
                "ward_no": w,
                "ward_name": wd["ward_name"],
                "green_cover_pct": pct,
                "last_updated": now,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [wd["coords"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}
