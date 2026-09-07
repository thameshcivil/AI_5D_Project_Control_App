// ============================================================
// AI-Integrated 5D Project Control System — Frontend Controller
// ============================================================
const CYAN = "#4FD1E8";
const ORANGE = "#F97316";
const GREEN = "#34D399";
const AMBER = "#FBBF24";
const RED = "#F87171";
const MUTED = "#8496B5";
const GRID = "rgba(148,178,220,0.10)";

Chart.defaults.color = MUTED;
Chart.defaults.font.family = "Inter, sans-serif";
Chart.defaults.borderColor = GRID;

const charts = {}; // keep references so we can destroy/rebuild on nav

// ---------------- Navigation ----------------
const titles = {
  overview: ["Project Overview", "Live snapshot of the 5D control model — geometry, time, and cost, in one place."],
  qto: ["AI Quantity Takeoff", "Upload a 2D drawing to auto-detect rooms and derive quantities via computer vision."],
  boq: ["Bill of Quantities & Cost Estimation", "Rate-linked BOQ generated from detected / defined quantities."],
  schedule: ["Schedule & Resource Planning", "Day-wise labour, material and machinery requirement, sequenced by activity."],
  delay: ["AI Delay Risk Prediction", "Random-Forest model trained on 260 historical projects."],
  cashflow: ["Cash Flow Forecasting", "Weekly and monthly S-curve for material, labour and machinery funding."],
};

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    document.getElementById("tab-" + tab).classList.add("active");
    document.getElementById("page-title").textContent = titles[tab][0];
    document.getElementById("page-sub").textContent = titles[tab][1];
    loadTab(tab);
  });
});

const loaded = new Set();
function loadTab(tab) {
  if (loaded.has(tab)) return;
  loaded.add(tab);
  if (tab === "overview") loadOverview();
  if (tab === "boq") loadBOQ();
  if (tab === "schedule") loadSchedule();
  if (tab === "delay") loadDelayMeta();
  if (tab === "cashflow") loadCashflow();
}

function fmtINR(n) {
  if (n === undefined || n === null) return "—";
  return "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
function fmtNum(n, d = 1) {
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: d });
}

// ---------------- Overview ----------------
async function loadOverview() {
  const ov = await fetch("/api/overview").then(r => r.json());
  document.getElementById("kpi-cost").textContent = fmtINR(ov.total_project_cost);
  document.getElementById("kpi-duration").textContent = ov.meta.actual_planned_duration_days + " days";
  document.getElementById("kpi-area").textContent = ov.meta.total_builtup_area_sqm + " sqm";
  document.getElementById("kpi-accuracy").textContent = (ov.delay_model_accuracy * 100).toFixed(1) + "%";

  document.getElementById("ov-name").textContent = ov.meta.project_name;
  document.getElementById("ov-type").textContent = ov.meta.project_type;
  document.getElementById("ov-plot").textContent = ov.meta.plot_dims + " (" + ov.meta.plot_size_sqm + " sqm)";
  document.getElementById("ov-structure").textContent = ov.meta.structure_type;
  document.getElementById("ov-foundation").textContent = ov.meta.foundation_type;
  document.getElementById("ov-costsqm").textContent = fmtINR(ov.cost_per_sqm) + " / sqm";

  const monthly = await fetch("/api/cashflow/monthly").then(r => r.json());
  const ctx = document.getElementById("chart-overview-scurve");
  charts.ovScurve = new Chart(ctx, {
    type: "line",
    data: {
      labels: monthly.rows.map(r => r.month),
      datasets: [{
        label: "Cumulative % Cost",
        data: monthly.rows.map(r => r.cumulative_pct),
        borderColor: CYAN, backgroundColor: "rgba(79,209,232,0.12)",
        fill: true, tension: 0.35, pointRadius: 3, pointBackgroundColor: CYAN,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: GRID }, ticks: { callback: v => v + "%" }, title: { display: true, text: "Cumulative Cost (%)" } },
        x: { grid: { display: false } },
      },
    },
  });
}

