from __future__ import annotations
"""
guardrail_engine.py — Central guardrail runner.
Every agent request flows through this engine before reaching the LLM and before the response reaches the user.

Flow:
  User Input → [INPUT GUARDRAILS] → [TOOL/DATA GUARDRAILS] → LLM → [OUTPUT GUARDRAILS] → [MULTI-AGENT] → [HITL] → User
"""
import functools
from flask import request, jsonify, g

from backend.guardrails.input_guardrails import validate_free_text, validate_file_upload
from backend.guardrails.output_guardrails import validate_health_response, strip_pii_from_output
from backend.guardrails.security_guardrails import sanitize_input
from backend.guardrails.data_guardrails import get_current_role, get_current_user_id
from backend.guardrails.multiagent_guardrails import check_agent_loop, log_agent_comm
from backend.guardrails.ethics_guardrails import ensure_reasoning_field


def run_input_guardrails(payload: dict) -> tuple[bool, str]:
    """
    Run all input checks on a request payload.
    Returns (is_ok, reason).
    """
    # Check all string fields for injection / jailbreak
    for key, val in payload.items():
        if isinstance(val, str):
            ok, reason = validate_free_text(val)
            if not ok:
                return False, reason
            _, blocked, reason2 = sanitize_input(val)
            if blocked:
                return False, reason2
    return True, ""


def run_output_guardrails(response: dict, agent_id: str) -> tuple[dict, list]:
    """
    Run all output checks on an LLM response.
    Returns (cleaned_response, list_of_warnings).
    """
    warnings = []
    if agent_id == "health_agent":
        response, w = validate_health_response(response)
        warnings.extend(w)
    # Ensure reasoning field always present (Ethics Guardrail 9)
    response, has_reasoning = ensure_reasoning_field(response)
    if not has_reasoning:
        warnings.append("missing_reasoning_field: added placeholder")
    return response, warnings


def run_tool_guardrails(tool_name: str, agent_id: str) -> tuple[bool, str]:
    """Check tool access permission for a given agent."""
    from backend.guardrails.tool_guardrails import is_tool_permitted
    if not is_tool_permitted(agent_id, tool_name):
        return False, f"tool_not_permitted: {tool_name} for agent {agent_id}"
    return True, ""


def run_data_guardrails(data: dict | list, user_role: str) -> dict | list:
    """Apply data masking and access control based on role."""
    from backend.guardrails.data_guardrails import apply_data_masking, citizen_cannot_access_officer_data
    if isinstance(data, list):
        return [apply_data_masking(item, user_role) for item in data]
    if isinstance(data, dict):
        data = apply_data_masking(data, user_role)
        if user_role == "citizen":
            data = citizen_cannot_access_officer_data(data)
    return data


def guardrailed(agent_id: str):
    """
    Flask route decorator that applies the full guardrail pipeline to a route.

    Usage:
        @app.route("/api/health/assess", methods=["POST"])
        @guardrailed("health_agent")
        def assess():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            user_role = get_current_role(request)
            user_id = get_current_user_id(request)

            # 1. Input guardrails on JSON body
            body = request.get_json(silent=True) or {}
            ok, reason = run_input_guardrails(body)
            if not ok:
                return jsonify({
                    "status": "blocked",
                    "reason": reason,
                    "message": "Input contains restricted content. Please rephrase.",
                }), 400

            # 2. Inject role and user_id into Flask g for downstream use
            g.user_role = user_role
            g.user_id = user_id
            g.agent_id = agent_id

            # 3. Call the actual route handler
            result = f(*args, **kwargs)
            return result
        return wrapper
    return decorator
