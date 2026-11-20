"""
ethics_guardrails.py — Guardrail 9: Bias detection, fairness, explainability, audit trails.
"""
from backend.models.db import SessionLocal, WardGreenCover, write_audit

TOTAL_BENGALURU_WARDS = 198
BIAS_SKIP_THRESHOLD = 0.30  # warn if >30% of wards are skipped in recommendations


def check_plantation_recommendation_bias(recommended_ward_ids: list) -> dict:
    """
    Ensure plantation recommendations don't systematically exclude wards.
    Returns warning if more than 30% of all wards are skipped.
    """
    if not recommended_ward_ids:
        return {"bias_check_passed": True, "note": "no recommendations to check"}
    unique_wards = set(recommended_ward_ids)
    coverage = len(unique_wards) / TOTAL_BENGALURU_WARDS
    skipped_ratio = 1 - coverage
    passed = skipped_ratio <= BIAS_SKIP_THRESHOLD
    return {
        "bias_check_passed": passed,
        "wards_recommended": len(unique_wards),
        "skipped_ratio": round(skipped_ratio, 3),
        "warning": (
            None if passed
            else f"Recommendation coverage too low: only {len(unique_wards)} of "
                 f"{TOTAL_BENGALURU_WARDS} wards included. Possible geographic bias."
        ),
    }


def ensure_reasoning_field(response: dict) -> tuple[dict, bool]:
    """
    Explainability guardrail: every LLM response must include a 'reasoning' field.
    If missing, flag and add a placeholder.
    """
    if "reasoning" not in response or not response["reasoning"]:
        response["reasoning"] = "Reasoning not provided by LLM — manual review recommended."
        return response, False
    return response, True


def check_maintenance_priority_fairness(trees: list) -> dict:
    """
    Ensure maintenance priorities are based only on health_score (objective),
    not on ward number or location patterns.
    """
    if not trees:
        return {"fairness_check_passed": True}
    ward_counts = {}
    for tree in trees:
        w = tree.get("ward", 0)
        ward_counts[w] = ward_counts.get(w, 0) + 1
    total = len(trees)
    max_concentration = max(ward_counts.values()) / total if ward_counts else 0
    passed = max_concentration < 0.5  # no single ward should dominate >50%
    return {
        "fairness_check_passed": passed,
        "ward_distribution": ward_counts,
        "max_single_ward_ratio": round(max_concentration, 3),
        "warning": (
            None if passed
            else "Maintenance priority list heavily concentrated in one ward — verify scoring logic."
        ),
    }


def audit_ai_decision(db, user_id: str, agent_id: str,
                      input_summary: str, output_summary: str):
    """Write every AI decision to the immutable audit log."""
    write_audit(
        db,
        user_id=user_id,
        action=f"AI_DECISION:{agent_id}",
        table_name="ai_decisions",
        record_id=None,
        old_val=None,
        new_val={"input": input_summary[:500], "output": output_summary[:500]},
    )