// ---------------- QTO ----------------
const uploadBox = document.getElementById("upload-box");
const fileInput = document.getElementById("qto-file");
const preview = document.getElementById("qto-preview");
const hint = document.getElementById("upload-hint");
let currentFile = null;

uploadBox.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => {
  if (e.target.files[0]) setFile(e.target.files[0]);
});
uploadBox.addEventListener("dragover", e => e.preventDefault());
uploadBox.addEventListener("drop", e => {
  e.preventDefault();
  if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});

function setFile(file) {
  currentFile = file;
  const url = URL.createObjectURL(file);
  preview.src = url;
  preview.style.display = "block";
  hint.style.display = "none";
}

document.getElementById("btn-load-sample").addEventListener("click", async () => {
  const resp = await fetch("/assets/sample_floor_plan.png");
  const blob = await resp.blob();
  const file = new File([blob], "sample_floor_plan.png", { type: "image/png" });
  setFile(file);
  document.getElementById("qto-status").textContent = "Sample plan loaded.";
});

document.getElementById("btn-analyze").addEventListener("click", async () => {
  if (!currentFile) {
    document.getElementById("qto-status").textContent = "Please choose or load an image first.";
    return;
  }
  document.getElementById("qto-status").textContent = "Running contour detection…";
  const fd = new FormData();
  fd.append("image", currentFile);
  fd.append("px_per_m", document.getElementById("px-per-m").value);
  fd.append("wall_height_m", document.getElementById("wall-height").value);

  const res = await fetch("/api/qto/analyze", { method: "POST", body: fd }).then(r => r.json());
  if (res.error) {
    document.getElementById("qto-status").textContent = "Error: " + res.error;
    return;
  }
  document.getElementById("qto-status").textContent = "Done.";
  document.getElementById("qto-results-empty").style.display = "none";
  document.getElementById("qto-results").style.display = "block";
  document.getElementById("qto-rooms").textContent = res.rooms_detected;
  document.getElementById("qto-area").textContent = fmtNum(res.total_carpet_area_sqm, 1);
  document.getElementById("qto-wall").textContent = fmtNum(res.estimated_wall_length_m, 1);

  const derived = document.getElementById("qto-derived-table");
  derived.innerHTML = `<thead><tr><th>Derived Quantity</th><th>Estimate</th></tr></thead>
    <tbody>
      <tr><td>Brickwork volume (230mm walls)</td><td class="num">${fmtNum(res.estimated_brickwork_volume_cum, 2)} cum</td></tr>
      <tr><td>Plaster area (internal + ceiling proxy)</td><td class="num">${fmtNum(res.estimated_plaster_area_sqm, 1)} sqm</td></tr>
      <tr><td>Flooring area</td><td class="num">${fmtNum(res.estimated_flooring_area_sqm, 1)} sqm</td></tr>
      <tr><td>Calibration used</td><td class="num">${res.calibration_px_per_m} px/m</td></tr>
    </tbody>`;

  const roomTable = document.getElementById("qto-room-table");
  let rows = res.rooms.map(r => `<tr><td>${r.room_id}</td><td class="num">${r.area_sqm}</td><td class="num">${r.perimeter_m}</td></tr>`).join("");
  roomTable.innerHTML = `<thead><tr><th>Room</th><th>Area (sqm)</th><th>Perimeter (m)</th></tr></thead><tbody>${rows}</tbody>`;
});

