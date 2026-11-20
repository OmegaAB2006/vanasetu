/**
 * inventory.js — Full tree inventory management.
 * Supports: list/filter, NL query, Add Tree, Edit Tree, Delete Tree,
 * View & Log Maintenance — all via plain language UI.
 */

// ── State ─────────────────────────────────────────────────────────────────────
let _currentTrees = [];

// ── Load & render inventory ───────────────────────────────────────────────────
async function loadInventory(params = {}) {
  const tbody  = document.getElementById("inventory-tbody");
  const status = document.getElementById("inventory-status");
  const count  = document.getElementById("inventory-count");

  status.textContent = "Loading trees…";
  tbody.innerHTML    = "";

  const qs = new URLSearchParams();
  if (params.ward)    qs.set("ward",    params.ward);
  if (params.species) qs.set("species", params.species);
  if (params.status)  qs.set("status",  params.status);

  try {
    const res   = await fetch(`${API}/inventory?${qs.toString()}`);
    const data  = await res.json();
    _currentTrees = data.trees || [];

    status.textContent = "";
    count.textContent  = `${_currentTrees.length} tree${_currentTrees.length !== 1 ? "s" : ""} found`;

    renderTreeRows(_currentTrees);
  } catch (err) {
    status.textContent = "Failed to load inventory. Please try again.";
    console.error(err);
  }
}

function renderTreeRows(trees) {
  const tbody = document.getElementById("inventory-tbody");
  tbody.innerHTML = "";

  if (!trees.length) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:28px;color:#757575">
      No trees found. Try a different filter or <strong>add a new tree</strong> below.
    </td></tr>`;
    return;
  }

  trees.forEach(t => {
    const badge       = `<span class="badge badge-${t.status}">${t.status}</span>`;
    const scoreColor  = t.health_score >= 70 ? "#2E7D32"
                      : t.health_score >= 40 ? "#F57F17" : "#D32F2F";
    tbody.innerHTML += `
      <tr>
        <td><strong>#${t.id}</strong></td>
        <td>${t.species}</td>
        <td>Ward ${t.ward}</td>
        <td>${t.age_years}y</td>
        <td><strong style="color:${scoreColor}">${t.health_score}/100</strong></td>
        <td>${badge}</td>
        <td>${t.last_checked ? t.last_checked : "—"}</td>
        <td class="inv-actions">
          <button class="btn-icon" title="Edit tree" onclick="openEditModal(${t.id})">✏️</button>
          <button class="btn-icon" title="View maintenance log" onclick="openMaintModal(${t.id}, '${t.species}')">🔧</button>
          <button class="btn-icon btn-icon-danger" title="Delete tree" onclick="confirmDelete(${t.id}, '${t.species}')">🗑️</button>
        </td>
      </tr>`;
  });
}

// ── Filter button ─────────────────────────────────────────────────────────────
document.getElementById("filter-btn").addEventListener("click", () => {
  loadInventory({
    ward:    document.getElementById("filter-ward").value   || undefined,
    species: document.getElementById("filter-species").value || undefined,
    status:  document.getElementById("filter-status").value  || undefined,
  });
});

// ── NL Query ("Search with AI") ───────────────────────────────────────────────
document.getElementById("nl-query-btn").addEventListener("click", async () => {
  const queryText = document.getElementById("nl-query-input").value.trim();
  if (!queryText) return;

  const status = document.getElementById("inventory-status");
  const count  = document.getElementById("inventory-count");
  status.textContent = "🤖 Analysing your query…";
  document.getElementById("inventory-tbody").innerHTML = "";

  try {
    const res  = await fetch(`${API}/inventory/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText }),
    });
    const data = await res.json();

    if (data.status === "blocked") {
      window.showGuardrailBlock(data.message || data.reason);
      status.textContent = "";
      return;
    }

    _currentTrees = data.trees || [];
    const filters = data.filters_applied || {};

    // Human-readable filter summary
    const filterParts = [];
    if (filters.ward)        filterParts.push(`Ward ${filters.ward}`);
    if (filters.species)     filterParts.push(`Species: ${filters.species}`);
    if (filters.status)      filterParts.push(`Status: ${filters.status}`);
    if (filters.health_max)  filterParts.push(`Health below ${filters.health_max}`);
    if (filters.health_min)  filterParts.push(`Health above ${filters.health_min}`);
    status.textContent = filterParts.length
      ? `Showing: ${filterParts.join(" · ")}` : "";
    count.textContent = `${_currentTrees.length} tree${_currentTrees.length !== 1 ? "s" : ""} found`;

    renderTreeRows(_currentTrees);
  } catch (err) {
    status.textContent = "Query failed. Please try again.";
    console.error(err);
  }
});

