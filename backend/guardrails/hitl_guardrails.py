"""
hitl_guardrails.py — Guardrail 7: Human-in-the-Loop approval workflows.
"""
import uuid
from datetime import datetime
from backend.models.db import SessionLocal, PendingApproval, write_audit

CRITICAL_HEALTH_THRESHOLD = 20  # health_score below this triggers HITL hold


def requires_hitl(action_type: str, payload: dict) -> bool:
    """Determine if an action requires human approval."""
    triggers = {
        "delete_tree",
        "bulk_plantation_recommend",
        "critical_removal_flag",
        "send_maintenance_alert",
        "modify_maintenance_log",
    }
    if action_type in triggers:
        return True
    # Health score critically low → hold before writing removal flag
    if action_type == "health_assessment":
        score = payload.get("health_score", 100)
        if score < CRITICAL_HEALTH_THRESHOLD:
            return True
    return False


def hold_for_approval(action_type: str, payload: dict) -> dict:
    """
    Save a pending action to the pending_approvals table.
    Returns a response with status='pending_approval' and the action_id.
    """
    action_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(PendingApproval(
            id=action_id,
            action_type=action_type,
            payload=payload,
            status="pending",
        ))
        db.commit()
    finally:
        db.close()

    return {
        "status": "pending_approval",
        "action_id": action_id,
        "message": (
            f"Action '{action_type}' requires human approval. "
            f"An officer must approve action_id={action_id} before it proceeds."
        ),
    }


def approve_action(action_id: str, approver_user_id: str) -> dict:
    """Mark a pending action as approved and return the original payload for execution."""
    db = SessionLocal()
    try:
        record = db.query(PendingApproval).filter(PendingApproval.id == action_id).first()
        if not record:
            return {"status": "error", "message": "action_id not found"}
        if record.status != "pending":
            return {"status": "error", "message": f"action already {record.status}"}
        record.status = "approved"
        record.resolved_at = datetime.utcnow()
        record.resolved_by = approver_user_id
        db.commit()
        payload = record.payload
        write_audit(db, approver_user_id, "APPROVE", "pending_approvals",
                    None, None, {"action_id": action_id, "action_type": record.action_type})
        return {"status": "approved", "payload": payload}
    finally:
        db.close()


def reject_action(action_id: str, rejector_user_id: str) -> dict:
    """Mark a pending action as rejected."""
    db = SessionLocal()
    try:
        record = db.query(PendingApproval).filter(PendingApproval.id == action_id).first()
        if not record:
            return {"status": "error", "message": "action_id not found"}
        record.status = "rejected"
        record.resolved_at = datetime.utcnow()
        record.resolved_by = rejector_user_id
        db.commit()
        write_audit(db, rejector_user_id, "REJECT", "pending_approvals",
                    None, None, {"action_id": action_id})
        return {"status": "rejected", "message": "Action has been rejected."}
    finally:
        db.close()


def list_pending_approvals() -> list:
    db = SessionLocal()
    try:
        rows = db.query(PendingApproval).filter(PendingApproval.status == "pending").all()
        return [
            {
                "id": r.id,
                "action_type": r.action_type,
                "payload": r.payload,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    finally:
        db.close()
