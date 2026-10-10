import datetime as dt

import pytest

from hp3001 import create_app
from hp3001.config import Config
from hp3001.models.reading import get_engine
from hp3001.models.repository import ReadingRepository
from hp3001.services.protocol import Sample


@pytest.fixture
def repo(tmp_path):
    return ReadingRepository(get_engine(f"sqlite:///{tmp_path / 't.db'}"))


@pytest.fixture
def client(tmp_path):
    cfg = Config(database_url=f"sqlite:///{tmp_path / 'w.db'}", backend="fake",
                 channel_names={1: "Camara"}, settings_path=str(tmp_path / "settings.json"))
    app = create_app(cfg)
    app.testing = True
    return app.test_client(), app.extensions["repo"]


def seed(repo, n=3):
    now = dt.datetime.now().replace(microsecond=0)
    for i in range(n):
        repo.save("D1", [Sample(1, 20.0 + i, 50), Sample(5, 25.0 + i, 60)],
                  when=now - dt.timedelta(minutes=n - i))
