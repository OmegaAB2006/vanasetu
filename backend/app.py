"""
app.py — Flask entry point for Smart Urban Tree Platform
"""
import os
import uuid
from flask import Flask, g, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

from backend.models.db import init_db
from backend.routes.agent_routes import agent_bp
from backend.routes.data_routes import data_bp
from backend.live_data.data_sync import start_scheduler

# Serve static frontend files from the frontend/ directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# CORS — allow frontend on any origin during dev
CORS(app)

# Rate limiting — Operational Guardrail 6
# API endpoints: 60/min. Chatbot (/api/assistant) is exempt — it handles its
# own lightweight logic and must never block mid-conversation.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "60 per minute"],
    storage_uri="memory://",
)

# Inject a unique request_id on every request (Multi-Agent Guardrail 8)
@app.before_request
def inject_request_id():
    g.request_id = str(uuid.uuid4())
    g.loop_counter = {}  # tracks agent call counts per request_id

# Register blueprints
app.register_blueprint(agent_bp, url_prefix="/api")
app.register_blueprint(data_bp, url_prefix="/api/data")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "landing.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/health")
def health():
    return {"status": "ok", "service": "Smart Urban Tree Platform"}, 200


if __name__ == "__main__":
    init_db()
    start_scheduler()
    app.run(host="0.0.0.0", debug=os.getenv("FLASK_DEBUG", "1") == "1", port=5000)
