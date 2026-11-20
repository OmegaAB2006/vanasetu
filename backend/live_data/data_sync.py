"""
data_sync.py — APScheduler: triggers all live data fetchers on schedule.
  - weather_fetcher: every 30 minutes
  - osm_fetcher: every 24 hours
  - ndvi_fetcher: every 16 days (MODIS revisit cycle)
  - mapping_agent.recalculate_all_wards: every 30 minutes (after weather fetch)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

_scheduler = None


def _run_weather():
    from backend.live_data.weather_fetcher import fetch_weather
    fetch_weather()
    # Recalculate composite green cover after each weather update
    from backend.agents.mapping_agent import recalculate_all_wards
    recalculate_all_wards()


def _run_osm():
    from backend.live_data.osm_fetcher import fetch_osm_green_spaces
    fetch_osm_green_spaces()


def _run_ndvi():
    from backend.live_data.ndvi_fetcher import fetch_ndvi_for_wards
    fetch_ndvi_for_wards()


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()

    # Seed on startup immediately
    _run_ndvi()
    _run_osm()
    _run_weather()

    # Schedule recurring jobs
    _scheduler.add_job(
        _run_weather,
        trigger=IntervalTrigger(minutes=30),
        id="weather_sync",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_osm,
        trigger=IntervalTrigger(hours=24),
        id="osm_sync",
        replace_existing=True,
    )
    _scheduler.add_job(
        _run_ndvi,
        trigger=IntervalTrigger(days=16),
        id="ndvi_sync",
        replace_existing=True,
    )

    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    print("[data_sync] Scheduler started: weather(30m), OSM(24h), NDVI(16d)")
