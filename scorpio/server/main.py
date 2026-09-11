import queue
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from http import HTTPStatus
import logging
import shlex
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
from .components.storage_handler import StorageHandler
from .components.status_manager import StatusManager
from .components.discord_handler import DiscordHandler

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
        storage_handler: StorageHandler,
        status_manager: StatusManager,
        discord_handler: DiscordHandler,
        **kwargs,
    ):
        self.github_client = github_client
        self.remote_executor = remote_executor
        self.setup_manager = setup_manager
        self.live_logs_manager = live_logs_manager
        self.storage_handler = storage_handler
        self.status_manager = status_manager
        self.discord_handler = discord_handler
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def _body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        return json.loads(body) if body else {}

    def _get_default(self) -> dict:
        return {"message": "Welcome to the Scorpio setup server."}

    def _get_system_version(self) -> dict:
        scorpio_latest_release = self.github_client.get_latest_release()
        return {
            "scorpio_cli": Host.get_package_version("scorpio-cli"),
            "scorpio_project": scorpio_latest_release.version,
        }

    def _ssh_set_is_active(self, hostname: str, username: str, password: str):
        storage_data = self.storage_handler.get()
        if not storage_data.get("ssh"):
            storage_data["ssh"] = {}

        storage_data["ssh"]["is_active"] = True
        storage_data["ssh"]["hostname"] = hostname
        storage_data["ssh"]["username"] = username
        storage_data["ssh"]["password"] = password
        self.storage_handler.update(storage_data)

    def _ssh_reset(self):
        storage_data = self.storage_handler.get()
        storage_data["ssh"]["is_active"] = False
        storage_data["ssh"]["hostname"] = ""
        storage_data["ssh"]["username"] = ""
        storage_data["ssh"]["password"] = ""
        self.storage_handler.update(storage_data)

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
        storage = self.storage_handler.get()
        if not storage.get("ssh") or not storage["ssh"].get("is_active"):
            return {"error": "No active SSH session found."}, HTTPStatus.BAD_REQUEST
        self._ssh_reset()
        self.remote_executor.close()
        return {"message": "SSH logout successful."}, HTTPStatus.OK

    def _setup_is_completed(self) -> bool:
        storage = self.storage_handler.get()
        if storage.get("setup") is None:
            return False

        setup_completed = storage["setup"].get("completed", False)
        return setup_completed

    def _get_setup_status(self) -> dict:
        """Return the live state enriched with the persisted installation state."""
        status = self.setup_manager.get_status()
        status["ssh_active"] = self.remote_executor.is_connected
        storage = self.storage_handler.get()
        persisted_setup = storage.get("setup") or {}

        if persisted_setup.get("completed"):
            status["status"] = "completed"
            status["completedAt"] = persisted_setup.get("completedAt")
            status["timezone"] = persisted_setup.get("timezone")
            status["version"] = persisted_setup.get("version")

        # status["infrastructure"] = self.status_manager.get_docker_compose_status()
        docker_infra_status = (
            self.storage_handler.get().get("docker_infra", {}).get("status", "unknown")
        )
        if docker_infra_status == "unknown":
            docker_status = self.status_manager.get_docker_compose_status()
            docker_infra_status = docker_status.get("running", False)
            docker_infra_status = "running" if docker_infra_status else "stopped"
            status["infrastructure"] = {"status": docker_infra_status}
        else:
            status["infrastructure"] = {"status": docker_infra_status}

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

        try:
            latest_release = self.github_client.get_latest_release()
        except Exception as error:
            return {
                "error": f"Unable to determine the latest Scorpio release: {error}"
            }, HTTPStatus.BAD_GATEWAY

        release_tag = shlex.quote(latest_release.version)
        project_dir = "~/.local/share/scorpio/Scorpio-Project"

        started = self.setup_manager.start(
            executor=self.remote_executor,
            command=(
                "mkdir -p ~/.local/share/scorpio && "
                f"if [ ! -d {project_dir}/.git ]; then "
                "git clone --depth 1 --branch "
                f"{release_tag} https://github.com/ScorpioIoTUC/Scorpio-Project.git "
                f"{project_dir}; "
                "else "
                f"git -C {project_dir} fetch --depth 1 origin refs/tags/{release_tag} && "
                f"git -C {project_dir} checkout --force FETCH_HEAD; "
                "fi && "
                f"cd {project_dir} && make setup-all"
            ),
            on_success=self._mark_setup_as_completed,
        )

        if not started:
            return {"error": "Unable to start Scorpio setup."}, HTTPStatus.CONFLICT

        return {
            "message": "Scorpio setup started.",
            "status": "running",
        }, HTTPStatus.ACCEPTED

    def _mark_setup_as_completed(self) -> None:
        storage = self.storage_handler.get()
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
        self.storage_handler.update(storage)

    def _send_live_logs(self):
        # Check if the ssh client is active
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
        except (BrokenPipeError, ConnectionResetError, ConnectionError, RuntimeError):
            # Closing one SSE client must not close the shared SSH session.
            return

    def _stop_scorpio(self) -> tuple[dict, HTTPStatus]:
        try:
            self._execute_remote("make stop")
            # Store this informatio in the storage
            storage = self.storage_handler.get()
            storage["docker_infra"]["status"] = "stopped"
            self.storage_handler.update(storage)
            return {"message": "Scorpio stopped."}, HTTPStatus.OK
        except Exception as e:
            logging.error("Error stopping Scorpio: %s", e)
            return {
                "error": "Failed to stop Scorpio."
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    
    def _close_connection(self) -> None:
        """Close the SSH connection and update the storage to reflect that the connection is no longer active."""
        self.remote_executor.close()
        storage = self.storage_handler.get()
        storage.setdefault("ssh", {})["is_active"] = False
        self.storage_handler.update(storage)
    
    def _start_scorpio(self) -> tuple[dict, HTTPStatus]:
        try:
            self._execute_remote("make start")
            # Store this information in the storage
            storage = self.storage_handler.get()
            storage["docker_infra"]["status"] = "running"
            self.storage_handler.update(storage)
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
                # The connection will be closed when the Raspberry Pi reboots.
                self._close_connection()

        threading.Thread(target=reboot_remote_host, daemon=True).start()
        return {"message": "Raspberry Pi reboot requested."}, HTTPStatus.ACCEPTED

    def do_GET(self):
        # Get endpoints
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

        elif self.path == "/discord/settings":
            self.send_json(self.discord_handler.get_settings())

        else:
            super().do_GET()

    def do_POST(self):
        # Post endpoints
        body = self._body()
        if self.path == "/ssh/login":
            self.send_json(*self._ssh_login(body))
        elif self.path == "/ssh/logout":
            self.send_json(*self._ssh_logout())
        elif self.path == "/scorpio/setup":
            self.send_json(*self._scorpio_setup(body))
        elif self.path == "/scorpio/reboot":
            self.send_json(*self._reboot())
        elif self.path == "/discord/setup":
            self.send_json(*self.discord_handler.setup(body.get("token")))
        elif self.path == "/discord/set-channel":
            self.send_json(*self.discord_handler.set_channel(
                body.get("tag"), body.get("channel_id")
            ))
        elif self.path == "/discord/set-alert-gap":
            self.send_json(*self.discord_handler.set_alert_gap(body.get("minutes")))
        elif self.path == "/discord/remove":
            self.send_json(*self.discord_handler.remove())
        elif self.path == "/discord/notify":
            self.send_json(*self.discord_handler.notify(
                body.get("message"), body.get("tag")
            ))
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


class ScorpioHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type in (ConnectionResetError, BrokenPipeError):
            return
        if exc_type is RuntimeError and "Remote command failed with code -1" in str(
            exc_value
        ):
            return
        super().handle_error(request, client_address)


def run_server(github_client: GithubContract):
    storage_handler = StorageHandler.get_instance(
        path=SERVER_STORAGE_PATH,
        initial_data=SERVER_STORAGE_INIT_DATA,
    )
    storage_handler.create()

    setup_manager = SetupManager()
    remote_executor = RemoteExecutor(storage_handler=storage_handler)
    live_logs_manager = LiveLogsManager(remote_executor)
    status_manager = StatusManager(remote_executor)
    discord_handler = DiscordHandler(storage_handler)

    handler = partial(
        Handler,
        github_client=github_client,
        setup_manager=setup_manager,
        live_logs_manager=live_logs_manager,
        remote_executor=remote_executor,
        storage_handler=storage_handler,
        status_manager=status_manager,
        discord_handler=discord_handler,
    )
    logging.info("Server started at %s", SERVER_URL)

    ScorpioHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
