"""Linha de comando (alternativa ao painel web).

  python logger.py collect [--once] [--backend hid|usb|fake]
  python logger.py list [--start 2026-01-01] [--end 2026-01-31] [--channel 1]
  python logger.py export arquivo.xlsx [--start ...] [--end ...] [--channel N]

Obs.: nao rode "collect" junto com "app.py": o equipamento so aceita um leitor por vez.
"""
import argparse
import dataclasses
import datetime as dt
import sys
import time

from hp3001.config import load_config
from hp3001.models.reading import get_engine
from hp3001.models.repository import ReadingRepository
from hp3001.services.collector import Collector
from hp3001.services.exporter import build_xlsx


def _date(s, end_of_day=False):
    if not s:
        return None
    d = dt.datetime.fromisoformat(s)
    return d + dt.timedelta(days=1) if end_of_day and len(s) <= 10 else d


def _filters(a):
    return dict(start=_date(a.start), end=_date(a.end, True), channel=a.channel)


def cmd_collect(a, cfg, repo):
    cfg = dataclasses.replace(cfg, backend=a.backend or cfg.backend)
    c = Collector(repo, cfg.device_name, cfg.interval_seconds, cfg.backend)
    try:
        while True:
            try:
                print(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} - {c.collect_once()} leituras salvas", flush=True)
            except Exception as e:
                print(f"erro na leitura/gravacao: {e}", file=sys.stderr, flush=True)
            if a.once:
                break
            time.sleep(cfg.interval_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        c.close()


def cmd_list(a, cfg, repo):
    for r in repo.query(**_filters(a)):
        print(f"{r.recorded_at}  {r.device_name}  {cfg.channel_label(r.channel)}  "
              f"{r.temperature_c:.1f} C  {r.humidity}%")


def cmd_export(a, cfg, repo):
    rows = repo.query(**_filters(a))
    with open(a.file, "wb") as f:
        f.write(build_xlsx(rows, cfg.channel_label))
    print(f"{len(rows)} linhas exportadas para {a.file}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect")
    c.add_argument("--once", action="store_true")
    c.add_argument("--backend", choices=["hid", "usb", "fake"])
    c.set_defaults(fn=cmd_collect)

    for name, fn in (("list", cmd_list), ("export", cmd_export)):
        s = sub.add_parser(name)
        if name == "export":
            s.add_argument("file")
        s.add_argument("--start")
        s.add_argument("--end")
        s.add_argument("--channel", type=int)
        s.set_defaults(fn=fn)

    a = p.parse_args()
    cfg = load_config()
    a.fn(a, cfg, ReadingRepository(get_engine(cfg.database_url)))


if __name__ == "__main__":
    main()
