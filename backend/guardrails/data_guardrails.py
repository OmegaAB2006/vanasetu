from __future__ import annotations
from typing import Optional
"""
data_guardrails.py — Guardrail 4: RBAC, data masking, DB access control.
"""
import re
import os
from functools import wraps
from flask import request, jsonify
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
JWT_ALGORITHM = "HS256"

ROLES = {"citizen", "officer", "admin"}


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT and return claims dict, or None if invalid."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def get_current_role(request_obj) -> str:
    """Extract role from Authorization header JWT, default to citizen."""
    auth = request_obj.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        claims = decode_token(token)
        if claims and claims.get("role") in ROLES:
            return claims["role"]
    return "citizen"


def get_current_user_id(request_obj) -> str:
    """Extract user_id from JWT."""
    auth = request_obj.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        claims = decode_token(token)
        if claims:
            return claims.get("sub", "anonymous")
    return "anonymous"


def mask_officer_name(name: str) -> str:
    """Replace officer name with anonymized ID for citizen-facing responses."""
    if not name:
        return "Officer [REDACTED]"
    # Use a stable hash-based ID
    import hashlib
    h = hashlib.md5(name.encode()).hexdigest()[:4].upper()
    return f"Officer #{h}"


def apply_data_masking(tree_dict: dict, user_role: str) -> dict:
    """Apply masking rules based on role (Data Guardrail 4)."""
    if user_role == "citizen":
        # Round GPS to 3 decimal places
        if "latitude" in tree_dict:
            tree_dict["latitude"] = round(float(tree_dict["latitude"]), 3)
        if "longitude" in tree_dict:
            tree_dict["longitude"] = round(float(tree_dict["longitude"]), 3)
        # Remove internal IDs from public view (keep tree id for reference)
    return tree_dict


def require_role(*roles):
    """Route decorator: returns 403 if current user's role is not in allowed roles."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = get_current_role(request)
            if role not in roles:
                return jsonify({
                    "status": "forbidden",
                    "reason": f"role '{role}' is not allowed for this action",
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def citizen_cannot_access_officer_data(response_data: dict) -> dict:
    """Strip officer-specific fields from citizen-visible responses."""
    sensitive_fields = {"officer_name", "approved_by", "officer_id"}
    if isinstance(response_data, dict):
        for field in sensitive_fields:
            if field in response_data:
                response_data[field] = "[REDACTED]"
    return response_data