document.getElementById("nl-query-input").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("nl-query-btn").click();
});

// ── Add Tree Modal ────────────────────────────────────────────────────────────
function openAddModal() {
  document.getElementById("inv-modal-title").textContent = "Add New Tree";
  document.getElementById("inv-form-tree-id").value      = "";
  document.getElementById("inv-form-species").value      = "";
  document.getElementById("inv-form-ward").value         = "";
  document.getElementById("inv-form-lat").value          = "";
  document.getElementById("inv-form-lng").value          = "";
  document.getElementById("inv-form-age").value          = "";
  document.getElementById("inv-form-health").value       = "100";
  document.getElementById("inv-form-status").value       = "healthy";
  document.getElementById("inv-form-date").value         = "";
  document.getElementById("inv-modal-error").textContent = "";
  document.getElementById("inv-modal").style.display     = "flex";
  document.getElementById("inv-form-species").focus();
}
window.openAddModal = openAddModal;

function openEditModal(treeId) {
  const t = _currentTrees.find(x => x.id === treeId);
  if (!t) { alert("Tree not found in current list. Reload inventory first."); return; }
  document.getElementById("inv-modal-title").textContent = `Edit Tree #${treeId}`;
  document.getElementById("inv-form-tree-id").value      = treeId;
  document.getElementById("inv-form-species").value      = t.species || "";
  document.getElementById("inv-form-ward").value         = t.ward    || "";
  document.getElementById("inv-form-lat").value          = t.latitude  || "";
  document.getElementById("inv-form-lng").value          = t.longitude || "";
  document.getElementById("inv-form-age").value          = t.age_years || "";
  document.getElementById("inv-form-health").value       = t.health_score ?? 100;
  document.getElementById("inv-form-status").value       = t.status || "healthy";
  document.getElementById("inv-form-date").value         = t.last_checked || "";
  document.getElementById("inv-modal-error").textContent = "";
  document.getElementById("inv-modal").style.display     = "flex";
  document.getElementById("inv-form-species").focus();
}
window.openEditModal = openEditModal;

function closeInvModal() {
  document.getElementById("inv-modal").style.display = "none";
}
window.closeInvModal = closeInvModal;

