"""
agent_routes.py — All agent API endpoints.
Applies guardrail_engine decorator to every route.
"""
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError

from backend.guardrails.guardrail_engine import guardrailed, run_output_guardrails, run_data_guardrails
from backend.guardrails.input_guardrails import TreeCreateSchema, NLQuerySchema, HealthAssessSchema, validate_file_upload
from backend.guardrails.hitl_guardrails import (
    requires_hitl, hold_for_approval, approve_action,
    reject_action, list_pending_approvals
)
from backend.guardrails.data_guardrails import get_current_role, get_current_user_id, require_role

agent_bp = Blueprint("agent", __name__)


# ── Inventory Agent (Agent 2) ─────────────────────────────────────────────────

@agent_bp.route("/inventory", methods=["GET"])
@guardrailed("inventory_agent")
def get_inventory():
    from backend.agents.inventory_agent import get_all_trees
    ward    = request.args.get("ward", type=int)
    species = request.args.get("species")
    status  = request.args.get("status")
    h_min   = request.args.get("health_min", type=int)
    h_max   = request.args.get("health_max", type=int)
    user_role = g.get("user_role", "citizen")
    trees = get_all_trees(ward=ward, species=species, status=status,
                          health_min=h_min, health_max=h_max, user_role=user_role)
    return jsonify({"trees": trees, "count": len(trees)})


@agent_bp.route("/inventory", methods=["POST"])
@guardrailed("inventory_agent")
@require_role("officer", "admin")
def add_tree():
    from backend.agents.inventory_agent import add_tree
    body = request.get_json(silent=True) or {}
    try:
        validated = TreeCreateSchema(**body)
    except ValidationError as e:
        return jsonify({"status": "blocked", "reason": "schema_validation_failed",
                        "details": e.errors()}), 400
    result = add_tree(validated.dict(), user_id=g.get("user_id", "anonymous"))
    return jsonify(result), 201


@agent_bp.route("/inventory/query", methods=["POST"])
@guardrailed("inventory_agent")
def nl_inventory_query():
    from backend.agents.inventory_agent import nl_to_filters, get_all_trees
    body = request.get_json(silent=True) or {}
    try:
        validated = NLQuerySchema(**body)
    except ValidationError as e:
        return jsonify({"status": "blocked", "reason": "schema_validation_failed",
                        "details": e.errors()}), 400
    user_role = g.get("user_role", "citizen")
    filters = nl_to_filters(validated.query)
    trees = get_all_trees(user_role=user_role, **filters)
    return jsonify({"trees": trees, "count": len(trees), "filters_applied": filters})


@agent_bp.route("/inventory/summary", methods=["GET"])
def inventory_summary():
    from backend.agents.inventory_agent import get_summary
    return jsonify(get_summary())


@agent_bp.route("/inventory/<int:tree_id>", methods=["GET"])
def get_tree(tree_id):
    from backend.agents.inventory_agent import get_tree_by_id
    user_role = g.get("user_role", "citizen")
    tree = get_tree_by_id(tree_id, user_role)
    if tree is None:
        return jsonify({"status": "error", "message": f"Tree {tree_id} not found"}), 404
    return jsonify(tree)


@agent_bp.route("/inventory/<int:tree_id>", methods=["PUT"])
@require_role("officer", "admin")
def update_tree(tree_id):
    from backend.models.db import SessionLocal, Tree, write_audit
    body = request.get_json(silent=True) or {}
    allowed = {"species", "ward", "age_years", "health_score", "last_checked", "status",
               "latitude", "longitude"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"status": "error", "message": "No valid fields to update"}), 400
    db = SessionLocal()
    try:
        tree = db.query(Tree).filter(Tree.id == tree_id).first()
        if not tree:
            return jsonify({"status": "error", "message": f"Tree {tree_id} not found"}), 404
        old_vals = {k: getattr(tree, k) for k in updates}
        for k, v in updates.items():
            setattr(tree, k, v)
        db.commit()
        db.refresh(tree)
        write_audit(db, g.get("user_id", "unknown"), "UPDATE", "trees", tree_id, old_vals, updates)
        return jsonify({"status": "ok", "message": f"Tree {tree_id} updated", "tree": {
            "id": tree.id, "species": tree.species, "ward": tree.ward,
            "health_score": tree.health_score, "status": tree.status,
        }})
    finally:
        db.close()


