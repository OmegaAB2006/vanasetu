"""
dashboard_agent.py — Agent 4: Green City Dashboard Agent
Orchestrates Agents 1–3, aggregates KPIs, routes requests.
"""
from backend.agents.inventory_agent import get_summary, get_all_trees
from backend.agents.mapping_agent import get_deficient_wards, get_wards_geojson
from backend.models.db import SessionLocal, LiveWeather
from datetime import datetime


def get_dashboard_summary() -> dict:
    """Aggregate KPIs from all agents for the main dashboard."""
    inventory_summary = get_summary()
    deficient_wards = get_deficient_wards(threshold=15.0)

    db = SessionLocal()
    try:
        weather_row = (
            db.query(LiveWeather)
            .order_by(LiveWeather.fetched_at.desc())
            .first()
        )
        weather = None
        if weather_row:
            weather = {
                "temperature": float(weather_row.temperature or 0),
                "rainfall": float(weather_row.rainfall or 0),
                "humidity": weather_row.humidity,
                "condition_text": weather_row.condition_text,
                "fetched_at": weather_row.fetched_at.isoformat(),
            }
    finally:
        db.close()

    return {
        "inventory": inventory_summary,
        "deficient_wards_count": len(deficient_wards),
        "deficient_wards": deficient_wards[:5],  # top 5 worst
        "weather": weather,
        "last_updated": datetime.utcnow().isoformat(),
    }


def route_nl_query(query: str, user_role: str = "citizen") -> dict:
    """
    Route a natural language query to the correct agent.
    Agent 4 acts as the dispatcher — multi-agent guardrail enforced here.
    """
    q_lower = query.lower()

    if any(kw in q_lower for kw in ["health", "sick", "diseased", "critical", "assess", "diagnose"]):
        agent = "health_agent"
        result = {"message": "Use POST /api/health/assess to submit an image for health analysis."}
    elif any(kw in q_lower for kw in ["inventory", "tree", "ward", "species", "how many", "count", "list"]):
        from backend.agents.inventory_agent import nl_to_filters
        agent = "inventory_agent"
        filters = nl_to_filters(query)
        trees = get_all_trees(user_role=user_role, **filters)
        result = {"trees": trees, "count": len(trees), "filters_applied": filters}
    elif any(kw in q_lower for kw in ["green cover", "ndvi", "map", "ward cover", "deficient"]):
        agent = "mapping_agent"
        result = {"deficient_wards": get_deficient_wards(15.0)}
    else:
        agent = "dashboard_agent"
        result = get_dashboard_summary()

    return {"routed_to": agent, "data": result}
