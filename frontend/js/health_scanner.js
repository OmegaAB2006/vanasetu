/**
 * health_scanner.js — Image upload + health assessment via Agent 1.
 * Features: drag-and-drop, image preview, loading spinner, HITL modal.
 */

const uploadZone    = document.getElementById("upload-zone");
const fileInput     = document.getElementById("file-input");
const assessBtn     = document.getElementById("assess-btn");
let selectedFile    = null;
let pendingActionId = null;

// ── Upload Zone — click / drag-and-drop ──────────────────────────────────────
uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", e => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});
uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) setSelectedFile(fileInput.files[0]);
});

// ── Set selected file + show inline preview ───────────────────────────────────
function setSelectedFile(file) {
  // Validate type client-side before even sending
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["jpg", "jpeg", "png"].includes(ext)) {
    showUploadError("Only JPEG / PNG files are allowed.");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showUploadError("File too large — maximum size is 5 MB.");
    return;
  }

  selectedFile = file;

  // Replace upload zone content with a preview thumbnail
  const reader = new FileReader();
  reader.onload = e => {
    uploadZone.innerHTML = `
      <img src="${e.target.result}"
           alt="Selected tree image"
           style="max-width:100%;max-height:160px;border-radius:8px;object-fit:cover;display:block;margin:0 auto 10px"/>
      <div style="font-size:12px;color:var(--text-muted);text-align:center">
        📎 <strong>${file.name}</strong>
        <br>${(file.size / 1024).toFixed(0)} KB
        <br><span style="color:var(--forest);cursor:pointer;text-decoration:underline" id="change-file-link">Change image</span>
      </div>`;
    document.getElementById("change-file-link")
      .addEventListener("click", e => { e.stopPropagation(); resetUploadZone(); });
  };
  reader.readAsDataURL(file);
}

function resetUploadZone() {
  selectedFile = null;
  fileInput.value = "";
  uploadZone.innerHTML = `
    <div class="upload-icon">🌿</div>
    <p>Drop a tree image here or click to browse</p>
    <p class="upload-hint">JPEG / PNG · max 5MB</p>`;
}

function showUploadError(msg) {
  const p = uploadZone.querySelector("p") || uploadZone;
  const err = document.createElement("p");
  err.style.cssText = "color:#D32F2F;font-size:12px;margin-top:8px;font-weight:600";
  err.textContent = "⚠ " + msg;
  uploadZone.appendChild(err);
  setTimeout(() => err.remove(), 4000);
}

// ── Analyse button ────────────────────────────────────────────────────────────
assessBtn.addEventListener("click", async () => {
  setLoadingState(true);

  const formData = new FormData();
  if (selectedFile) formData.append("image", selectedFile);

  const ward = document.getElementById("param-ward").value;
  const temp = document.getElementById("param-temp").value;
  const ph   = document.getElementById("param-ph").value;
  const rain = document.getElementById("param-rain").value;

  if (ward) formData.append("ward", ward);
  if (temp) formData.append("temperature", temp);
  if (ph)   formData.append("soil_ph", ph);
  if (rain) formData.append("rainfall", rain);

  try {
    const res  = await fetch(`${API}/health/assess`, { method: "POST", body: formData });
    const data = await res.json();

    if (data.status === "blocked") {
      window.showGuardrailBlock(data.message || data.reason);
      return;
    }

    // HITL hold — critical score requires officer approval
    if (data.status === "pending_approval") {
      pendingActionId = data.action_id;
      document.getElementById("hitl-action-id").textContent = `Action ID: ${data.action_id}`;
      document.getElementById("hitl-modal").style.display = "flex";
      return;
    }

    renderHealthResult(data);
  } catch (err) {
    console.error("Health assessment failed:", err);
    window.showGuardrailBlock("Health assessment failed. Please check your connection and try again.");
  } finally {
    setLoadingState(false);
  }
});

function setLoadingState(loading) {
  assessBtn.disabled = loading;
  assessBtn.innerHTML = loading
    ? `<span class="btn-spinner"></span> Analysing…`
    : "Analyse Tree";
}

// ── Render health result ───────────────────────────────────────────────────────
function renderHealthResult(data) {
  const resultCard = document.getElementById("health-result");
  resultCard.style.display = "flex";

  const score     = data.health_score ?? 0;
  const scoreRing = document.getElementById("health-score-ring");
  document.getElementById("health-score-num").textContent = score;

  // Color score ring by health level
  scoreRing.style.borderColor = score >= 70 ? "#2E7D32"
                               : score >= 40 ? "#F57F17" : "#D32F2F";
  scoreRing.style.boxShadow   = `0 0 0 4px ${score >= 70 ? "#E8F5E9" : score >= 40 ? "#FFF8E1" : "#FFEBEE"}`;

  // Issues
  const issuesList = document.getElementById("health-issues");
  issuesList.innerHTML = "";
  (data.issues || []).forEach(issue => {
    const li = document.createElement("li");
    li.textContent = issue;
    issuesList.appendChild(li);
  });
  if (!data.issues?.length) issuesList.innerHTML = "<li>✅ No issues detected</li>";

  // Maintenance actions
  const actionsList = document.getElementById("health-actions");
  actionsList.innerHTML = "";
  (data.maintenance_actions || []).forEach(action => {
    const li = document.createElement("li");
    li.textContent = action;
    actionsList.appendChild(li);
  });
  if (!data.maintenance_actions?.length) {
    actionsList.innerHTML = "<li>No immediate actions required</li>";
  }

  // Reasoning
  document.getElementById("health-reasoning").textContent =
    data.reasoning || "No reasoning provided.";

  // Confidence bar
  const conf = data.confidence ?? 0;
  document.getElementById("confidence-fill").style.width  = `${Math.round(conf * 100)}%`;
  document.getElementById("confidence-pct").textContent   = `${Math.round(conf * 100)}%`;

  // Scroll result into view smoothly
  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── HITL Modal ────────────────────────────────────────────────────────────────
document.getElementById("hitl-approve-btn").addEventListener("click", async () => {
  if (!pendingActionId) return;
  try {
    const res  = await fetch(`${API}/approve/${pendingActionId}`, {
      method: "POST",
      headers: window.authHeaders(),
    });
    const data = await res.json();
    document.getElementById("hitl-modal").style.display = "none";
    if (data.payload) renderHealthResult(data.payload);
  } catch {
    window.showGuardrailBlock("Approval failed. Please try again.");
  }
});

document.getElementById("hitl-reject-btn").addEventListener("click", async () => {
  if (!pendingActionId) return;
  try {
    await fetch(`${API}/reject/${pendingActionId}`, {
      method: "POST",
      headers: window.authHeaders(),
    });
  } finally {
    document.getElementById("hitl-modal").style.display = "none";
    pendingActionId = null;
  }
});
