/**
 * dashboard.js — Vana Sethu
 * Panel routing, KPI cards, weather strip, 5-min auto-poll.
 */

const API = "http://127.0.0.1:5001/api";

// ── Panel switching ───────────────────────────────────────────────────────────
function switchPanel(name) {
  document.querySelectorAll(".nav-link").forEach(l => {
    l.classList.toggle("active", l.dataset.panel === name);
  });
  document.querySelectorAll(".panel").forEach(p => {
    p.classList.toggle("active", p.id === `panel-${name}`);
  });
  if (name === "map") {
    // defer one frame so the panel is fully painted before Leaflet measures it
    requestAnimationFrame(() => {
      window.loadMap && window.loadMap();
    });
  }
  if (name === "inventory") window.loadInventory && window.loadInventory();
  if (name === "approvals") loadApprovals();
}
window.switchPanel = switchPanel;

document.querySelectorAll(".nav-link").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    switchPanel(link.dataset.panel);
  });
});

// ── Dashboard KPIs ────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const [sumRes, defRes] = await Promise.all([
      fetch(`${API}/dashboard/summary`),
      fetch(`${API}/map/deficient?threshold=15`),
    ]);
    const summary   = await sumRes.json();
    const deficient = await defRes.json();

    const inv = summary.inventory || {};
    // KPI strip (home panel)
    setEl("kpi-total",       inv.total_trees      ?? "—");
    setEl("kpi-avg-health",  inv.avg_health_score ?? "—");
    setEl("kpi-deficient",   summary.deficient_wards_count ?? "—");
    setEl("kpi-maintenance", inv.maintenance_due  ?? "—");
    setEl("kpi-temp",        summary.weather ? `${summary.weather.temperature}°C` : "—°C");

    // Hero floating stats
    setEl("hs-total",    inv.total_trees      ?? "—");
    setEl("hs-health",   inv.avg_health_score ?? "—");
    setEl("hs-deficient",summary.deficient_wards_count ?? "—");
    setEl("ms-total",    inv.total_trees      ?? "—");

    // Deficient wards table
    renderDeficientTable(Array.isArray(deficient) ? deficient : (summary.deficient_wards || []));
  } catch(err) {
    console.error("Dashboard load failed:", err);
  }
}

function renderDeficientTable(wards) {
  const tbody = document.getElementById("deficient-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  wards.forEach(w => {
    const pct = typeof w.green_cover_pct === "number" ? w.green_cover_pct.toFixed(1) : "—";
    const cls = w.green_cover_pct < 10 ? "badge-critical"
              : w.green_cover_pct < 15 ? "badge-stressed" : "badge-diseased";
    const label = w.green_cover_pct < 10 ? "Critical" : w.green_cover_pct < 15 ? "Low" : "Moderate";
    tbody.innerHTML += `<tr>
      <td>Ward ${w.ward_id}</td>
      <td><strong>${pct}%</strong></td>
      <td><span class="badge ${cls}">${label}</span></td>
      <td><button class="btn-secondary" style="padding:4px 12px;font-size:12px"
          onclick="switchPanel('map')">View Map</button></td>
    </tr>`;
  });
  if (!wards.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#617849;padding:20px">
      All wards above threshold — good coverage! 🌳</td></tr>`;
  }
}

// ── Weather pill ──────────────────────────────────────────────────────────────
async function loadWeather() {
  try {
    const res  = await fetch(`${API}/live/weather`);
    const data = await res.json();
    setEl("nav-weather-temp", `${data.temperature ?? "--"}°C`);
    setEl("nav-weather-cond", data.condition_text ?? "Bengaluru");
    setEl("nav-weather-icon", weatherEmoji(data.condition_text));
  } catch {
    setEl("nav-weather-cond", "Weather unavailable");
  }
}

function weatherEmoji(cond) {
  if (!cond) return "🌤";
  const c = cond.toLowerCase();
  if (c.includes("rain"))  return "🌧";
  if (c.includes("storm")) return "⛈";
  if (c.includes("clear")) return "☀";
  if (c.includes("cloud")) return "⛅";
  return "🌤";
}

// ── Approvals panel ───────────────────────────────────────────────────────────
async function loadApprovals() {
  const container = document.getElementById("approvals-list");
  if (!container) return;
  try {
    const res = await fetch(`${API}/pending-approvals`, { headers: authHeaders() });
    if (res.status === 403) {
      container.innerHTML = `<div style="padding:32px 32px;color:#617849">Approvals visible to officers and admins only.</div>`;
      return;
    }
    const list = await res.json();
    if (!list.length) {
      container.innerHTML = `<div style="padding:32px 32px;color:#617849">✅ No pending approvals.</div>`;
      return;
    }
    container.innerHTML = list.map(item => `
      <div class="approval-card">
        <div>
          <div class="approval-type">${item.action_type}</div>
          <div class="approval-id">ID: ${item.id} &nbsp;·&nbsp; ${new Date(item.created_at).toLocaleString()}</div>
        </div>
        <div class="approval-actions">
          <button class="btn-primary" onclick="resolveApproval('${item.id}','approve')">Approve</button>
          <button class="btn-danger"  onclick="resolveApproval('${item.id}','reject')">Reject</button>
        </div>
      </div>`).join("");
  } catch {
    container.innerHTML = `<div style="padding:32px;color:#C62828">Failed to load approvals.</div>`;
  }
}

window.resolveApproval = async function(actionId, action) {
  const endpoint = action === "approve" ? "approve" : "reject";
  try {
    const res  = await fetch(`${API}/${endpoint}/${actionId}`, { method:"POST", headers: authHeaders() });
    const data = await res.json();
    showToast(data.status === "approved" ? "✅ Action approved." : "❌ Action rejected.", data.status === "approved" ? "green" : "red");
    loadApprovals();
  } catch { showToast("Failed to process.", "red"); }
};

// ── Toast ─────────────────────────────────────────────────────────────────────
window.showGuardrailBlock = function(message) {
  const toast = document.getElementById("guardrail-toast");
  document.getElementById("toast-msg").textContent =
    `🛡 ${message || "Input contains restricted content. Please rephrase."}`;
  toast.style.display = "flex";
  setTimeout(() => { toast.style.display = "none"; }, 6000);
};

function showToast(msg, color = "green") {
  const toast = document.getElementById("guardrail-toast");
  document.getElementById("toast-msg").textContent = msg;
  toast.style.borderLeftColor = color === "green" ? "#2E7D32" : "#C62828";
  toast.style.display = "flex";
  setTimeout(() => { toast.style.display = "none"; }, 4000);
}

// ── Auth helpers ──────────────────────────────────────────────────────────────
function authHeaders() {
  const token = localStorage.getItem("auth_token");
  return token ? { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }
               : { "Content-Type": "application/json" };
}
window.authHeaders = authHeaders;

// ── Utilities ─────────────────────────────────────────────────────────────────
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadDashboard();
loadWeather();
setInterval(loadDashboard, 5 * 60 * 1000);
setInterval(loadWeather,   5 * 60 * 1000);
