const $ = (id) => document.getElementById(id);
const MAX = 7 * 24 * 3600;

function human(sec) {
  const units = [[86400, "dia", "dias"], [3600, "hora", "horas"], [60, "minuto", "minutos"], [1, "segundo", "segundos"]];
  const parts = [];
  for (const [size, one, many] of units) {
    const n = Math.floor(sec / size);
    if (n > 0) { parts.push(`${n} ${n === 1 ? one : many}`); sec -= n * size; }
  }
  return parts.join(" e ");
}

function currentSeconds() {
  if ($("preset").value !== "custom") return Number($("preset").value);
  return Math.round(Number($("customValue").value) * Number($("customUnit").value));
}

function refresh() {
  $("customBox").hidden = $("preset").value !== "custom";
  const s = currentSeconds();
  const ok = Number.isFinite(s) && s >= 1 && s <= MAX;
  $("save").disabled = !ok;
  $("summary").textContent = ok ? "Uma leitura a cada " + human(s) + "." : "Informe um valor entre 1 segundo e 7 dias.";
  const perDay = ok ? 86400 / s : 0;
  const warn = $("warn");
  warn.hidden = !(ok && perDay > 5000);
  if (!warn.hidden) {
    warn.textContent = `Atencao: isso grava cerca de ${Math.round(perDay).toLocaleString("pt-BR")} leituras por canal por dia e o banco cresce rapido.`;
  }
}

function select(seconds) {
  const opt = [...$("preset").options].find((o) => o.value === String(seconds));
  if (opt) { $("preset").value = String(seconds); return; }
  $("preset").value = "custom";
  const units = [86400, 3600, 60, 1];
  const u = units.find((x) => seconds % x === 0) || 1;
  $("customUnit").value = String(u);
  $("customValue").value = seconds / u;
}

async function save() {
  const msg = $("msg");
  msg.className = "msg";
  msg.textContent = "Salvando...";
  try {
    const r = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interval_seconds: currentSeconds() }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "erro");
    msg.className = "msg ok";
    msg.textContent = "Salvo. Intervalo atual: " + human(data.interval_seconds) + ".";
  } catch (e) {
    msg.className = "msg bad";
    msg.textContent = "Erro: " + e.message;
  }
}

["preset", "customValue", "customUnit"].forEach((id) => $(id).addEventListener("input", refresh));
$("save").addEventListener("click", save);
select(window.CURRENT_INTERVAL);
refresh();
