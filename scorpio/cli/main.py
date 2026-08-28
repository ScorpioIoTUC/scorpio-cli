import argparse
import threading
import webbrowser
import os

from scorpio.server.main import run_server
from scorpio.server.config import SERVER_URL
from scorpio.cli.check_last_release import install_latest_release
from scorpio.cli.get_hostname_data import get_local_ip

def main():
    local_ip = get_local_ip()
    network_url = f"http://{local_ip}:8000"
    parser = argparse.ArgumentParser(prog="scorpio")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("ui", help="Starts the web UI for Scorpio")

    args = parser.parse_args()

    if args.command == "ui":
        project_directory, version = install_latest_release()
        print(f"Scorpio {version} instalado en {project_directory}")       

        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            threading.Timer(
                0.5,
                lambda: webbrowser.open(SERVER_URL)
            ).start()
        else:
            print(f"Abre la interfaz desde otro equipo: {network_url}")

        run_server()


if __name__ == "__main__":
    main()
