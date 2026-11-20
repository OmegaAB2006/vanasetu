"""
geojson_manager.py — Ward boundary GeoJSON loader and merger.
Merges static ward boundaries with live green cover stats.
"""
import json
import os
from backend.agents.mapping_agent import get_wards_geojson

GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "bengaluru_wards.geojson"
)


def load_ward_boundaries() -> dict:
    """Load ward boundary GeoJSON from file or return synthetic placeholder."""
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}


def get_enriched_geojson() -> dict:
    """Return GeoJSON with live green_cover_pct merged into properties."""
    return get_wards_geojson()


def save_ward_geojson(geojson: dict):
    """Save a GeoJSON dict to the data directory."""
    os.makedirs(os.path.dirname(GEOJSON_PATH), exist_ok=True)
    with open(GEOJSON_PATH, "w") as f:
        json.dump(geojson, f)
