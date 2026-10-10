from flask import Flask

from .config import Config, load_config
from .controllers.dashboard import bp
from .models.reading import get_engine
from .models.repository import ReadingRepository
from .services.collector import Collector


def create_app(config: Config = None, start_collector: bool = False) -> Flask:
    config = config or load_config()
    app = Flask(__name__, template_folder="views/templates", static_folder="views/static")

    repo = ReadingRepository(get_engine(config.database_url))
    collector = Collector(repo, config.device_name, config.interval_seconds, config.backend)

    app.extensions["config"] = config
    app.extensions["repo"] = repo
    app.extensions["collector"] = collector
    app.register_blueprint(bp)

    if start_collector:
        collector.start()
    return app
