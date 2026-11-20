"""
data_routes.py — Data import/export endpoints.
"""
from flask import Blueprint, jsonify, request, send_file
from backend.guardrails.data_guardrails import require_role

data_bp = Blueprint("data", __name__)


@data_bp.route("/export/trees", methods=["GET"])
@require_role("officer", "admin")
def export_trees():
    """Export all tree records as JSON."""
    from backend.agents.inventory_agent import get_all_trees
    trees = get_all_trees(user_role="admin")
    return jsonify({"trees": trees, "count": len(trees)})


@data_bp.route("/sync/weather", methods=["POST"])
@require_role("admin")
def manual_weather_sync():
    """Manually trigger weather data sync."""
    from backend.live_data.weather_fetcher import fetch_weather
    result = fetch_weather()
    return jsonify({"status": "synced", "weather": result})


@data_bp.route("/sync/osm", methods=["POST"])
@require_role("admin")
def manual_osm_sync():
    """Manually trigger OSM green space sync."""
    from backend.live_data.osm_fetcher import fetch_osm_green_spaces
    result = fetch_osm_green_spaces()
    return jsonify({"status": "synced", "wards_updated": len(result)})


@data_bp.route("/sync/ndvi", methods=["POST"])
@require_role("admin")
def manual_ndvi_sync():
    """Manually trigger NDVI data sync."""
    from backend.live_data.ndvi_fetcher import fetch_ndvi_for_wards
    result = fetch_ndvi_for_wards()
    return jsonify({"status": "synced", "wards_updated": len(result)})