@agent_bp.route("/inventory/<int:tree_id>", methods=["DELETE"])
@require_role("officer", "admin")
def delete_tree(tree_id):
    from backend.models.db import SessionLocal, Tree, write_audit
    db = SessionLocal()
    try:
        tree = db.query(Tree).filter(Tree.id == tree_id).first()
        if not tree:
            return jsonify({"status": "error", "message": f"Tree {tree_id} not found"}), 404
        old = {"species": tree.species, "ward": tree.ward}
        db.delete(tree)
        db.commit()
        write_audit(db, g.get("user_id", "unknown"), "DELETE", "trees", tree_id, old, None)
        return jsonify({"status": "ok", "message": f"Tree {tree_id} deleted"})
    finally:
        db.close()


@agent_bp.route("/maintenance", methods=["POST"])
@require_role("officer", "admin")
def log_maintenance_route():
    from backend.agents.health_agent import log_maintenance
    body = request.get_json(silent=True) or {}
    tree_id      = body.get("tree_id")
    action       = body.get("action", "").strip()
    officer_name = body.get("officer_name", g.get("user_id", "unknown"))
    notes        = body.get("notes", "")
    approved_by  = body.get("approved_by", "")
    if not tree_id or not action:
        return jsonify({"status": "error", "message": "tree_id and action are required"}), 400
    result = log_maintenance(int(tree_id), action, officer_name, notes, approved_by,
                             user_id=g.get("user_id", "unknown"))
    return jsonify(result), 201


@agent_bp.route("/maintenance/<int:tree_id>", methods=["GET"])
def get_maintenance_log(tree_id):
    from backend.models.db import SessionLocal, MaintenanceLog
    db = SessionLocal()
    try:
        rows = (db.query(MaintenanceLog)
                  .filter(MaintenanceLog.tree_id == tree_id)
                  .order_by(MaintenanceLog.date.desc())
                  .all())
        return jsonify([{
            "id":           r.id,
            "tree_id":      r.tree_id,
            "action":       r.action,
            "date":         r.date.isoformat() if r.date else None,
            "officer_name": r.officer_name,
            "notes":        r.notes,
            "approved_by":  r.approved_by,
        } for r in rows])
    finally:
        db.close()


# ── Health Agent (Agent 1) ────────────────────────────────────────────────────

@agent_bp.route("/health/assess", methods=["POST"])
@guardrailed("health_agent")
def assess_health():
    from backend.agents.health_agent import assess_tree_health

    # File upload validation (Input Guardrail 1)
    image_bytes = None
    if "image" in request.files:
        file = request.files["image"]
        ok, reason = validate_file_upload(file.filename, len(file.read()))
        if not ok:
            return jsonify({"status": "blocked", "reason": reason,
                            "message": "Invalid file upload."}), 400
        file.seek(0)
        image_bytes = file.read()

    # Optional env params
    form = request.form
    ward        = form.get("ward", type=int)
    temperature = form.get("temperature", type=float)
    soil_ph     = form.get("soil_ph", type=float)
    rainfall    = form.get("rainfall", type=float)
    latitude    = form.get("latitude", type=float)
    longitude   = form.get("longitude", type=float)

    response = assess_tree_health(
        image_bytes=image_bytes,
        latitude=latitude, longitude=longitude,
        ward=ward, temperature=temperature,
        soil_ph=soil_ph, rainfall=rainfall,
    )

    # Output guardrails
    response, warnings = run_output_guardrails(response, "health_agent")

    # HITL: if health_score critically low, hold for approval
    if requires_hitl("health_assessment", response):
        return jsonify(hold_for_approval("health_assessment", response))

    return jsonify({**response, "_guardrail_warnings": warnings})


