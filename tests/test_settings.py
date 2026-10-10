import json
import time

import pytest

from hp3001.config import load_config, validate_interval
from hp3001.services.collector import Collector


def test_settings_page_and_get(client):
    c, _ = client
    assert c.get("/settings").status_code == 200
    assert c.get("/api/settings").get_json() == {"interval_seconds": 60}


@pytest.mark.parametrize("seconds", [1, 10, 1800, 3600, 86400, 7 * 86400])
def test_save_valid_interval_applies_and_persists(client, seconds):
    c, _ = client
    r = c.post("/api/settings", json={"interval_seconds": seconds})
    assert r.status_code == 200 and r.get_json()["interval_seconds"] == seconds
    assert c.get("/api/status").get_json()["interval_seconds"] == seconds
    path = c.application.extensions["config"].settings_path
    assert json.load(open(path))["interval_seconds"] == seconds


@pytest.mark.parametrize("bad", [0, -5, 7 * 86400 + 1, "abc", None, True, 1.5e30])
def test_save_invalid_interval_rejected(client, bad):
    c, _ = client
    r = c.post("/api/settings", json={"interval_seconds": bad})
    assert r.status_code == 400
    assert c.get("/api/settings").get_json()["interval_seconds"] == 60


def test_post_requires_json(client):
    c, _ = client
    assert c.post("/api/settings", data="interval_seconds=5").status_code == 415


def test_saved_interval_overrides_config_ini(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({"interval_seconds": 900}))
    ini = tmp_path / "c.ini"
    ini.write_text("[logger]\ninterval_seconds = 5\n")
    cfg = load_config(str(ini), str(s))
    assert cfg.interval_seconds == 900 and cfg.settings_path == str(s)


def test_corrupt_settings_file_falls_back(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text("{nao e json")
    ini = tmp_path / "c.ini"
    ini.write_text("[logger]\ninterval_seconds = 5\n")
    assert load_config(str(ini), str(s)).interval_seconds == 5


def test_validate_interval_bounds():
    assert validate_interval("30") == 30
    with pytest.raises(ValueError):
        validate_interval(0)


def test_collector_applies_new_interval_without_restart(repo):
    c = Collector(repo, "D1", 3600, "fake")
    c.start()
    try:
        time.sleep(0.5)
        assert repo.count() == 2  # uma leitura inicial, depois espera 1 h
        c.set_interval(1)
        deadline = time.time() + 5
        while repo.count() < 4 and time.time() < deadline:
            time.sleep(0.1)
        assert repo.count() >= 4
    finally:
        c.stop()
