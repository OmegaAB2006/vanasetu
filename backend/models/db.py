from __future__ import annotations
from typing import Optional
"""
db.py — Database connection and SQLAlchemy ORM setup.
Supports MySQL (production) and SQLite (local dev — zero config).

Set DATABASE_URL in .env to override. If not set, defaults to SQLite at smart_urban_tree.db.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, Numeric, JSON, Text
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# If DATABASE_URL is set directly, use it (supports MySQL, PostgreSQL, SQLite).
# Otherwise, check for individual MySQL env vars. Fall back to SQLite.
_explicit_url = os.getenv("DATABASE_URL", "")
if _explicit_url:
    DATABASE_URL = _explicit_url
else:
    DB_HOST     = os.getenv("DB_HOST", "")
    DB_PORT     = os.getenv("DB_PORT", "3306")
    DB_NAME     = os.getenv("DB_NAME", "smart_urban_tree")
    DB_USER     = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    if DB_HOST and DB_USER:
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # SQLite fallback — stored next to run.py
        _db_path = os.path.join(os.path.dirname(__file__), "..", "..", "smart_urban_tree.db")
        DATABASE_URL = f"sqlite:///{os.path.abspath(_db_path)}"

_is_sqlite = DATABASE_URL.startswith("sqlite")
_engine_kwargs = {} if _is_sqlite else {"pool_pre_ping": True, "pool_recycle": 3600}
# SQLite requires check_same_thread=False in a multi-threaded Flask context
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency — yields a DB session, closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── ORM Models ────────────────────────────────────────────────────────────────

class Tree(Base):
    __tablename__ = "trees"
    id          = Column(Integer, primary_key=True, index=True)
    species     = Column(String(100), nullable=False)
    latitude    = Column(Numeric(9, 6), nullable=False)
    longitude   = Column(Numeric(9, 6), nullable=False)
    ward        = Column(Integer, nullable=False)
    age_years   = Column(Integer, default=0)
    health_score= Column(Integer, default=100)
    last_checked= Column(Date, nullable=True)
    status      = Column(Enum("healthy","stressed","diseased","critical","removed"), default="healthy")
    created_at  = Column(DateTime, default=datetime.utcnow)


class MaintenanceLog(Base):
    __tablename__ = "maintenance_log"
    id           = Column(Integer, primary_key=True, index=True)
    tree_id      = Column(Integer, nullable=False)
    action       = Column(String(255), nullable=False)
    date         = Column(Date, nullable=False)
    officer_name = Column(String(100))
    notes        = Column(Text)
    approved_by  = Column(String(100))
    created_at   = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(String(100))
    action     = Column(String(100), nullable=False)
    table_name = Column(String(100))
    record_id  = Column(Integer)
    old_val    = Column(JSON)
    new_val    = Column(JSON)
    timestamp  = Column(DateTime, default=datetime.utcnow)


class LiveWeather(Base):
    __tablename__ = "live_weather"
    id             = Column(Integer, primary_key=True, index=True)
    city           = Column(String(100), default="Bengaluru")
    temperature    = Column(Numeric(5, 2))
    rainfall       = Column(Numeric(6, 2))
    humidity       = Column(Integer)
    wind_speed     = Column(Numeric(5, 2))
    condition_text = Column(String(100))
    fetched_at     = Column(DateTime, default=datetime.utcnow)


class WardNDVI(Base):
    __tablename__ = "ward_ndvi"
    id            = Column(Integer, primary_key=True, index=True)
    ward_id       = Column(Integer, nullable=False)
    ndvi_value    = Column(Numeric(5, 4))
    source        = Column(String(50), default="MODIS")
    recorded_date = Column(Date)
    fetched_at    = Column(DateTime, default=datetime.utcnow)


class OSMGreenSpaces(Base):
    __tablename__ = "osm_green_spaces"
    id              = Column(Integer, primary_key=True, index=True)
    ward_id         = Column(Integer, nullable=False)
    green_area_sqm  = Column(Numeric(14, 2))
    total_area_sqm  = Column(Numeric(14, 2))
    fetched_at      = Column(DateTime, default=datetime.utcnow)


class WardGreenCover(Base):
    __tablename__ = "ward_green_cover"
    id              = Column(Integer, primary_key=True, index=True)
    ward_id         = Column(Integer, nullable=False, unique=True)
    green_cover_pct = Column(Numeric(5, 2))
    ndvi_normalized = Column(Numeric(5, 4))
    osm_ratio       = Column(Numeric(5, 4))
    rainfall_bonus  = Column(Numeric(5, 4))
    calculated_at   = Column(DateTime, default=datetime.utcnow)


class APIUsageLog(Base):
    __tablename__ = "api_usage_log"
    id         = Column(Integer, primary_key=True, index=True)
    agent_id   = Column(String(50))
    endpoint   = Column(String(200))
    tokens_in  = Column(Integer)
    tokens_out = Column(Integer)
    latency_ms = Column(Integer)
    timestamp  = Column(DateTime, default=datetime.utcnow)


class AgentCommLog(Base):
    __tablename__ = "agent_comm_log"
    id           = Column(Integer, primary_key=True, index=True)
    request_id   = Column(String(36))
    source_agent = Column(String(50))
    dest_agent   = Column(String(50))
    payload_hash = Column(String(64))
    timestamp    = Column(DateTime, default=datetime.utcnow)


class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    id          = Column(String(36), primary_key=True)
    action_type = Column(String(100))
    payload     = Column(JSON)
    status      = Column(Enum("pending","approved","rejected"), default="pending")
    created_at  = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)


def init_db():
    """Create all tables (safe to call on startup)."""
    Base.metadata.create_all(bind=engine)


def write_audit(db, user_id: str, action: str, table_name: str,
                record_id: Optional[int] = None, old_val: Optional[dict] = None, new_val: Optional[dict] = None):
    """Helper — append a row to audit_log (never updates existing rows)."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_val=old_val,
        new_val=new_val,
    )
    db.add(entry)
    db.commit()
