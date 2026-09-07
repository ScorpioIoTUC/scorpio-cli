from collections.abc import Callable
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from http import HTTPStatus
import logging
from scorpio.server.config import (
    PORT,
    SERVER_URL,
    UI_URL,
    UI_DIR,
    SERVER_STORAGE_PATH,
    SERVER_STORAGE_INIT_DATA,
)
from scorpio.cli.clients.ssh.ssh_client import SSHClient
from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host
from datetime import datetime

# Logger configs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Handler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        github_client: GithubContract,
        execute_command: Callable[[str], None],
        **kwargs,
    ):
        self.github_client = github_client
        self.execute_command = execute_command
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def _body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        return json.loads(body) if body else {}

    def _get_default(self) -> dict:
        return {"message": "Welcome to the Scorpio setup server."}

    def _get_storage(self) -> dict:
        if not SERVER_STORAGE_PATH.exists():
            return {}
        with open(SERVER_STORAGE_PATH, "r") as f:
            return json.load(f)

    def _update_storage(self, data: dict):
        with open(SERVER_STORAGE_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def _get_system_version(self) -> dict:
        scorpio_latest_release = self.github_client.get_latest_release()
        return {
            "scorpio_cli": Host.get_package_version("scorpio-cli"),
            "scorpio_project": scorpio_latest_release.version,
        }

    def _ssh_set_is_active(self, hostname: str, username: str, password: str):
        storage_data = self._get_storage()
        if not storage_data.get("ssh"):
            storage_data["ssh"] = {}

        storage_data["ssh"]["is_active"] = True
        storage_data["ssh"]["hostname"] = hostname
        storage_data["ssh"]["username"] = username
        storage_data["ssh"]["password"] = password
        self._update_storage(storage_data)

    def _ssh_reset(self):
        storage_data = self._get_storage()
        storage_data["ssh"]["is_active"] = False
        storage_data["ssh"]["hostname"] = ""
        storage_data["ssh"]["username"] = ""
        storage_data["ssh"]["password"] = ""
        self._update_storage(storage_data)

    def _ssh_login(self, body: dict) -> dict:
        username = body.get("username")
        password = body.get("password")
        hostname = body.get("hostname")
        if not username or not password or not hostname:
            return {
                "error": "Missing required fields: username, password, and hostname are required."
            }

        ssh_client = SSHClient(hostname=hostname, username=username, password=password)
        try:
            ssh_client.connect()
            self._ssh_set_is_active(hostname, username, password)

        except ConnectionError as e:
            return {"error": str(e)}

        # For demonstration purposes, we'll just return a success message.
        return {"message": f"SSH login successful for user {username}."}

    def _ssh_logout(self) -> tuple[dict, HTTPStatus]:
        storage = self._get_storage()
        if not storage.get("ssh") or not storage["ssh"].get("is_active"):
            return {"error": "No active SSH session found."}, HTTPStatus.BAD_REQUEST
        self._ssh_reset()
        return {"message": "SSH logout successful."}, HTTPStatus.OK

    def _setup_is_completed(self) -> bool:
        storage = self._get_storage()
        if storage.get("setup") is None:
            return False

        setup_completed = storage["setup"].get("completed", False)
        return setup_completed

    def _scorpio_setup(self, body: dict) -> tuple[dict, HTTPStatus]:
        if self._setup_is_completed():
            return {
                "error": "Scorpio setup has already been completed."
            }, HTTPStatus.BAD_REQUEST

        self.execute_command("setup")

        storage = self._get_storage()
        scorpio_proj_version = self.github_client.get_latest_release().version
        scorpio_cli_version = Host.get_package_version("scorpio-cli")
        timezone = Host.get_local_timezone()
        completed_at = datetime.now(tz=Host.get_local_timezone()).isoformat()
        storage["setup"] = {
            "completed": True,
            "completedAt": completed_at,
            "timezone": str(timezone),
            "version": {
                "scoprio_project": scorpio_proj_version,
                "scorpio_cli": scorpio_cli_version,
            },
        }
        self._update_storage(storage)

        return {"message": "Scorpio setup completed successfully."}, HTTPStatus.OK

    def do_GET(self):
        if self.path == "/version":
            self.send_json(self._get_system_version())
        else:
            super().do_GET()

    def do_POST(self):
        body = self._body()
        if self.path == "/ssh/login":
            response = self._ssh_login(body)
            status = (
                HTTPStatus.OK if "error" not in response else HTTPStatus.BAD_REQUEST
            )
            self.send_json(response, status=status)
        elif self.path == "/ssh/logout":
            response, status = self._ssh_logout()
            self.send_json(response, status=status)

        elif self.path == "/scorpio/setup":
            response, status = self._scorpio_setup(body)
            self.send_json(response, status=status)

        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", UI_URL)
        super().end_headers()


def ensure_server_storage():
    if not SERVER_STORAGE_PATH.parent.exists():
        SERVER_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SERVER_STORAGE_PATH.exists():
        with open(SERVER_STORAGE_PATH, "w") as f:
            json.dump(SERVER_STORAGE_INIT_DATA, f, indent=4)


def run_server(github_client: GithubContract, execute_command: Callable[[str], None]):
    ensure_server_storage()
    handler = partial(
        Handler, github_client=github_client, execute_command=execute_command
    )
    logging.info("Server started at %s", SERVER_URL)

    ThreadingHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