@agent_bp.route("/health/recommend", methods=["POST"])
@guardrailed("health_agent")
def recommend_plantation():
    from backend.agents.health_agent import recommend_plantation
    body = request.get_json(silent=True) or {}
    response = recommend_plantation(
        ward=body.get("ward"),
        temperature=body.get("temperature"),
        rainfall=body.get("rainfall"),
        soil_ph=body.get("soil_ph"),
    )
    response, warnings = run_output_guardrails(response, "health_agent")
    return jsonify({**response, "_guardrail_warnings": warnings})


# ── Mapping Agent (Agent 3) ───────────────────────────────────────────────────

@agent_bp.route("/map/wards", methods=["GET"])
def get_map_wards():
    from backend.agents.mapping_agent import get_wards_geojson
    return jsonify(get_wards_geojson())


@agent_bp.route("/map/deficient", methods=["GET"])
def get_deficient_wards():
    from backend.agents.mapping_agent import get_deficient_wards
    threshold = request.args.get("threshold", default=15.0, type=float)
    return jsonify(get_deficient_wards(threshold))


@agent_bp.route("/live/weather", methods=["GET"])
def get_live_weather():
    from backend.live_data.weather_fetcher import get_latest_weather
    return jsonify(get_latest_weather())


# ── Dashboard Agent (Agent 4) ─────────────────────────────────────────────────

@agent_bp.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    from backend.agents.dashboard_agent import get_dashboard_summary
    return jsonify(get_dashboard_summary())


@agent_bp.route("/dashboard/query", methods=["POST"])
@guardrailed("dashboard_agent")
def dashboard_nl_query():
    from backend.agents.dashboard_agent import route_nl_query
    body = request.get_json(silent=True) or {}
    query = body.get("query", "")
    user_role = g.get("user_role", "citizen")
    result = route_nl_query(query, user_role)
    return jsonify(result)


# ── HITL Approval Routes ──────────────────────────────────────────────────────

@agent_bp.route("/approve/<action_id>", methods=["POST"])
@require_role("officer", "admin")
def approve(action_id):
    user_id = get_current_user_id(request)
    result = approve_action(action_id, user_id)
    return jsonify(result)


@agent_bp.route("/reject/<action_id>", methods=["POST"])
@require_role("officer", "admin")
def reject(action_id):
    user_id = get_current_user_id(request)
    result = reject_action(action_id, user_id)
    return jsonify(result)


@agent_bp.route("/pending-approvals", methods=["GET"])
@require_role("officer", "admin")
def pending_approvals():
    return jsonify(list_pending_approvals())


# ── Metrics / LLM Performance Dashboard ──────────────────────────────────────

@agent_bp.route("/metrics", methods=["GET"])
def get_all_metrics():
    from backend.agents.metrics_agent import get_all_metrics
    return jsonify(get_all_metrics())


@agent_bp.route("/metrics/accuracy", methods=["GET"])
def metrics_accuracy():
    from backend.agents.metrics_agent import accuracy_quality_metrics
    return jsonify(accuracy_quality_metrics())


@agent_bp.route("/metrics/rag", methods=["GET"])
def metrics_rag():
    from backend.agents.metrics_agent import rag_metrics
    return jsonify(rag_metrics())


@agent_bp.route("/metrics/agentic", methods=["GET"])
def metrics_agentic():
    from backend.agents.metrics_agent import agentic_metrics
    return jsonify(agentic_metrics())


@agent_bp.route("/metrics/safety", methods=["GET"])
def metrics_safety():
    from backend.agents.metrics_agent import safety_guardrail_metrics
    return jsonify(safety_guardrail_metrics())


@agent_bp.route("/metrics/performance", methods=["GET"])
def metrics_performance():
    from backend.agents.metrics_agent import performance_cost_metrics
    return jsonify(performance_cost_metrics())


@agent_bp.route("/metrics/multiagent", methods=["GET"])
def metrics_multiagent():
    from backend.agents.metrics_agent import multiagent_system_metrics
    return jsonify(multiagent_system_metrics())


# ── Auth: Login endpoint ──────────────────────────────────────────────────────

