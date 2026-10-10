import datetime as dt
import threading
import time

from . import device


class Collector:
    """Le o equipamento periodicamente e grava no repositorio (thread em segundo plano)."""

    def __init__(self, repo, device_name, interval_seconds, backend="hid"):
        self.repo = repo
        self.device_name = device_name
        self.interval = interval_seconds
        self.backend = backend
        self._dev = None
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._status = {"running": False, "last_ok": None, "last_error": None, "last_count": 0}

    @property
    def status(self) -> dict:
        with self._lock:
            s = dict(self._status)
        s["running"] = bool(self._thread and self._thread.is_alive())
        s["interval_seconds"] = self.interval
        s["backend"] = self.backend
        return s

    def collect_once(self) -> int:
        try:
            if self._dev is None:
                self._dev = device.open_device(self.backend)
            samples = device.read_with_retry(self._dev)
            n = self.repo.save(self.device_name, samples)
        except Exception as e:
            self.close()
            with self._lock:
                self._status["last_error"] = f"{dt.datetime.now():%d/%m/%Y %H:%M:%S} - {e}"
            raise
        with self._lock:
            self._status.update(last_ok=dt.datetime.now().isoformat(sep=" ", timespec="seconds"),
                                last_count=n, last_error=None)
        return n

    def close(self):
        if self._dev is not None:
            try:
                self._dev.close()
            except Exception:
                pass
            self._dev = None

    def set_interval(self, seconds: int):
        """Aplica o novo intervalo na hora, sem reiniciar a coleta."""
        self.interval = seconds
        self._wake.set()

    def _run(self):
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                self.collect_once()
            except Exception:
                pass
            while not self._stop.is_set():
                remaining = started + self.interval - time.monotonic()
                if remaining <= 0:
                    break
                self._wake.wait(remaining)
                self._wake.clear()
        self.close()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="collector", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
