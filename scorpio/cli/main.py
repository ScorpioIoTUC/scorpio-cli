import argparse
import os
import subprocess
import threading
import webbrowser

from scorpio.cli.config import ALLOWED_TARGETS, COMMAND_DESCRIPTIONS
from scorpio.cli.check_last_release import (
    ensure_latest_release,
    ensure_project_installed,
)
from scorpio.cli.get_hostname_data import get_local_ip
from scorpio.server.config import SERVER_URL
from scorpio.server.main import run_server


def confirm_reset():
    print("WARNING: this will stop Scorpio and delete its Docker volumes.")
    print("MQTT data, MQTT logs, and the SQLite database will be permanently removed.")
    try:
        confirmation = input("Type 'reset' to continue: ")
    except (EOFError, KeyboardInterrupt):
        print("\nReset cancelled.")
        return False

    if confirmation.strip().lower() != "reset":
        print("Reset cancelled.")
        return False
    return True


def main():
    local_ip = get_local_ip()
    network_url = f"http://{local_ip}:8000"
    parser = argparse.ArgumentParser(prog="scorpio")
    subcommands = parser.add_subparsers(dest="command", required=True)
    # Add subcommand for ui initialization
    subcommands.add_parser(
        "ui",
        help="Start the Scorpio setup web interface.",
        description="Start the local Scorpio setup server and web interface.",
    )
    # Add subcommands for manual configuration
    for command in ALLOWED_TARGETS:
        description = COMMAND_DESCRIPTIONS[command]
        subcommands.add_parser(
            command,
            help=description,
            description=description,
        )
    args = parser.parse_args()

    if args.command == "ui":
        project_directory, version = ensure_latest_release()
        print(f"Scorpio {version} instalado en {project_directory}")
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            threading.Timer(0.5, lambda: webbrowser.open(SERVER_URL)).start()
        else:
            print(f"Abre la interfaz desde otro equipo: {network_url}")
        run_server()
    elif args.command in ALLOWED_TARGETS:
        if args.command == "reset" and not confirm_reset():
            return

        project_directory, _ = ensure_project_installed()
        target = ALLOWED_TARGETS[args.command]
        subprocess.run(
            ["make", target],
            cwd=project_directory,
            check=True,
        )


if __name__ == "__main__":
    main()
