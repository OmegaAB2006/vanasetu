/**
 * metrics.js — LLM & Agent Performance Dashboard
 * Fetches /api/metrics and renders all 6 metric category tabs.
 */

const METRIC_API = "http://127.0.0.1:5001/api/metrics";
let metricsData = null;

// ── Tab switching ──────────────────────────────────────────────────────────────
document.querySelectorAll(".mtab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mtab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".mtab-panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`mtab-${tab.dataset.tab}`).classList.add("active");
    if (metricsData) renderCurrentTab(tab.dataset.tab);
  });
});

document.getElementById("refresh-metrics-btn").addEventListener("click", loadMetrics);

// ── Load metrics ───────────────────────────────────────────────────────────────
async function loadMetrics() {
  try {
    const res  = await fetch(METRIC_API);
    metricsData = await res.json();
    const activeTab = document.querySelector(".mtab.active")?.dataset.tab || "accuracy";
    renderCurrentTab(activeTab);
    // Pre-render all tabs so switching is instant
    ["accuracy","rag","agentic","safety","perf","multiagent"].forEach(renderCurrentTab);
  } catch(e) {
    console.error("Metrics load failed:", e);
  }
}

function renderCurrentTab(tab) {
  if (!metricsData) return;
  if (tab === "accuracy")   renderAccuracy(metricsData.accuracy_quality);
  if (tab === "rag")        renderRAG(metricsData.rag);
  if (tab === "agentic")    renderAgentic(metricsData.agentic);
  if (tab === "safety")     renderSafety(metricsData.safety_guardrails);
  if (tab === "perf")       renderPerf(metricsData.performance_cost);
  if (tab === "multiagent") renderMultiAgent(metricsData.multiagent_system);
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function pct(v) { return typeof v === "number" ? (v * 100).toFixed(1) + "%" : "—"; }
function num(v, dec=3) { return typeof v === "number" ? v.toFixed(dec) : "—"; }

function kpiHtml(val, lbl, cls="ok", sub="") {
  return `<div class="m-kpi ${cls}">
    <div class="m-kpi-val">${val}</div>
    <div class="m-kpi-lbl">${lbl}</div>
    ${sub ? `<div class="m-kpi-sub">${sub}</div>` : ""}
  </div>`;
}

function barChartHtml(rows) {
  // rows: [{label, value (0–1), cls}]
  return rows.map(r => {
    const pctW = Math.min(Math.max((r.value || 0) * 100, 2), 100).toFixed(1);
    const cls  = r.cls || "";
    const displayVal = r.raw !== undefined ? r.raw : pct(r.value);
    return `<div class="bar-row">
      <div class="bar-label">${r.label}</div>
      <div class="bar-track">
        <div class="bar-fill ${cls}" style="width:${pctW}%">
          <span class="bar-val">${displayVal}</span>
        </div>
      </div>
    </div>`;
  }).join("");
}

// ── 1. Accuracy & Quality ──────────────────────────────────────────────────────
function renderAccuracy(d) {
  if (!d) return;
  document.getElementById("mq-kpis").innerHTML =
    kpiHtml(pct(d.accuracy),  "Accuracy",   "ok") +
    kpiHtml(pct(d.precision), "Precision",  "ok") +
    kpiHtml(pct(d.recall),    "Recall",     "ok") +
    kpiHtml(pct(d.f1_score),  "F1 Score",   "ok") +
    kpiHtml(pct(d.exact_match),"Exact Match","info") +
    kpiHtml(pct(d.semantic_similarity),"Semantic Sim.","ok") +
    kpiHtml(d.total_evaluations || 0, "Total Evaluations","info");

  document.getElementById("mq-bar-chart").innerHTML = barChartHtml([
    {label:"Accuracy",           value: d.accuracy},
    {label:"Precision",          value: d.precision},
    {label:"Recall",             value: d.recall},
    {label:"F1 Score",           value: d.f1_score},
    {label:"Exact Match",        value: d.exact_match, cls:"info-fill"},
    {label:"Semantic Similarity",value: d.semantic_similarity},
    {label:"ROUGE-L",            value: d.rouge_l,    cls:"info-fill"},
    {label:"BLEU",               value: d.bleu,       cls:"info-fill"},
  ]);
}

// ── 2. RAG ─────────────────────────────────────────────────────────────────────
function renderRAG(d) {
  if (!d) return;
  document.getElementById("mrag-kpis").innerHTML =
    kpiHtml(pct(d.context_precision), "Context Precision", "ok") +
    kpiHtml(pct(d.context_recall),    "Context Recall",    "ok") +
    kpiHtml(pct(d.faithfulness),      "Faithfulness",      "ok") +
    kpiHtml(pct(d.answer_relevancy),  "Answer Relevancy",  "ok") +
    kpiHtml(pct(d.groundedness),      "Groundedness",      "ok") +
    kpiHtml(d.total_rag_queries || 0, "Total RAG Queries", "info");

  document.getElementById("mrag-bar-chart").innerHTML = barChartHtml([
    {label:"Context Precision",  value: d.context_precision},
    {label:"Context Recall",     value: d.context_recall},
    {label:"Faithfulness",       value: d.faithfulness},
    {label:"Answer Relevancy",   value: d.answer_relevancy},
    {label:"Context Relevancy",  value: d.context_relevancy},
    {label:"Groundedness",       value: d.groundedness},
  ]);
}

// ── 3. Agentic AI ──────────────────────────────────────────────────────────────
function renderAgentic(d) {
  if (!d) return;
  document.getElementById("mag-kpis").innerHTML =
    kpiHtml(pct(d.task_completion_rate),         "Task Completion",      "ok") +
    kpiHtml(pct(d.goal_achievement),             "Goal Achievement",     "ok") +
    kpiHtml(pct(d.tool_call_accuracy),           "Tool Call Accuracy",   "ok") +
    kpiHtml(pct(d.tool_execution_success_rate),  "Tool Exec. Success",   "ok") +
    kpiHtml(pct(d.planning_accuracy),            "Planning Accuracy",    "ok") +
    kpiHtml(pct(d.reasoning_quality),            "Reasoning Quality",    "ok") +
    kpiHtml(pct(d.agent_coordination),           "Agent Coordination",   "ok") +
    kpiHtml(pct(d.loop_detection_rate),          "Loop Detection",       "ok", "anti-loop guardrail") +
    kpiHtml(d.total_agent_interactions || 0,     "Total Interactions",   "info");

  // Per-agent cards
  const pa = d.per_agent || {};
  const agentLabels = {
    health_agent:    "Health Agent",
    inventory_agent: "Inventory Agent",
    mapping_agent:   "Mapping Agent",
    dashboard_agent: "Dashboard Agent",
  };
  document.getElementById("agent-perf-grid").innerHTML = Object.entries(pa).map(([id, m]) => `
    <div class="agent-card">
      <div class="agent-name">${agentLabels[id] || id}</div>
      <div class="agent-metric">
        <div class="agent-metric-lbl">Calls</div>
        <div class="agent-metric-val">${m.calls || 0}</div>
      </div>
      <div class="agent-metric">
        <div class="agent-metric-lbl">Task Completion</div>
        <div class="agent-metric-val">${pct(m.task_completion_rate)}</div>
      </div>
      <div class="agent-metric">
        <div class="agent-metric-lbl">Tool Accuracy</div>
        <div class="agent-metric-val">${pct(m.tool_call_accuracy)}</div>
      </div>
    </div>`).join("");
}

// ── 4. Safety & Guardrails ─────────────────────────────────────────────────────
function renderSafety(d) {
  if (!d) return;
  const hallucinationCls = d.hallucination_rate > 0.05 ? "danger" : "ok";
  document.getElementById("ms-kpis").innerHTML =
    kpiHtml(pct(d.hallucination_rate),          "Hallucination Rate",        hallucinationCls) +
    kpiHtml(num(d.toxicity_score, 4),           "Toxicity Score",             "ok", "lower = better") +
    kpiHtml(pct(d.prompt_injection_resistance), "Injection Resistance",       "ok") +
    kpiHtml(num(d.pii_leakage_rate, 4),         "PII Leakage Rate",           "ok") +
    kpiHtml(pct(d.guardrail_intervention_rate), "Guardrail Intervention",     "info") +
    kpiHtml(d.guardrail_blocks_total || 0,      "Total Guardrail Blocks",     "warn");

  document.getElementById("ms-bar-chart").innerHTML = barChartHtml([
    {label:"Injection Resistance",    value: d.prompt_injection_resistance},
    {label:"Hallucination (inverted)",value: 1 - d.hallucination_rate},
    {label:"Toxicity (inverted)",     value: 1 - Math.min(d.toxicity_score * 10, 1), cls:"info-fill"},
    {label:"PII Safety",              value: 1 - Math.min(d.pii_leakage_rate * 100, 1)},
    {label:"Policy Compliance",       value: 1 - Math.min(d.policy_violation_rate * 10, 1)},
  ]);

  const guardrails = [
    "Input Guardrail","Output Guardrail","Tool Guardrail","Data Guardrail",
    "Security Guardrail","Operational Guardrail","HITL Guardrail",
    "Multi-Agent Guardrail","Ethics Guardrail",
  ];
  document.getElementById("guardrail-status-grid").innerHTML = guardrails.map(g => `
    <div class="gl-row">
      <div class="gl-dot active"></div>
      <div class="gl-name">${g}</div>
      <div class="gl-count">Active</div>
    </div>`).join("");
}

// ── 5. Performance & Cost ──────────────────────────────────────────────────────
function renderPerf(d) {
  if (!d) return;
  const latCls = d.avg_response_latency_ms > 2000 ? "warn" : "ok";
  document.getElementById("mp-kpis").innerHTML =
    kpiHtml(`${d.avg_response_latency_ms?.toFixed(0)}ms`, "Avg Response Latency", latCls) +
    kpiHtml(`${d.time_to_first_token_ms?.toFixed(0)}ms`,  "Time to First Token",  "info") +
    kpiHtml(`${d.tokens_per_second?.toFixed(1)} tok/s`,   "Tokens per Second",    "ok") +
    kpiHtml(`$${d.cost_per_request_usd?.toFixed(5)}`,     "Cost per Request",     "info") +
    kpiHtml(`${(d.error_rate * 100)?.toFixed(2)}%`,       "Error Rate",           d.error_rate > 0.03 ? "warn" : "ok") +
    kpiHtml(d.total_llm_calls || 0,                       "Total LLM Calls",      "info") +
    kpiHtml(`$${d.total_cost_usd?.toFixed(4)}`,           "Total Cost (USD)",     "info");

  document.getElementById("mp-token-chart").innerHTML = barChartHtml([
    {label:"Avg Input Tokens",  value: d.avg_input_tokens / 512,  raw: `${d.avg_input_tokens?.toFixed(0)} tok`},
    {label:"Avg Output Tokens", value: d.avg_output_tokens / 512, raw: `${d.avg_output_tokens?.toFixed(0)} tok`, cls:"info-fill"},
    {label:"Throughput (norm)", value: d.throughput_req_per_min / 20, raw: `${d.throughput_req_per_min?.toFixed(1)} req/min`},
    {label:"Error Rate (norm)", value: d.error_rate * 10, raw: pct(d.error_rate), cls: d.error_rate > 0.03 ? "warn-fill":"info-fill"},
  ]);

  document.getElementById("cost-breakdown").innerHTML = [
    ["Avg Input Tokens",        d.avg_input_tokens?.toFixed(1) || "—"],
    ["Avg Output Tokens",       d.avg_output_tokens?.toFixed(1) || "—"],
    ["Cost per Request (USD)",  `$${d.cost_per_request_usd?.toFixed(6) || "—"}`],
    ["Cost per Successful Task",`$${d.cost_per_successful_task_usd?.toFixed(6) || "—"}`],
    ["Total LLM Calls",         d.total_llm_calls || 0],
    ["Total Cost (USD)",        `$${d.total_cost_usd?.toFixed(5) || "—"}`],
    ["Throughput (req/min)",    d.throughput_req_per_min?.toFixed(1) || "—"],
    ["Error Rate",              pct(d.error_rate)],
  ].map(([k,v]) => `<div class="cost-row"><span class="cost-key">${k}</span><span class="cost-val">${v}</span></div>`).join("");
}

// ── 6. Multi-Agent ─────────────────────────────────────────────────────────────
function renderMultiAgent(d) {
  if (!d) return;
  document.getElementById("mma-kpis").innerHTML =
    kpiHtml(`${d.avg_e2e_execution_time_ms?.toFixed(0)}ms`, "Avg E2E Time",         "info") +
    kpiHtml(pct(d.workflow_completion_rate),                 "Workflow Completion",  "ok") +
    kpiHtml(pct(d.supervisor_agent_accuracy),               "Supervisor Accuracy",  "ok") +
    kpiHtml(pct(d.conflict_resolution_rate),                "Conflict Resolution",  "ok") +
    kpiHtml(pct(d.inter_agent_consistency),                 "Inter-Agent Consist.", "ok") +
    kpiHtml(pct(d.agent_communication_success_rate),        "Comm. Success Rate",   "ok") +
    kpiHtml(d.total_inter_agent_calls || 0,                 "Total Agent Calls",    "info");

  const acc = d.individual_agent_accuracy || {};
  const agentLabels = {
    health_agent:    "Health Agent",
    inventory_agent: "Inventory Agent",
    mapping_agent:   "Mapping Agent",
    dashboard_agent: "Dashboard Agent",
  };
  document.getElementById("mma-bar-chart").innerHTML = barChartHtml(
    Object.entries(acc).map(([id, v]) => ({label: agentLabels[id] || id, value: v}))
  );
}

// ── Auto-load on panel open ────────────────────────────────────────────────────
// Hook into panel switching (dashboard.js exposes switchPanel)
const _origSwitchPanel = window.switchPanel;
window.switchPanel = function(name) {
  if (_origSwitchPanel) _origSwitchPanel(name);
  if (name === "metrics" && !metricsData) loadMetrics();
};
