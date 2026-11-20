from __future__ import annotations
from typing import Optional
"""
weather_fetcher.py — Live weather from OpenWeatherMap API.
Runs every 30 minutes via APScheduler.
"""
import os
import requests
from datetime import datetime
from backend.models.db import SessionLocal, LiveWeather
from backend.guardrails.operational_guardrails import with_retry

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


@with_retry
def fetch_weather(city: str = "Bengaluru") -> Optional[dict]:
    """Fetch current weather from OpenWeatherMap and upsert to live_weather table."""
    if not OPENWEATHERMAP_API_KEY:
        return _mock_weather()

    params = {"q": city, "appid": OPENWEATHERMAP_API_KEY, "units": "metric"}
    resp = requests.get(OWM_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    weather = {
        "city": city,
        "temperature": data["main"]["temp"],
        "rainfall": data.get("rain", {}).get("1h", 0.0),
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "condition_text": data["weather"][0]["description"] if data.get("weather") else "unknown",
    }

    _upsert_weather(weather)
    return weather


def _upsert_weather(weather: dict):
    db = SessionLocal()
    try:
        db.add(LiveWeather(
            city=weather["city"],
            temperature=weather["temperature"],
            rainfall=weather["rainfall"],
            humidity=weather["humidity"],
            wind_speed=weather["wind_speed"],
            condition_text=weather["condition_text"],
            fetched_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _mock_weather() -> dict:
    """Return realistic mock data when no API key is configured."""
    mock = {
        "city": "Bengaluru",
        "temperature": 27.5,
        "rainfall": 0.0,
        "humidity": 72,
        "wind_speed": 3.2,
        "condition_text": "partly cloudy",
    }
    _upsert_weather(mock)
    return mock


def get_latest_weather() -> Optional[dict]:
    """Read latest weather row from DB."""
    db = SessionLocal()
    try:
        row = db.query(LiveWeather).order_by(LiveWeather.fetched_at.desc()).first()
        if row:
            return {
                "city": row.city,
                "temperature": float(row.temperature or 0),
                "rainfall": float(row.rainfall or 0),
                "humidity": row.humidity,
                "wind_speed": float(row.wind_speed or 0),
                "condition_text": row.condition_text,
                "fetched_at": row.fetched_at.isoformat(),
            }
        return _mock_weather()
    finally:
        db.close()
