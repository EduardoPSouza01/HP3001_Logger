"""Inicia o painel web + coleta automatica.  Acesse http://localhost:5000

  python app.py                  # usa o equipamento real
  python app.py --backend fake   # dados simulados (teste)
"""
import argparse
import dataclasses

from hp3001 import create_app
from hp3001.config import load_config


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["hid", "usb", "fake"])
    p.add_argument("--no-collect", action="store_true", help="so visualizar, sem ler o equipamento")
    args = p.parse_args()

    cfg = load_config()
    if args.backend:
        cfg = dataclasses.replace(cfg, backend=args.backend)
    app = create_app(cfg, start_collector=cfg.autostart and not args.no_collect)
    print(f"Painel: http://{cfg.host}:{cfg.port}  (Ctrl+C para parar)")
    app.run(host=cfg.host, port=cfg.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
