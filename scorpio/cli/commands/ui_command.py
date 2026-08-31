from .commands_types import CommandContract
from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host
import os
import threading
import webbrowser
from scorpio.server.config import SERVER_URL
from scorpio.server.main import run_server


class UICommand(CommandContract):
    def __init__(self, github_client: GithubContract):
        self.github_client = github_client
        self.NETWORK_URL = Host.get_network_url()

    def execute(self):
        directory, version = self.github_client.ensure_latest_release()
        print(f"Scorpio {version} instalado en {directory}")
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            threading.Timer(0.5, lambda: webbrowser.open(SERVER_URL)).start()
        else:
            print(f"Abre la interfaz desde otro equipo: {self.NETWORK_URL}")

        run_server()
