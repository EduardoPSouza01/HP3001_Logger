import datetime as dt

from conftest import seed
from hp3001.services.collector import Collector


def test_save_query_count_filters(repo):
    seed(repo)
    assert repo.count() == 6
    assert repo.count(channel=5) == 3
    assert len(repo.query(channel=1, limit=2)) == 2
    assert repo.channels() == [1, 5]
    assert repo.query(start=dt.datetime.now() + dt.timedelta(days=1)) == []


def test_latest_and_stats(repo):
    seed(repo)
    latest = {r.channel: r for r in repo.latest_per_channel()}
    assert latest[1].temperature_c == 22.0 and latest[5].temperature_c == 27.0
    st = repo.stats_since(dt.datetime.now() - dt.timedelta(hours=1))
    assert st[1]["temp_min"] == 20.0 and st[1]["temp_max"] == 22.0


def test_collector_with_fake_device(repo):
    c = Collector(repo, "D1", 60, "fake")
    assert c.collect_once() == 2
    assert repo.count() == 2
    assert c.status["last_error"] is None
