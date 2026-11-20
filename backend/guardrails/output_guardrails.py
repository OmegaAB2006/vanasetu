from __future__ import annotations
from typing import Optional
"""
output_guardrails.py — Guardrail 2: Hallucination detection, toxicity, format validation, PII strip.
"""
import re
import json
import jsonschema
from backend.models.db import SessionLocal, Tree

# ── JSON output schemas per agent ────────────────────────────────────────────

HEALTH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["health_score", "issues", "maintenance_actions", "plantation_zones", "confidence", "reasoning"],
    "properties": {
        "health_score":          {"type": "integer", "minimum": 0, "maximum": 100},
        "issues":                {"type": "array", "items": {"type": "string"}},
        "maintenance_actions":   {"type": "array", "items": {"type": "string"}},
        "plantation_zones":      {"type": "array"},
        "confidence":            {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning":             {"type": "string"},
    },
}

INVENTORY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["trees", "count"],
    "properties": {
        "trees": {"type": "array"},
        "count": {"type": "integer"},
    },
}

# ── PII patterns (strip from LLM output) ─────────────────────────────────────
PII_PATTERNS = {
    "aadhaar": r"\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b",
    "phone":   r"\b(?:\+91|0)?[6-9]\d{9}\b",
    "email":   r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,7}\b",
}


def validate_json_schema(data: dict, schema: dict) -> tuple[bool, str]:
    """Validate a dict against a JSON schema."""
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, str(e.message)


# Singleton — load Detoxify model once at first use, never reload per-request
_detoxify_model = None
_detoxify_loaded = False   # True once we've attempted load (even if it failed)


def _get_detoxify():
    global _detoxify_model, _detoxify_loaded
    if not _detoxify_loaded:
        _detoxify_loaded = True
        try:
            from detoxify import Detoxify
            _detoxify_model = Detoxify("original")
        except Exception:
            _detoxify_model = None
    return _detoxify_model


def check_toxicity(text: str) -> tuple[bool, float]:
    """
    Lightweight toxicity check. Uses detoxify singleton if available, else regex fallback.
    Returns (is_toxic: bool, score: float).
    """
    model = _get_detoxify()
    if model is not None:
        try:
            result = model.predict(text)
            score = result.get("toxicity", 0.0)
            return score > 0.6, score
        except Exception:
            pass
    # Regex fallback
    toxic_keywords = r"\b(kill|harm|destroy|attack|violate|abuse)\b"
    if re.search(toxic_keywords, text, re.IGNORECASE):
        return True, 1.0
    return False, 0.0


def strip_pii_from_output(text: str) -> str:
    """Remove any PII that slipped into LLM output."""
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{pii_type.upper()} REDACTED]", text)
    return text


def fact_check_tree_count(llm_text: str, ward: int = None) -> dict:
    """
    If LLM mentions a number of trees, cross-check it against DB.
    Returns {"fact_check_passed": bool, "db_count": int, "llm_claimed": Optional[int]}
    """
    db = SessionLocal()
    try:
        q = db.query(Tree)
        if ward:
            q = q.filter(Tree.ward == ward)
        db_count = q.count()
    finally:
        db.close()

    # Try to extract a number from LLM text like "Ward 5 has 42 trees"
    match = re.search(r'\b(\d+)\s+tree', llm_text, re.IGNORECASE)
    if match:
        claimed = int(match.group(1))
        passed = abs(claimed - db_count) <= max(5, db_count * 0.2)  # 20% tolerance
        return {"fact_check_passed": passed, "db_count": db_count, "llm_claimed": claimed}
    return {"fact_check_passed": True, "db_count": db_count, "llm_claimed": None}


def validate_health_response(response: dict) -> tuple[dict, list]:
    """Full output validation pipeline for health agent responses."""
    warnings = []

    # 1. JSON schema
    valid, err = validate_json_schema(response, HEALTH_RESPONSE_SCHEMA)
    if not valid:
        warnings.append(f"schema_violation: {err}")

    # 2. Toxicity on issues text
    issues_text = " ".join(response.get("issues", []))
    toxic, score = check_toxicity(issues_text)
    if toxic:
        response["issues"] = ["[Content filtered]"]
        warnings.append(f"toxicity_filtered: score={score:.2f}")

    # 3. Strip PII from reasoning
    if "reasoning" in response:
        response["reasoning"] = strip_pii_from_output(response["reasoning"])

    return response, warnings
