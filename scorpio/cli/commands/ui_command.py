from .commands_types import CommandContract
from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host
import os
import json
import threading
import webbrowser
from scorpio.server.config import SERVER_URL
from scorpio.cli.config import STORAGE_PATH
from scorpio.server.main import run_server
import logging

logger = logging.getLogger(__name__)


class UICommand(CommandContract):
    def __init__(
        self, github_client: GithubContract, execute_command=None
    ):
        self.github_client = github_client
        self.NETWORK_URL = Host.get_network_url()

    def execute(self):
        directory, version = self.github_client.ensure_latest_release()
        logger.info(f"Scorpio {version} installed in {directory}")

        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            threading.Timer(0.5, lambda: webbrowser.open(SERVER_URL)).start()
        else:
            print(f"Open the Scorpio web interface in this device: {self.NETWORK_URL}")

        run_server(self.github_client)
