"""
tool_guardrails.py — Guardrail 3: Tool access permissions per agent.
Whitelist of allowed tools per agent. Decorator to enforce permissions.
"""
import functools
from flask import jsonify

# ── Whitelist: agent_id → allowed tool names ─────────────────────────────────
AGENT_TOOL_WHITELIST = {
    "health_agent": {
        "analyze_image",
        "fetch_weather",
        "log_maintenance",
        "read_trees",
    },
    "inventory_agent": {
        "read_trees",
        "insert_tree",
        "update_tree",
        "nl_to_filters",
        "read_maintenance_log",
    },
    "mapping_agent": {
        "read_ward_ndvi",
        "read_osm_green_spaces",
        "read_live_weather",
        "serve_geojson",
        "fetch_osm",
        "fetch_ndvi",
        "fetch_weather",
    },
    "dashboard_agent": {
        "read_trees",
        "read_ward_green_cover",
        "read_live_weather",
        "call_health_agent",
        "call_inventory_agent",
        "call_mapping_agent",
    },
}

# Operations that are NEVER allowed for any agent
BLOCKED_OPERATIONS = {"DELETE", "DROP", "TRUNCATE", "GRANT", "REVOKE"}


def is_tool_permitted(agent_id: str, tool_name: str) -> bool:
    allowed = AGENT_TOOL_WHITELIST.get(agent_id, set())
    return tool_name in allowed


def check_sql_operation(operation: str) -> tuple[bool, str]:
    """Block destructive SQL operations."""
    op = operation.strip().upper().split()[0]
    if op in BLOCKED_OPERATIONS:
        return False, f"blocked_operation: {op} is not allowed"
    return True, ""


def tool_permitted(agent_id: str, tool_name: str):
    """Decorator: wraps a tool function and enforces agent permission."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not is_tool_permitted(agent_id, tool_name):
                return None, f"tool_not_permitted: {tool_name} for {agent_id}"
            return func(*args, **kwargs), None
        return wrapper
    return decorator


def validate_function_call(agent_id: str, fn_name: str, params: dict) -> tuple[bool, str]:
    """
    Validate an LLM-generated function call before execution.
    Checks function name against whitelist and param types.
    """
    if not is_tool_permitted(agent_id, fn_name):
        return False, f"function_not_whitelisted: {fn_name}"
    # Basic param sanity (no SQL keywords in string params)
    for key, val in params.items():
        if isinstance(val, str):
            ok, reason = check_sql_operation(val)
            if not ok:
                return False, reason
    return True, ""
