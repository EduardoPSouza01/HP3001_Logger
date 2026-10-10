"""Versao desktop do HP3001.

  HP3001.exe               inicia a coleta em segundo plano (icone na bandeja) e abre o painel
  HP3001.exe --background  so coleta, sem abrir janela (usado na inicializacao do Windows)
  HP3001.exe --window      abre apenas a janela do painel (nao interfere na coleta)

Fechar a janela do painel NAO para a coleta. Para encerrar: icone da bandeja > Sair.
"""
import os
import socket
import subprocess
import sys
import threading
import webbrowser

from hp3001.config import ROOT, load_config

TITLE = "Termohigrometro HP3001"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "HP3001"


def _redirect_output_when_windowed():
    if sys.stdout is None or sys.stderr is None:
        log = open(os.path.join(ROOT, "hp3001.log"), "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log


def _port_in_use(host, port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _self_command(*args):
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    return [sys.executable, os.path.abspath(__file__), *args]


def open_window(url):
    try:
        import webview

        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.create_window(TITLE, url, width=1280, height=820, min_size=(900, 600))
        webview.start()
    except Exception:
        webbrowser.open(url)


def spawn_window():
    subprocess.Popen(_self_command("--window"), close_fds=True)


def autostart_enabled():
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
        return True
    except (ImportError, OSError):
        return False


def set_autostart(enabled):
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            cmd = subprocess.list2cmdline(_self_command("--background"))
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except OSError:
                pass


def _tray_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 4, 42, 44), 10, fill=(37, 99, 235, 255))
    d.ellipse((14, 34, 50, 62), fill=(37, 99, 235, 255))
    d.rectangle((29, 14, 35, 40), fill=(255, 255, 255, 255))
    d.ellipse((24, 38, 40, 54), fill=(220, 38, 38, 255))
    return img


def run_service(cfg, url, show_window):
    from werkzeug.serving import make_server

    from hp3001 import create_app

    app = create_app(cfg, start_collector=True)
    server = make_server(cfg.host, cfg.port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    collector = app.extensions["collector"]

    def shutdown():
        collector.stop()
        server.shutdown()

    try:
        import pystray
    except ImportError:
        if show_window:
            spawn_window()
        threading.Event().wait()
        return

    def on_open(icon, item):
        spawn_window()

    def on_toggle_autostart(icon, item):
        set_autostart(not autostart_enabled())

    def on_exit(icon, item):
        icon.stop()

    def tooltip():
        s = collector.status
        if s["last_error"]:
            return f"{TITLE} - erro de leitura"
        return f"{TITLE} - coletando a cada {s['interval_seconds']}s"

    menu = pystray.Menu(
        pystray.MenuItem("Abrir painel", on_open, default=True),
        pystray.MenuItem("Iniciar com o Windows", on_toggle_autostart,
                         checked=lambda item: autostart_enabled()),
        pystray.MenuItem("Sair (para a coleta)", on_exit),
    )
    icon = pystray.Icon("HP3001", _tray_image(), tooltip(), menu)

    def setup(ic):
        ic.visible = True
        if show_window:
            spawn_window()

    server_alive = threading.Event()
    server_alive.set()
    threading.Thread(target=lambda: _loop(icon, tooltip, server_alive), daemon=True).start()
    try:
        icon.run(setup)
    finally:
        server_alive.clear()
        shutdown()


def _loop(icon, tooltip, alive):
    import time

    while alive.is_set():
        try:
            icon.title = tooltip()
        except Exception:
            pass
        time.sleep(15)


def main():
    _redirect_output_when_windowed()
    cfg = load_config()
    url = f"http://{cfg.host}:{cfg.port}"
    args = set(sys.argv[1:])

    if "--window" in args:
        open_window(url)
        return

    if _port_in_use(cfg.host, cfg.port):
        # Ja esta coletando em segundo plano: so mostra o painel
        if "--background" not in args:
            spawn_window()
        return

    run_service(cfg, url, show_window="--background" not in args)


if __name__ == "__main__":
    main()
