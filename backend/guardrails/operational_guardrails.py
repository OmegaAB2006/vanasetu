"""
operational_guardrails.py — Guardrail 6: Token limits, rate limiting, retries, timeouts.
"""
import time
import functools
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.models.db import SessionLocal, APIUsageLog
from datetime import datetime

MAX_TOKENS = {
    "health_agent":     512,
    "inventory_agent":  256,
    "mapping_agent":    256,
    "dashboard_agent":  512,
}
MAX_EXECUTION_SECONDS = 10
MAX_RETRIES = 3


def timeout(seconds: int = MAX_EXECUTION_SECONDS):
    """Decorator: raises TimeoutError if function takes too long."""
    import signal

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _handler(signum, frame):
                raise TimeoutError(f"Agent call exceeded {seconds}s limit")
            old = signal.signal(signal.SIGALRM, _handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        return wrapper
    return decorator


def with_retry(func):
    """Exponential backoff retry wrapper (max 3 attempts) for external API calls."""
    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=False,
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def log_api_usage(agent_id: str, endpoint: str,
                  tokens_in: int, tokens_out: int, latency_ms: int):
    """Write token usage to api_usage_log for cost monitoring."""
    db = SessionLocal()
    try:
        db.add(APIUsageLog(
            agent_id=agent_id,
            endpoint=endpoint,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def get_max_tokens(agent_id: str) -> int:
    return MAX_TOKENS.get(agent_id, 256)