// ---------------- BOQ ----------------
let boqItemsCache = [];
async function loadBOQ() {
  const data = await fetch("/api/boq").then(r => r.json());
  boqItemsCache = data.items;
  renderBOQTable(boqItemsCache);
  document.getElementById("boq-total").textContent = "Total Estimated Project Cost: " + fmtINR(data.total_cost);

  const catCtx = document.getElementById("chart-boq-category");
  charts.boqCat = new Chart(catCtx, {
    type: "doughnut",
    data: {
      labels: data.category_summary.map(c => c.category),
      datasets: [{
        data: data.category_summary.map(c => c.amount),
        backgroundColor: [CYAN, ORANGE, GREEN, AMBER, "#818CF8", "#F472B6", "#38BDF8", "#FB923C", "#4ADE80", "#FCD34D", "#A78BFA", "#F87171"],
        borderColor: "#121B2E", borderWidth: 2,
      }],
    },
    options: { plugins: { legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } } } },
  });

  const top = [...data.items].sort((a, b) => b.amount_inr - a.amount_inr).slice(0, 8);
  const topCtx = document.getElementById("chart-boq-top");
  charts.boqTop = new Chart(topCtx, {
    type: "bar",
    data: {
      labels: top.map(i => i.description.slice(0, 28) + (i.description.length > 28 ? "…" : "")),
      datasets: [{ data: top.map(i => i.amount_inr), backgroundColor: CYAN, borderRadius: 4 }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: GRID }, ticks: { callback: v => "₹" + (v / 100000).toFixed(1) + "L" } }, y: { grid: { display: false } } },
    },
  });

  document.getElementById("boq-search").addEventListener("input", e => {
    const q = e.target.value.toLowerCase();
    renderBOQTable(boqItemsCache.filter(i => i.description.toLowerCase().includes(q)));
  });
}

function renderBOQTable(items) {
  const table = document.getElementById("boq-table");
  const rows = items.map(i => `<tr>
      <td>${i.sl_no}</td><td>${i.description}</td><td>${i.unit}</td>
      <td class="num">${fmtNum(i.quantity, 2)}</td><td class="num">${fmtNum(i.rate_inr, 0)}</td>
      <td class="num">${fmtINR(i.amount_inr)}</td><td>${i.category}</td>
    </tr>`).join("");
  table.innerHTML = `<thead><tr><th>Sl.</th><th>Description</th><th>Unit</th><th>Qty</th><th>Rate</th><th>Amount</th><th>Category</th></tr></thead><tbody>${rows}</tbody>`;
}

// ---------------- Schedule ----------------
async function loadSchedule() {
  const sched = await fetch("/api/schedule").then(r => r.json());
  const acts = sched.activities;
  const startAll = new Date(acts[0].start_date);

  const ganttData = acts.map(a => {
    const s = (new Date(a.start_date) - startAll) / 86400000;
    const e = (new Date(a.end_date) - startAll) / 86400000 + 1;
    return { x: [s, e], y: a.activity };
  });

  const ctx = document.getElementById("chart-gantt");
  ctx.parentElement.style.height = Math.max(500, acts.length * 22) + "px";
  ctx.parentElement.style.minWidth = "700px";
  charts.gantt = new Chart(ctx, {
    type: "bar",
    data: { labels: acts.map(a => a.activity), datasets: [{ data: ganttData.map(d => d.x), backgroundColor: CYAN, borderRadius: 3, barThickness: 12 }] },
    options: {
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => "Day " + ctx.raw[0].toFixed(0) + " – " + ctx.raw[1].toFixed(0) } },
      },
      scales: {
        x: { title: { display: true, text: "Project Day" }, grid: { color: GRID } },
        y: { grid: { display: false }, ticks: { font: { size: 10 } } },
      },
    },
  });

  const daily = await fetch("/api/resources/daily").then(r => r.json());
  const rows = daily.rows;
  const step = Math.max(1, Math.floor(rows.length / 60));
  const sampled = rows.filter((_, i) => i % step === 0);

  charts.labour = new Chart(document.getElementById("chart-labour"), {
    type: "line",
    data: {
      labels: sampled.map(r => r.date),
      datasets: [
        { label: "Mason", data: sampled.map(r => r.mason), borderColor: ORANGE, tension: 0.3, pointRadius: 0 },
        { label: "Helper", data: sampled.map(r => r.helper), borderColor: CYAN, tension: 0.3, pointRadius: 0 },
      ],
    },
    options: { scales: { x: { ticks: { maxTicksLimit: 8 }, grid: { display: false } }, y: { grid: { color: GRID } } } },
  });

  charts.material = new Chart(document.getElementById("chart-material"), {
    type: "bar",
    data: { labels: sampled.map(r => r.date), datasets: [{ label: "Cement (bags)", data: sampled.map(r => r.cement_bags), backgroundColor: AMBER }] },
    options: { scales: { x: { ticks: { maxTicksLimit: 8 }, grid: { display: false } }, y: { grid: { color: GRID } } } },
  });

  renderResourceTable(rows);
  document.getElementById("schedule-date-filter").addEventListener("change", e => {
    const val = e.target.value;
    renderResourceTable(val ? rows.filter(r => r.date === val) : rows);
  });
}

