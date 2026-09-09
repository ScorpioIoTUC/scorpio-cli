import queue
import json
import sys
import threading
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
from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host
from datetime import datetime
from .components.setup_manager.main import SetupManager
from .components.live_logs_manager import LiveLogsManager
from .components.remote_executor import RemoteExecutor

# Logger configs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Handler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        github_client: GithubContract,
        setup_manager: SetupManager,
        live_logs_manager: LiveLogsManager,
        remote_executor: RemoteExecutor,
        **kwargs,
    ):
        self.github_client = github_client
        self.remote_executor = remote_executor
        self.setup_manager = setup_manager
        self.live_logs_manager = live_logs_manager
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

    def _ssh_login(self, body: dict) -> tuple[dict, HTTPStatus]:
        username = body.get("username")
        password = body.get("password")
        hostname = body.get("hostname")
        if not username or not password or not hostname:
            return {
                "error": "Missing required fields: username, password, and hostname are required."
            }, HTTPStatus.BAD_REQUEST

        try:
            self.remote_executor.connect(hostname, username, password)
            self._ssh_set_is_active(hostname, username, password)

        except ConnectionError as e:
            return {"error": str(e)}, HTTPStatus.UNAUTHORIZED

        # For demonstration purposes, we'll just return a success message.
        return {"message": f"SSH login successful for user {username}."}, HTTPStatus.OK

    def _ssh_logout(self) -> tuple[dict, HTTPStatus]:
        storage = self._get_storage()
        if not storage.get("ssh") or not storage["ssh"].get("is_active"):
            return {"error": "No active SSH session found."}, HTTPStatus.BAD_REQUEST
        self._ssh_reset()
        self.remote_executor.close()
        return {"message": "SSH logout successful."}, HTTPStatus.OK

    def _setup_is_completed(self) -> bool:
        storage = self._get_storage()
        if storage.get("setup") is None:
            return False

        setup_completed = storage["setup"].get("completed", False)
        return setup_completed

    def _get_setup_status(self) -> dict:
        """Return the live state enriched with the persisted installation state."""
        status = self.setup_manager.get_status()
        storage = self._get_storage()
        persisted_setup = storage.get("setup") or {}

        if persisted_setup.get("completed"):
            status["status"] = "completed"
            status["completedAt"] = persisted_setup.get("completedAt")
            status["timezone"] = persisted_setup.get("timezone")
            status["version"] = persisted_setup.get("version")

        return status

    def _scorpio_setup(self, body: dict) -> tuple[dict, HTTPStatus]:
        current_status = self.setup_manager.get_status()["status"]
        if current_status == "running":
            return {
                "error": "Scorpio setup is already in progress."
            }, HTTPStatus.CONFLICT

        if self._setup_is_completed():
            return {
                "error": "Scorpio setup has already been completed."
            }, HTTPStatus.BAD_REQUEST

        started = self.setup_manager.start(
            executor=self.remote_executor,
            command=("cd ~/.local/share/scorpio/Scorpio-Project && make setup-all"),
            on_success=self._mark_setup_as_completed,
        )

        if not started:
            return {"error": "Unable to start Scorpio setup."}, HTTPStatus.CONFLICT

        return {
            "message": "Scorpio setup started.",
            "status": "running",
        }, HTTPStatus.ACCEPTED

    def _mark_setup_as_completed(self) -> None:
        storage = self._get_storage()
        scorpio_proj_version = self.github_client.get_latest_release().version
        scorpio_cli_version = Host.get_package_version("scorpio-cli")
        timezone = Host.get_local_timezone()

        storage["setup"] = {
            "completed": True,
            "completedAt": datetime.now(tz=timezone).isoformat(),
            "timezone": str(timezone),
            "version": {
                "scorpio_project": scorpio_proj_version,
                "scorpio_cli": scorpio_cli_version,
            },
        }
        self._update_storage(storage)

    def _send_live_logs(self):
        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", UI_URL)
            self.end_headers()

            for event in self.live_logs_manager.stream():
                self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
                self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError, RuntimeError):
            # The generator's finally block closes docker compose logs -f.
            pass

    def _stop_scorpio(self) -> tuple[dict, HTTPStatus]:
        try:
            self._execute_remote("make stop")
            return {"message": "Scorpio stopped."}, HTTPStatus.OK
        except Exception as e:
            logging.error("Error stopping Scorpio: %s", e)
            return {
                "error": "Failed to stop Scorpio."
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def _start_scorpio(self) -> tuple[dict, HTTPStatus]:
        try:
            self._execute_remote("make start")
            return {"message": "Scorpio started."}, HTTPStatus.OK
        except Exception as e:
            logging.error("Error starting Scorpio: %s", e)
            return {
                "error": "Failed to start Scorpio."
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    def _execute_remote(self, command: str) -> None:
        remote_command = f"cd ~/.local/share/scorpio/Scorpio-Project && {command}"
        for _ in self.remote_executor.stream(remote_command):
            pass

    def _reboot(self) -> tuple[dict, HTTPStatus]:
        if not self.remote_executor.is_connected:
            return {"error": "No active SSH connection."}, HTTPStatus.BAD_REQUEST

        def reboot_remote_host() -> None:
            try:
                for _ in self.remote_executor.stream("sudo reboot"):
                    pass
            except (ConnectionError, RuntimeError, OSError):
                pass

        threading.Thread(target=reboot_remote_host, daemon=True).start()
        return {"message": "Raspberry Pi reboot requested."}, HTTPStatus.ACCEPTED

    def do_GET(self):
        if self.path == "/version":
            self.send_json(self._get_system_version())
        elif self.path == "/scorpio/setup/status":
            self.send_json(self._get_setup_status())
        elif self.path == "/scorpio/setup/events":
            self._send_setup_events()

        elif self.path == "/scorpio/stop":
            self.send_json(*self._stop_scorpio())

        elif self.path == "/scorpio/start":
            self.send_json(*self._start_scorpio())

        elif self.path == "/scorpio/logs/live":
            self._send_live_logs()

        else:
            super().do_GET()

    def do_POST(self):
        body = self._body()
        if self.path == "/ssh/login":
            self.send_json(*self._ssh_login(body))
        elif self.path == "/ssh/logout":
            self.send_json(*self._ssh_logout())
        elif self.path == "/scorpio/setup":
            self.send_json(*self._scorpio_setup(body))
        elif self.path == "/scorpio/reboot":
            self.send_json(*self._reboot())
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
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

    def _send_setup_events(self):
        subscriber = self.setup_manager.subscribe()

        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", UI_URL)
            self.end_headers()

            # Permite al frontend conocer inmediatamente el estado actual.
            initial_status = {
                "type": "status",
                "data": self._get_setup_status(),
            }

            self.wfile.write(f"data: {json.dumps(initial_status)}\n\n".encode("utf-8"))
            self.wfile.flush()

            while True:
                try:
                    log = subscriber.get(timeout=15)

                    if log is None:
                        final_status = {
                            "type": "status",
                            "data": self._get_setup_status(),
                        }

                        self.wfile.write(
                            f"data: {json.dumps(final_status)}\n\n".encode("utf-8")
                        )
                        self.wfile.flush()
                        break
                    event = {"type": "log", "data": log.to_dict()}
                    self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
                    self.wfile.flush()

                except queue.Empty:
                    # Heartbeat to keep the connection alive
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError):
            pass

        finally:
            self.setup_manager.unsubscribe(subscriber)


def ensure_server_storage():
    if not SERVER_STORAGE_PATH.parent.exists():
        SERVER_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SERVER_STORAGE_PATH.exists():
        with open(SERVER_STORAGE_PATH, "w") as f:
            json.dump(SERVER_STORAGE_INIT_DATA, f, indent=4)


class ScorpioHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type in (ConnectionResetError, BrokenPipeError):
            return
        if exc_type is RuntimeError and "Remote command failed with code -1" in str(exc_value):
            return
        super().handle_error(request, client_address)


def run_server(github_client: GithubContract):
    ensure_server_storage()

    setup_manager = SetupManager()
    remote_executor = RemoteExecutor()
    live_logs_manager = LiveLogsManager(remote_executor)

    handler = partial(
        Handler,
        github_client=github_client,
        setup_manager=setup_manager,
        live_logs_manager=live_logs_manager,
        remote_executor=remote_executor,
    )
    logging.info("Server started at %s", SERVER_URL)

    ScorpioHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
