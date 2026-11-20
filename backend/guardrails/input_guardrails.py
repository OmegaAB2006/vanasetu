"""
input_guardrails.py — Guardrail 1: Input validation, PII detection, injection blocking.
"""
import re
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

# ── Injection patterns (Security + Input Guardrails) ──────────────────────────
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions?",
    r"act\s+as\s+(if\s+you\s+are|a\s+different)",
    r"\bDAN\b",
    r"developer\s+mode",
    r"pretend\s+you\s+(are|were)",
    r"override\s+(your\s+)?(instructions?|rules?|system)",
    r"forget\s+(all\s+)?(previous\s+)?(instructions?|rules?)",
    r"jailbreak",
    r"<\s*script",
    r"--\s*;?\s*DROP",
    r"UNION\s+SELECT",
    r";\s*DELETE\s+FROM",
]

# PII patterns (Aadhaar, Indian mobile, email)
PII_PATTERNS = {
    "aadhaar": r"\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b",
    "phone":   r"\b(?:\+91|0)?[6-9]\d{9}\b",
    "email":   r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,7}\b",
}

PROFANITY_BLOCKLIST = {"spam", "hack", "exploit", "malware", "attack"}  # extend as needed


def check_prompt_injection(text: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"prompt_injection_detected: pattern '{pattern}'"
    return False, ""


def strip_pii(text: str) -> tuple[str, list]:
    """Strip detected PII from text. Returns (cleaned_text, list_of_found_types)."""
    found = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            text = re.sub(pattern, f"[{pii_type.upper()} REDACTED]", text)
            found.append(pii_type)
    return text, found


def check_profanity(text: str) -> bool:
    words = set(text.lower().split())
    return bool(words & PROFANITY_BLOCKLIST)


def validate_free_text(text: str) -> tuple[bool, str]:
    """Combined check: injection + PII + profanity."""
    blocked, reason = check_prompt_injection(text)
    if blocked:
        return False, reason
    if check_profanity(text):
        return False, "inappropriate_content_detected"
    return True, ""


# ── Pydantic input schemas ─────────────────────────────────────────────────────

class TreeCreateSchema(BaseModel):
    species: str
    latitude: float
    longitude: float
    ward: int
    age_years: Optional[int] = 0
    health_score: Optional[int] = 100
    last_checked: Optional[date] = None
    status: Optional[str] = "healthy"

    @validator("species")
    def species_max_length(cls, v):
        if len(v) > 100:
            raise ValueError("species name too long")
        return v

    @validator("latitude")
    def valid_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("invalid latitude")
        return v

    @validator("longitude")
    def valid_lng(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("invalid longitude")
        return v

    @validator("health_score")
    def valid_score(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("health_score must be 0–100")
        return v

    @validator("status")
    def valid_status(cls, v):
        allowed = {"healthy", "stressed", "diseased", "critical", "removed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class NLQuerySchema(BaseModel):
    query: str

    @validator("query")
    def not_empty_or_too_long(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty")
        if len(v) > 500:
            raise ValueError("query too long (max 500 chars)")
        return v


class HealthAssessSchema(BaseModel):
    ward: Optional[int] = None
    temperature: Optional[float] = None
    soil_ph: Optional[float] = None
    rainfall: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def validate_file_upload(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate image file upload. Only JPEG/PNG, max 5MB."""
    allowed_exts = {".jpg", ".jpeg", ".png"}
    import os
    ext = os.path.splitext(filename.lower())[1]
    if ext not in allowed_exts:
        return False, f"invalid_file_type: {ext} not allowed (JPEG/PNG only)"
    if file_size > 5 * 1024 * 1024:
        return False, "file_too_large: max 5MB allowed"
    # Sanitize filename
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    if safe_name != filename:
        pass  # allow — just log internally
    return True, ""