function renderResourceTable(rows) {
  const table = document.getElementById("resource-table");
  const body = rows.slice(0, 300).map(r => `<tr>
      <td>${r.date}</td><td class="num">${r.mason}</td><td class="num">${r.helper}</td>
      <td class="num">${r.barbender}</td><td class="num">${r.carpenter}</td>
      <td class="num">${fmtNum(r.cement_bags, 1)}</td><td class="num">${fmtNum(r.steel_kg, 1)}</td>
      <td class="num">${fmtNum(r.sand_cum, 2)}</td><td class="num">${fmtNum(r.bricks_nos, 0)}</td>
    </tr>`).join("");
  table.innerHTML = `<thead><tr><th>Date</th><th>Mason</th><th>Helper</th><th>Bar Bender</th><th>Carpenter</th><th>Cement (bags)</th><th>Steel (kg)</th><th>Sand (cum)</th><th>Bricks</th></tr></thead><tbody>${body}</tbody>`;
}

// ---------------- Delay Risk ----------------
async function loadDelayMeta() {
  const meta = await fetch("/api/delay/meta").then(r => r.json());
  document.getElementById("model-acc").textContent = (meta.classifier_accuracy * 100).toFixed(1) + "%";
  document.getElementById("model-auc").textContent = meta.classifier_auc.toFixed(3);
  document.getElementById("model-mae").textContent = meta.regressor_mae_days.toFixed(1);
}

document.getElementById("btn-predict-delay").addEventListener("click", async () => {
  const payload = {
    planned_duration_days: +document.getElementById("in-duration").value,
    num_floors: +document.getElementById("in-floors").value,
    monsoon_exposure_days: +document.getElementById("in-monsoon").value,
    labour_availability_pct: +document.getElementById("in-labour").value,
    material_delay_risk: document.getElementById("in-material-risk").value,
    contractor_experience_years: +document.getElementById("in-contractor").value,
    site_accessibility_score: +document.getElementById("in-access").value,
    design_change_frequency: +document.getElementById("in-design").value,
    funding_regularity_score: +document.getElementById("in-funding").value,
    permit_delay_days: +document.getElementById("in-permit").value,
  };
  const res = await fetch("/api/delay/predict", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  }).then(r => r.json());

  document.getElementById("delay-result-empty").style.display = "none";
  document.getElementById("delay-result").style.display = "block";
  const probaEl = document.getElementById("delay-proba");
  probaEl.textContent = res.delay_probability_pct + "%";
  const bandEl = document.getElementById("delay-band");
  bandEl.textContent = res.risk_band + " Risk";
  const colorMap = { Low: GREEN, Medium: AMBER, High: RED };
  probaEl.style.color = colorMap[res.risk_band];
  bandEl.style.color = colorMap[res.risk_band];
  document.getElementById("delay-days").textContent = res.expected_delay_days + " days";

  if (charts.delayFactors) charts.delayFactors.destroy();
  charts.delayFactors = new Chart(document.getElementById("chart-delay-factors"), {
    type: "bar",
    data: {
      labels: res.top_factors.map(f => f.factor.replaceAll("_", " ")),
      datasets: [{ data: res.top_factors.map(f => f.importance), backgroundColor: ORANGE, borderRadius: 4 }],
    },
    options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { grid: { color: GRID } }, y: { grid: { display: false } } } },
  });
});

