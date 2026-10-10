// Consulta o estado da coleta a cada 1s (resposta minima) e avisa as paginas
// quando chega uma leitura nova, qualquer que seja o intervalo configurado.
const readingListeners = [];
window.onNewReading = (fn) => readingListeners.push(fn);
let lastOk = null;

function notifyListeners() {
  readingListeners.forEach((fn) => { try { fn(); } catch (e) {} });
}

async function refreshStatus() {
  const el = document.getElementById("status");
  try {
    const s = await (await fetch("/api/status", { cache: "no-store" })).json();
    if (s.last_error) {
      el.textContent = "Erro de leitura";
      el.title = s.last_error;
      el.className = "status bad";
    } else if (s.running) {
      el.textContent = s.last_ok ? "Coletando" : "Iniciando...";
      el.title = s.last_ok ? "Ultima leitura: " + s.last_ok : "";
      el.className = "status ok";
    } else {
      el.textContent = "Coleta parada";
      el.title = "";
      el.className = "status";
    }
    if (s.last_ok && s.last_ok !== lastOk) {
      const first = lastOk === null;
      lastOk = s.last_ok;
      if (!first) notifyListeners();
    }
  } catch (e) {
    el.textContent = "Servidor offline";
    el.className = "status bad";
  }
}

refreshStatus();
setInterval(() => { if (!document.hidden) refreshStatus(); }, 1000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) notifyListeners(); });