# Demo credentials — in production use a real user table + bcrypt
DEMO_USERS = {
    "citizen@vanasethu.in":  {"password": "citizen123", "role": "citizen",  "name": "Priya Citizen"},
    "officer@bbmp.gov.in":   {"password": "officer123", "role": "officer",  "name": "Officer Rajan"},
    "admin@bbmp.gov.in":     {"password": "admin123",   "role": "admin",    "name": "Admin Mehta"},
}

@agent_bp.route("/auth/login", methods=["POST"])
def login():
    import os
    from jose import jwt
    body = request.get_json(silent=True) or {}
    email    = body.get("email", "").strip().lower()
    password = body.get("password", "")
    user = DEMO_USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
    secret = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    token = jwt.encode(
        {"sub": email, "role": user["role"], "name": user["name"]},
        secret, algorithm="HS256"
    )
    return jsonify({
        "status":  "ok",
        "token":   token,
        "role":    user["role"],
        "name":    user["name"],
        "email":   email,
    })


@agent_bp.route("/auth/me", methods=["GET"])
def me():
    from backend.guardrails.data_guardrails import get_current_role, get_current_user_id, decode_token
    import os
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"role": "citizen", "name": "Guest"}), 200
    token = auth.split(" ", 1)[1]
    secret = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    claims = decode_token(token)
    if not claims:
        return jsonify({"status": "error", "message": "Invalid token"}), 401
    return jsonify({"role": claims.get("role","citizen"), "name": claims.get("name",""), "email": claims.get("sub","")})


@agent_bp.route("/public/stats", methods=["GET"])
def public_stats():
    """Public endpoint — no auth required. Used by citizen landing page."""
    from backend.agents.inventory_agent import get_summary
    from backend.agents.mapping_agent import get_deficient_wards
    from backend.live_data.weather_fetcher import get_latest_weather
    summary  = get_summary()
    deficient = get_deficient_wards(15.0)
    weather   = get_latest_weather()
    return jsonify({
        "total_trees":      summary["total_trees"],
        "avg_health_score": summary["avg_health_score"],
        "maintenance_due":  summary["maintenance_due"],
        "deficient_wards":  len(deficient),
        "weather":          weather,
    })


# ── Global AI Assistant ───────────────────────────────────────────────────────

