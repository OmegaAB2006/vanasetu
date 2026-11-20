"""
run.py — Top-level entry point. Run from smart-urban-tree/ root:
  python run.py
"""
import sys
import os

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import app
from backend.models.db import init_db
from backend.live_data.data_sync import start_scheduler

if __name__ == "__main__":
    init_db()
    start_scheduler()
    app.run(host="0.0.0.0", debug=True, port=5001, use_reloader=False)
