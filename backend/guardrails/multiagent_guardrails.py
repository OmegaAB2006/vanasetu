"""
multiagent_guardrails.py — Guardrail 8: Agent coordination, loop prevention, schema validation.
"""
import hashlib
import json
from flask import g
from backend.models.db import SessionLocal, AgentCommLog
from datetime import datetime

MAX_LOOP_COUNT = 3
ALLOWED_INTER_AGENT_PATHS = {
    ("dashboard_agent", "health_agent"),
    ("dashboard_agent", "inventory_agent"),
    ("dashboard_agent", "mapping_agent"),
}


def get_request_id() -> str:
    """Get the current request's unique ID from Flask g."""
    return getattr(g, "request_id", "unknown")


def check_agent_loop(source_agent: str, dest_agent: str) -> tuple[bool, str]:
    """
    Prevent infinite loops. If the same agent pair appears > MAX_LOOP_COUNT
    times in one request, block the call.
    """
    loop_counter = getattr(g, "loop_counter", {})
    key = f"{source_agent}->{dest_agent}"
    count = loop_counter.get(key, 0) + 1
    loop_counter[key] = count
    if hasattr(g, "loop_counter"):
        g.loop_counter = loop_counter
    if count > MAX_LOOP_COUNT:
        return True, f"agent_loop_detected: {key} called {count} times"
    return False, ""


def check_agent_route_permitted(source_agent: str, dest_agent: str) -> tuple[bool, str]:
    """Only allow approved agent-to-agent communication paths."""
    if (source_agent, dest_agent) not in ALLOWED_INTER_AGENT_PATHS:
        return False, f"inter_agent_call_not_permitted: {source_agent} → {dest_agent}"
    return True, ""


def log_agent_comm(source_agent: str, dest_agent: str, payload: dict):
    """Write inter-agent call to agent_comm_log."""
    request_id = get_request_id()
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    db = SessionLocal()
    try:
        db.add(AgentCommLog(
            request_id=request_id,
            source_agent=source_agent,
            dest_agent=dest_agent,
            payload_hash=payload_hash,
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def validate_inter_agent_payload(payload: dict, expected_keys: list) -> tuple[bool, str]:
    """Validate schema before cross-agent data transfer."""
    missing = [k for k in expected_keys if k not in payload]
    if missing:
        return False, f"inter_agent_schema_violation: missing keys {missing}"
    return True, ""
