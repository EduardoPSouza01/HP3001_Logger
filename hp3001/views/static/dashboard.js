const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#db2777", "#4b5563"];
const cardsEl = document.getElementById("cards");
let intervalSec = Number(cardsEl.dataset.interval) || 60;
let chartTemp, chartHum;

const fmt1 = (v) => (v === null || v === undefined ? "-" : Number(v).toFixed(1));
const fmtDate = (s) => new Date(s.replace(" ", "T")).toLocaleString("pt-BR");
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function loadLatest() {
  try {
    intervalSec = (await (await fetch("/api/settings")).json()).interval_seconds || intervalSec;
  } catch (e) {}
  const items = await (await fetch("/api/latest")).json();
  if (!items.length) {
    cardsEl.innerHTML = '<p class="muted">Ainda nao ha leituras gravadas.</p>';
    return;
  }
  cardsEl.innerHTML = items.map((i) => {
    const age = (Date.now() - new Date(i.recorded_at.replace(" ", "T"))) / 1000;
    const stale = age > intervalSec * 3 + 30;
    const s = i.stats_24h || {};
    return `<div class="card ${stale ? "stale" : ""}">
      <h3>${esc(i.name)}</h3>
      <div class="row">
        <div class="big">${fmt1(i.temperature_c)}<small> &deg;C</small></div>
        <div class="big">${i.humidity ?? "-"}<small> %</small></div>
      </div>
      <div class="meta">
        Atualizado: ${fmtDate(i.recorded_at)}${stale ? " (desatualizado)" : ""}<br>
        24h: temp ${fmt1(s.temp_min)} a ${fmt1(s.temp_max)} &deg;C (media ${fmt1(s.temp_avg)})<br>
        24h: umid ${fmt1(s.hum_min)} a ${fmt1(s.hum_max)} % (media ${fmt1(s.hum_avg)})
      </div>
    </div>`;
  }).join("");
}

function buildChart(canvasId, series, key) {
  const labels = [...new Set(series.flatMap((s) => s.points.map((p) => p.t)))].sort();
  const datasets = series.map((s, idx) => {
    const byTime = new Map(s.points.map((p) => [p.t, p[key]]));
    return {
      label: s.name,
      data: labels.map((t) => byTime.get(t) ?? null),
      borderColor: COLORS[idx % COLORS.length],
      backgroundColor: COLORS[idx % COLORS.length],
      pointRadius: 0,
      borderWidth: 2,
      tension: 0.2,
      spanGaps: true,
    };
  });
  return new Chart(document.getElementById(canvasId), {
    type: "line",
    data: { labels: labels.map(fmtDate), datasets },
    options: {
      animation: false,
      interaction: { mode: "index", intersect: false },
      scales: { x: { ticks: { maxTicksLimit: 8 } } },
    },
  });
}

let chartsLoading = false;
async function loadCharts() {
  if (chartsLoading) return;
  chartsLoading = true;
  try {
    const hours = document.getElementById("hours").value;
    const series = await (await fetch("/api/series?hours=" + hours)).json();
    if (chartTemp) chartTemp.destroy();
    if (chartHum) chartHum.destroy();
    chartTemp = buildChart("chartTemp", series, "temp");
    chartHum = buildChart("chartHum", series, "hum");
  } finally {
    chartsLoading = false;
  }
}

document.getElementById("hours").addEventListener("change", loadCharts);
loadLatest();
loadCharts();

// Atualiza a cada leitura nova; os graficos no maximo a cada 3s (intervalos curtos)
let lastCharts = 0;
window.onNewReading(() => {
  loadLatest();
  if (Date.now() - lastCharts >= 3000) {
    lastCharts = Date.now();
    loadCharts();
  }
});
setInterval(() => { if (!document.hidden) loadLatest(); }, 30000);
