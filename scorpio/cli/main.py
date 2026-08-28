import argparse
import threading
import webbrowser


from scorpio.server.main import run_server
from scorpio.server.config import SERVER_URL
from scorpio.cli.check_last_release import install_latest_release


def main():
    parser = argparse.ArgumentParser(prog="scorpio")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("ui", help="Starts the web UI for Scorpio")

    args = parser.parse_args()

    if args.command == "ui":
        project_directory, version = install_latest_release()
        print(f"Scorpio {version} instalado en {project_directory}")
        threading.Timer(0.5, lambda: webbrowser.open(SERVER_URL)).start()
        run_server()


if __name__ == "__main__":
    main()