document.getElementById("inv-modal-save").addEventListener("click", async () => {
  const errEl   = document.getElementById("inv-modal-error");
  const treeId  = document.getElementById("inv-form-tree-id").value;
  const species = document.getElementById("inv-form-species").value.trim();
  const ward    = parseInt(document.getElementById("inv-form-ward").value);
  const lat     = parseFloat(document.getElementById("inv-form-lat").value);
  const lng     = parseFloat(document.getElementById("inv-form-lng").value);
  const age     = parseInt(document.getElementById("inv-form-age").value) || 0;
  const health  = parseInt(document.getElementById("inv-form-health").value) || 100;
  const status  = document.getElementById("inv-form-status").value;
  const checked = document.getElementById("inv-form-date").value || null;

  if (!species) { errEl.textContent = "Species name is required."; return; }
  if (!ward || isNaN(ward)) { errEl.textContent = "Ward number is required."; return; }

  const body = { species, ward, age_years: age, health_score: health, status };
  if (!isNaN(lat) && lat) body.latitude  = lat;
  if (!isNaN(lng) && lng) body.longitude = lng;
  if (checked) body.last_checked = checked;
  if (!body.latitude)  body.latitude  = 12.9716;   // default Bengaluru centre
  if (!body.longitude) body.longitude = 77.5946;

  errEl.textContent = "";
  document.getElementById("inv-modal-save").textContent = "Saving…";
  document.getElementById("inv-modal-save").disabled = true;

  try {
    let res;
    if (treeId) {
      // UPDATE
      res = await fetch(`${API}/inventory/${treeId}`, {
        method: "PUT",
        headers: { ...window.authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } else {
      // CREATE
      res = await fetch(`${API}/inventory`, {
        method: "POST",
        headers: { ...window.authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    const data = await res.json();
    if (!res.ok || data.status === "error") {
      errEl.textContent = data.message || data.reason || "Save failed.";
      return;
    }
    closeInvModal();
    loadInventory();   // refresh table
    showInvToast(treeId ? `✅ Tree #${treeId} updated!` : `✅ New tree added (ID #${data.id || ""})!`);
  } catch {
    errEl.textContent = "Network error. Please try again.";
  } finally {
    document.getElementById("inv-modal-save").textContent = "Save";
    document.getElementById("inv-modal-save").disabled = false;
  }
});

// ── Delete confirmation ────────────────────────────────────────────────────────
async function confirmDelete(treeId, species) {
  if (!confirm(`Delete tree #${treeId} (${species})?\n\nThis action is permanent and will be logged.`)) return;
  try {
    const res  = await fetch(`${API}/inventory/${treeId}`, {
      method: "DELETE",
      headers: window.authHeaders(),
    });
    const data = await res.json();
    if (!res.ok || data.status === "error") {
      showInvToast(`❌ ${data.message || "Delete failed."}`, "red");
      return;
    }
    showInvToast(`🗑️ Tree #${treeId} deleted.`);
    loadInventory();
  } catch {
    showInvToast("❌ Network error. Please try again.", "red");
  }
}
window.confirmDelete = confirmDelete;

// ── Maintenance Modal ─────────────────────────────────────────────────────────
async function openMaintModal(treeId, species) {
  document.getElementById("maint-tree-label").textContent = `Tree #${treeId} — ${species}`;
  document.getElementById("maint-tree-id-hidden").value  = treeId;
  document.getElementById("maint-action").value          = "";
  document.getElementById("maint-notes").value           = "";
  document.getElementById("maint-officer").value         = "";
  document.getElementById("maint-modal-error").textContent = "";
  document.getElementById("maint-modal").style.display   = "flex";

  // Load existing log
  const logEl = document.getElementById("maint-log-list");
  logEl.innerHTML = "<li style='color:#888'>Loading…</li>";
  try {
    const res  = await fetch(`${API}/maintenance/${treeId}`);
    const rows = await res.json();
    if (!rows.length) {
      logEl.innerHTML = "<li style='color:#888'>No maintenance records yet.</li>";
    } else {
      logEl.innerHTML = rows.map(r => `
        <li>
          <strong>${r.action}</strong>
          <span style="color:#888;font-size:11px"> · ${r.date || "—"} · ${r.officer_name || "unknown"}</span>
          ${r.notes ? `<div style="font-size:11px;color:#666;margin-top:2px">${r.notes}</div>` : ""}
        </li>`).join("");
    }
  } catch {
    logEl.innerHTML = "<li style='color:#D32F2F'>Failed to load log.</li>";
  }
}
window.openMaintModal = openMaintModal;

function closeMaintModal() {
  document.getElementById("maint-modal").style.display = "none";
}
window.closeMaintModal = closeMaintModal;

document.getElementById("maint-save-btn").addEventListener("click", async () => {
  const errEl      = document.getElementById("maint-modal-error");
  const treeId     = document.getElementById("maint-tree-id-hidden").value;
  const action     = document.getElementById("maint-action").value.trim();
  const notes      = document.getElementById("maint-notes").value.trim();
  const officer    = document.getElementById("maint-officer").value.trim();

  if (!action) { errEl.textContent = "Please describe the maintenance action."; return; }

  errEl.textContent = "";
  document.getElementById("maint-save-btn").textContent = "Logging…";
  document.getElementById("maint-save-btn").disabled = true;

  try {
    const res = await fetch(`${API}/maintenance`, {
      method: "POST",
      headers: { ...window.authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ tree_id: parseInt(treeId), action, notes, officer_name: officer }),
    });
    const data = await res.json();
    if (!res.ok || data.status === "error") {
      errEl.textContent = data.message || "Failed to log maintenance.";
      return;
    }
    closeMaintModal();
    showInvToast(`🔧 Maintenance logged for tree #${treeId}`);
  } catch {
    errEl.textContent = "Network error. Please try again.";
  } finally {
    document.getElementById("maint-save-btn").textContent = "Log Action";
    document.getElementById("maint-save-btn").disabled = false;
  }
});

// ── Toast notification ────────────────────────────────────────────────────────
function showInvToast(msg, type = "green") {
  const toast = document.getElementById("guardrail-toast");
  const msgEl = document.getElementById("toast-msg");
  if (toast && msgEl) {
    msgEl.textContent = msg;
    toast.style.borderLeftColor = type === "red" ? "#C62828" : "#2E7D32";
    toast.style.display = "flex";
    setTimeout(() => { toast.style.display = "none"; }, 4000);
  }
}

window.loadInventory = loadInventory;
