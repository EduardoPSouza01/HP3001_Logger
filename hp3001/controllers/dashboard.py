import datetime as dt

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from ..config import save_interval, validate_interval
from ..models.reading import row_to_dict
from ..services import exporter

bp = Blueprint("dashboard", __name__)
PAGE_SIZE = 50


def _repo():
    return current_app.extensions["repo"]


def _config():
    return current_app.extensions["config"]


def _date(value, end_of_day=False):
    try:
        d = dt.datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    return d + dt.timedelta(days=1) if end_of_day else d


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _filters():
    return dict(
        start=_date(request.args.get("start")),
        end=_date(request.args.get("end"), end_of_day=True),
        channel=_int(request.args.get("channel")),
    )


@bp.route("/")
def index():
    return render_template("dashboard.html", interval=_config().interval_seconds)


@bp.route("/history")
def history():
    f = _filters()
    page = max(_int(request.args.get("page"), 1), 1)
    total = _repo().count(**f)
    pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = min(page, pages)
    rows = _repo().query(**f, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE, newest_first=True)
    args = {k: v for k, v in request.args.items() if k != "page" and v}
    return render_template(
        "history.html", rows=rows, total=total, page=page, pages=pages, args=args,
        channels=_repo().channels(), label=_config().channel_label,
        start=request.args.get("start", ""), end=request.args.get("end", ""),
        channel=f["channel"],
    )


@bp.route("/api/latest")
def api_latest():
    cfg = _config()
    stats = _repo().stats_since(dt.datetime.now() - dt.timedelta(hours=24))
    items = []
    for row in _repo().latest_per_channel():
        item = row_to_dict(row)
        item["name"] = cfg.channel_label(row.channel)
        item["stats_24h"] = stats.get(row.channel, {})
        items.append(item)
    return jsonify(items)


@bp.route("/api/series")
def api_series():
    hours = min(max(_int(request.args.get("hours"), 24), 1), 24 * 30)
    since = dt.datetime.now() - dt.timedelta(hours=hours)
    series = {}
    for row in _repo().query(start=since):
        series.setdefault(row.channel, []).append(
            {"t": row.recorded_at.isoformat(sep=" "), "temp": row.temperature_c, "hum": row.humidity})
    cfg = _config()
    return jsonify([{"channel": ch, "name": cfg.channel_label(ch), "points": pts}
                    for ch, pts in sorted(series.items())])


@bp.route("/settings")
def settings():
    return render_template("settings.html", interval=_config().interval_seconds)


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    cfg = _config()
    if request.method == "POST":
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="envie JSON"), 415
        try:
            seconds = validate_interval(payload.get("interval_seconds"))
        except ValueError as e:
            return jsonify(error=str(e)), 400
        try:
            save_interval(cfg.settings_path, seconds)
        except OSError as e:
            return jsonify(error=f"nao foi possivel salvar: {e}"), 500
        cfg.interval_seconds = seconds
        current_app.extensions["collector"].set_interval(seconds)
    return jsonify(interval_seconds=cfg.interval_seconds)


@bp.route("/api/status")
def api_status():
    return jsonify(current_app.extensions["collector"].status)


@bp.route("/export.xlsx")
def export():
    rows = _repo().query(**_filters())
    data = exporter.build_xlsx(rows, _config().channel_label)
    name = f"leituras_{dt.datetime.now():%Y%m%d_%H%M%S}.xlsx"
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={name}"},
    )
