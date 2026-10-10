import configparser
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PREFIX = "sqlite:///"
SETTINGS_FILE = os.path.join(ROOT, "settings.json")

MIN_INTERVAL = 1
MAX_INTERVAL = 7 * 24 * 3600


def validate_interval(value) -> int:
    """Converte para segundos inteiros; levanta ValueError se fora do limite."""
    if isinstance(value, bool):
        raise ValueError("intervalo invalido")
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        raise ValueError("intervalo invalido")
    if not MIN_INTERVAL <= seconds <= MAX_INTERVAL:
        raise ValueError("o intervalo deve ficar entre 1 segundo e 7 dias")
    return seconds


@dataclass
class Config:
    database_url: str = SQLITE_PREFIX + os.path.join(ROOT, "hp3001.db")
    device_name: str = "HP3001-01"
    interval_seconds: int = 60
    backend: str = "hid"
    autostart: bool = True
    host: str = "127.0.0.1"
    port: int = 5000
    channel_names: Dict[int, str] = field(default_factory=dict)
    settings_path: str = SETTINGS_FILE

    def channel_label(self, channel: int) -> str:
        return self.channel_names.get(channel, f"Canal {channel}")


def save_interval(settings_path: str, seconds: int):
    data = {}
    try:
        with open(settings_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        pass
    data["interval_seconds"] = seconds
    tmp = settings_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, settings_path)


def _saved_interval(settings_path: str):
    try:
        with open(settings_path, encoding="utf-8") as f:
            return validate_interval(json.load(f).get("interval_seconds"))
    except (OSError, ValueError, AttributeError):
        return None


def load_config(path: str = None, settings_path: str = None) -> Config:
    settings_path = settings_path or SETTINGS_FILE
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(path or os.path.join(ROOT, "config.ini"), encoding="utf-8")
    default = Config()

    url = cp.get("database", "url", fallback=default.database_url)
    if url.startswith(SQLITE_PREFIX) and not os.path.isabs(url[len(SQLITE_PREFIX):]):
        url = SQLITE_PREFIX + os.path.join(ROOT, url[len(SQLITE_PREFIX):])

    names = {}
    if cp.has_section("channels"):
        names = {int(k): v for k, v in cp.items("channels") if k.isdigit()}

    return Config(
        database_url=url,
        device_name=cp.get("logger", "device_name", fallback=default.device_name),
        interval_seconds=_saved_interval(settings_path)
        or cp.getint("logger", "interval_seconds", fallback=default.interval_seconds),
        backend=cp.get("logger", "backend", fallback=default.backend),
        autostart=cp.getboolean("logger", "autostart", fallback=default.autostart),
        host=cp.get("web", "host", fallback=default.host),
        port=cp.getint("web", "port", fallback=default.port),
        channel_names=names,
        settings_path=settings_path,
    )