// ---------------- Cash Flow ----------------
async function loadCashflow() {
  const monthly = await fetch("/api/cashflow/monthly").then(r => r.json());
  const weekly = await fetch("/api/cashflow/weekly").then(r => r.json());

  charts.cfMonthly = new Chart(document.getElementById("chart-cashflow-monthly"), {
    data: {
      labels: monthly.rows.map(r => r.month),
      datasets: [
        { type: "bar", label: "Monthly Cost", data: monthly.rows.map(r => r.total_cost), backgroundColor: "rgba(79,209,232,0.55)", order: 2 },
        { type: "line", label: "Cumulative %", data: monthly.rows.map(r => r.cumulative_pct), borderColor: ORANGE, yAxisID: "y1", tension: 0.3, pointRadius: 3, order: 1 },
      ],
    },
    options: {
      scales: {
        y: { grid: { color: GRID }, title: { display: true, text: "Monthly Cost (₹)" } },
        y1: { position: "right", grid: { display: false }, ticks: { callback: v => v + "%" }, title: { display: true, text: "Cumulative %" } },
        x: { grid: { display: false } },
      },
    },
  });

  charts.cfWeekly = new Chart(document.getElementById("chart-cashflow-weekly"), {
    type: "bar",
    data: {
      labels: weekly.rows.map((r, i) => "W" + (i + 1)),
      datasets: [
        { label: "Material", data: weekly.rows.map(r => r.material_cost), backgroundColor: CYAN },
        { label: "Labour", data: weekly.rows.map(r => r.labour_cost), backgroundColor: ORANGE },
        { label: "Machinery", data: weekly.rows.map(r => r.machinery_cost), backgroundColor: GREEN },
      ],
    },
    options: { scales: { x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 12 } }, y: { stacked: true, grid: { color: GRID } } } },
  });

  const peakWeek = weekly.rows.reduce((a, b) => (b.total_cost > a.total_cost ? b : a));
  const peakMonth = monthly.rows.reduce((a, b) => (b.total_cost > a.total_cost ? b : a));
  document.getElementById("cashflow-peak-table").innerHTML = `
    <tr><td>Peak Week</td><td>${peakWeek.week_label} — ${fmtINR(peakWeek.total_cost)}</td></tr>
    <tr><td>Peak Month</td><td>${peakMonth.month} — ${fmtINR(peakMonth.total_cost)}</td></tr>
    <tr><td>Total Material Cost</td><td>${fmtINR(monthly.rows.reduce((s, r) => s + r.material_cost, 0))}</td></tr>
    <tr><td>Total Labour Cost</td><td>${fmtINR(monthly.rows.reduce((s, r) => s + r.labour_cost, 0))}</td></tr>
    <tr><td>Total Machinery Cost</td><td>${fmtINR(monthly.rows.reduce((s, r) => s + r.machinery_cost, 0))}</td></tr>
  `;

  const table = document.getElementById("cashflow-monthly-table");
  const rows = monthly.rows.map(r => `<tr>
      <td>${r.month}</td><td class="num">${fmtINR(r.material_cost)}</td><td class="num">${fmtINR(r.labour_cost)}</td>
      <td class="num">${fmtINR(r.machinery_cost)}</td><td class="num">${fmtINR(r.total_cost)}</td>
      <td class="num">${fmtINR(r.cumulative_cost)}</td><td class="num">${r.cumulative_pct}%</td>
    </tr>`).join("");
  table.innerHTML = `<thead><tr><th>Month</th><th>Material</th><th>Labour</th><th>Machinery</th><th>Total</th><th>Cumulative</th><th>Cum %</th></tr></thead><tbody>${rows}</tbody>`;
}

// Initial load
loadOverview();