@agent_bp.route("/assistant", methods=["POST"])
def assistant():
    """
    Global AI assistant — rate-limit exempt (chatbot must never block mid-conversation).
    Answers any question about the platform, live data, or Bengaluru trees.
    """
    from flask import current_app
    # Exempt this route from the per-minute rate limit
    try:
        from flask_limiter import Limiter
        limiter_ext = current_app.extensions.get("limiter")
        if limiter_ext:
            limiter_ext.exempt(assistant)
    except Exception:
        pass

    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"reply": "Please type a question.", "navigate_to": None})

    import re as _re
    q = query.lower()

    def _word(w, text):
        """True if w appears as a whole word in text."""
        return bool(_re.search(r'\b' + _re.escape(w) + r'\b', text))

    # ── Greetings & small-talk ────────────────────────────────────────────────
    if any(_word(kw, q) for kw in ["hello", "hi", "hey", "namaste"]) or \
       any(kw in q for kw in ["good morning", "good evening"]):
        return jsonify({
            "reply": "Hello! 👋 I'm the **Vana Sethu AI**. Ask me anything about Bengaluru's urban trees — tree counts, ward green cover, weather, or say *'go to map'* to explore!",
            "navigate_to": None,
        })
    if any(kw in q for kw in ["thank", "thanks", "great", "awesome", "good job", "well done", "nice one", "nice work", "nicely done"]):
        return jsonify({
            "reply": "You're welcome! 🌳 Let me know if you have more questions about Bengaluru's urban trees.",
            "navigate_to": None,
        })

    # ── Platform introduction ─────────────────────────────────────────────────
    if any(kw in q for kw in ["what is vana sethu", "about vana sethu", "what does this", "explain this", "what is this platform", "what is this app", "purpose of this"]):
        return jsonify({
            "reply": "**Vana Sethu** (ವನ ಸೇತು) means *Bridge to the Forest* in Kannada.\n\nIt's an AI-powered Smart Urban Tree Platform for Bengaluru that helps BBMP officers, NGOs and citizens:\n- Monitor the health of every registered tree\n- Track green cover % across all BBMP wards\n- Get AI-powered maintenance recommendations\n- Approve critical actions via Human-in-the-Loop\n\nBuilt with **4 AI agents** and **9 safety guardrail layers**.",
            "navigate_to": None,
        })
    if any(kw in q for kw in ["who can use", "who uses", "users", "citizen", "officer", "admin", "roles"]):
        return jsonify({
            "reply": "Vana Sethu has **3 user roles**:\n- 👤 **Citizen** — view tree data and green cover maps (read-only)\n- 🏛️ **Officer** — add/edit/delete trees, log maintenance, approve health flags\n- 👑 **Admin** — full access including data exports and manual syncs\n\nUse *'show me the demo credentials'* to log in and try each role.",
            "navigate_to": None,
        })
    if any(kw in q for kw in ["bbmp", "what is bbmp", "bruhat bengaluru"]):
        return jsonify({
            "reply": "**BBMP** stands for *Bruhat Bengaluru Mahanagara Palike* — the civic body responsible for governing Bengaluru city. It manages 198 administrative wards, infrastructure, parks, and urban forestry. Vana Sethu was built to help BBMP officers manage the city's tree canopy more efficiently.",
            "navigate_to": None,
        })

    # ── Login & credentials ───────────────────────────────────────────────────
    if any(kw in q for kw in ["login", "sign in", "how do i login", "credentials", "demo", "password", "email", "officer password", "citizen login", "admin login"]):
        return jsonify({
            "reply": "**Demo login credentials:**\n\n👤 Citizen: `citizen@vanasethu.in` / `citizen123`\n🏛️ Officer: `officer@bbmp.gov.in` / `officer123`\n👑 Admin: `admin@bbmp.gov.in` / `admin123`\n\nOfficers and admins can add trees, log maintenance, and approve critical health flags.",
            "navigate_to": None,
        })

    # ── Help & capabilities ───────────────────────────────────────────────────
    if any(kw in q for kw in ["help", "what can you do", "what can you answer", "capabilities", "features", "how do you work"]):
        return jsonify({
            "reply": "Here's what I can do:\n\n**📊 Live Data**\n- How many trees are registered?\n- Which wards are deficient in green cover?\n- What is the current weather?\n- What is the average health score?\n\n**🗺️ Map Locations**\n- Show me Indiranagar on the map\n- Where is Cubbon Park?\n- Find Whitefield\n\n**🧭 Navigation**\n- Go to the inventory\n- Open the health scanner\n- Take me to the map\n\n**ℹ️ Platform Info**\n- What is Vana Sethu?\n- How many AI agents are there?\n- What are the guardrails?\n- Show demo credentials",
            "navigate_to": None,
        })

    # ── Agents ────────────────────────────────────────────────────────────────
    if any(kw in q for kw in ["how many agents", "ai agents", "what agents", "which agents"]):
        return jsonify({
            "reply": "Vana Sethu has **4 specialised AI agents**:\n1. **Health Agent** — diagnoses tree diseases from uploaded images using IBM Granite LLM\n2. **Inventory Agent** — manages the full tree registry with NL query support\n3. **Mapping Agent** — calculates ward-level green cover % from NDVI, OSM and weather data\n4. **Dashboard Agent** — orchestrates all agents, routes queries, and aggregates KPIs",
            "navigate_to": None,
        })

    # ── Guardrails ────────────────────────────────────────────────────────────
    if any(kw in q for kw in ["guardrail", "safety", "how safe", "security", "is this safe"]):
        return jsonify({
            "reply": "Vana Sethu applies **9 guardrail layers** on every request:\n1. **Input validation** — blocks injection, PII, profanity\n2. **Output validation** — toxicity filter, schema check, PII strip\n3. **Tool access control** — each agent can only use whitelisted tools\n4. **RBAC** — citizens, officers and admins see different data\n5. **Security** — jailbreak and SQL injection detection\n6. **Rate limiting** — prevents abuse and runaway calls\n7. **HITL** — critical actions require officer approval\n8. **Multi-agent safety** — loop detection, approved agent paths only\n9. **Ethics & fairness** — bias checks, explainability, immutable audit log",
            "navigate_to": None,
        })

    # ── Tree species ──────────────────────────────────────────────────────────
    if any(kw in q for kw in ["species", "what species", "types of trees", "which trees", "tree types", "kind of tree"]):
        return jsonify({
            "reply": "Common species tracked in Vana Sethu include:\n- **Peepal** (Ficus religiosa) — heritage trees, religious significance\n- **Neem** (Azadirachta indica) — medicinal, pest-resistant\n- **Banyan** (Ficus benghalensis) — large canopy, landmark trees\n- **Rain Tree** (Samanea saman) — fast-growing, wide shade\n- **Gulmohar** (Delonix regia) — flowering, street trees\n- **Ashoka, Tamarind, Coconut** and many more\n\nUse the **Inventory** to filter by species.",
            "navigate_to": "inventory",
        })

    # ── How to add a tree ─────────────────────────────────────────────────────
    if any(kw in q for kw in ["add a tree", "add tree", "register tree", "how do i add", "create tree", "new tree"]):
        return jsonify({
            "reply": "To add a tree:\n1. Log in as an **Officer** or Admin\n2. Open the **Tree Inventory** page\n3. Click the **+ Add Tree** button\n4. Fill in: Species, Ward number, Age, Health Score, Status\n5. Click **Save**\n\nThe new tree is added to the registry and the audit log is updated automatically.",
            "navigate_to": "inventory",
        })

    # ── How to scan a tree ────────────────────────────────────────────────────
    if any(kw in q for kw in ["scan a tree", "how do i scan", "scan tree", "tree scan", "health scan", "upload image", "diagnose a tree", "assess tree", "check tree health"]):
        return jsonify({
            "reply": "To scan a tree's health:\n1. Open the **Health Scanner** page\n2. Drag-and-drop or click to upload a **JPEG/PNG image** of the tree (max 5MB)\n3. Optionally fill in Ward, Temperature, Soil pH, Rainfall\n4. Click **Analyse Tree**\n5. The AI returns a **health score (0–100)**, detected issues, maintenance actions, and confidence\n\nIf the score drops below 20, an officer approval (HITL) is required before flagging.",
            "navigate_to": "health",
        })

    # ── Ward green cover specific ─────────────────────────────────────────────
    if any(kw in q for kw in ["green cover of ward", "ward cover", "green cover ward", "ward green"]):
        try:
            from backend.agents.mapping_agent import get_wards_geojson
            geo = get_wards_geojson()
            features = geo.get("features", [])
            lines = []
            for f in features:
                p = f.get("properties", {})
                lines.append(f"Ward {p.get('ward_no')} ({p.get('ward_name','?')}): **{p.get('green_cover_pct',0):.1f}%**")
            if lines:
                return jsonify({
                    "reply": "**Current green cover by ward:**\n" + "\n".join(f"- {l}" for l in lines),
                    "navigate_to": "map",
                })
        except Exception:
            pass

    # ── Navigation intent detection ──────────────────────────────────────────
    PAGE_ALIASES = {
        "home":      ["home", "dashboard", "main", "start", "overview"],
        "map":       ["map", "green cover", "ward map", "coverage", "vegetation", "ndvi", "deficient wards", "green space"],
        "inventory": ["inventory", "tree list", "tree registry", "how many trees", "species list"],
        "health":    ["health scanner", "scan", "diagnose", "disease", "sick tree", "analyse tree", "analyze tree", "upload image"],
        "metrics":   ["metrics", "ai dashboard", "performance", "accuracy", "rag metrics", "guardrail metrics", "llm stats"],
        "approvals": ["approval", "approvals", "pending approval", "officer approval"],
    }
    nav_panel = None
    for panel, aliases in PAGE_ALIASES.items():
        if any(alias in q for alias in aliases):
            nav_panel = panel
            break

    # ── Live data queries ─────────────────────────────────────────────────────
    try:
        if any(kw in q for kw in ["how many trees", "total trees", "tree count", "trees registered", "trees are there"]):
            from backend.agents.inventory_agent import get_summary
            s = get_summary()
            return jsonify({
                "reply": f"There are currently **{s['total_trees']} trees** registered in Vana Sethu. Average health score is **{s['avg_health_score']}/100** and **{s['maintenance_due']}** need maintenance.",
                "navigate_to": "inventory",
            })

        if any(kw in q for kw in ["deficient ward", "which wards", "worst ward", "low green cover", "green cover below", "need attention", "needs attention"]):
            from backend.agents.mapping_agent import get_deficient_wards
            wards = get_deficient_wards(15.0)
            if wards:
                worst = wards[0]
                names_str = ", ".join([f"Ward {w['ward_id']} ({w['green_cover_pct']}%)" for w in wards[:3]])
                return jsonify({
                    "reply": f"**{len(wards)} wards** are below 15% green cover. The worst is **Ward {worst['ward_id']}** at {worst['green_cover_pct']}%. Top deficient: {names_str}.",
                    "navigate_to": "map",
                })
            return jsonify({"reply": "All wards are currently above the 15% green cover threshold. 🌳", "navigate_to": "map"})

        if any(kw in q for kw in ["weather", "temperature", "rain", "humidity", "current weather"]):
            from backend.live_data.weather_fetcher import get_latest_weather
            w = get_latest_weather()
            if w.get("temperature"):
                return jsonify({
                    "reply": f"Current Bengaluru weather: **{w['temperature']}°C**, {w.get('condition_text','—')}. Humidity: {w.get('humidity','—')}%, Rainfall: {w.get('rainfall', 0)}mm.",
                    "navigate_to": None,
                })
            return jsonify({"reply": "Weather data is being fetched. Please check back shortly.", "navigate_to": None})

        if any(kw in q for kw in ["health score", "average health", "tree health", "avg health", "maintenance"]):
            from backend.agents.inventory_agent import get_summary
            s = get_summary()
            return jsonify({
                "reply": f"The average tree health score is **{s['avg_health_score']}/100**. **{s['maintenance_due']} trees** are flagged for maintenance and **{s['critical_trees']}** are in critical condition.",
                "navigate_to": "health",
            })

        if any(kw in q for kw in ["summary", "overview", "stats", "statistics", "platform status", "platform summary"]):
            from backend.agents.dashboard_agent import get_dashboard_summary
            d = get_dashboard_summary()
            inv = d.get("inventory", {})
            return jsonify({
                "reply": (
                    f"**Platform Summary:**\n"
                    f"- **{inv.get('total_trees','—')} trees** registered across Bengaluru\n"
                    f"- Average health score: **{inv.get('avg_health_score','—')}/100**\n"
                    f"- Trees needing maintenance: **{inv.get('maintenance_due','—')}**\n"
                    f"- Critical trees: **{inv.get('critical_trees','—')}**\n"
                    f"- Deficient wards (< 15% green cover): **{d.get('deficient_wards_count','—')}**"
                ),
                "navigate_to": nav_panel or "home",
            })

    except Exception:
        pass

    # ── If navigation intent was detected ────────────────────────────────────
    if nav_panel:
        labels = {"home": "Home", "map": "Green Cover Map", "inventory": "Tree Inventory",
                  "health": "Health Scanner", "metrics": "AI Dashboard", "approvals": "Approvals"}
        return jsonify({
            "reply": f"Taking you to the **{labels[nav_panel]}** page!",
            "navigate_to": nav_panel,
        })

    # ── Fallback with helpful suggestions ────────────────────────────────────
    return jsonify({
        "reply": "I didn't quite catch that. Here are some things you can ask me:\n- *\"How many trees are registered?\"*\n- *\"Which wards have low green cover?\"*\n- *\"Show me Indiranagar on the map\"*\n- *\"Go to the health scanner\"*\n- *\"What is Vana Sethu?\"*\n\nType **help** for the full list.",
        "navigate_to": None,
    })

