"""Behavioral coverage for HTTP, application boundaries and side effects."""

import io
import json
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scorpio.server.application.contracts.result import Outcome
from scorpio.server.application.use_cases.discord import DiscordUseCases
from scorpio.server.application.use_cases.infrastructure import (
    InfrastructureUseCases,
)
from scorpio.server.application.use_cases.setup import SetupUseCases
from scorpio.server.application.use_cases.ssh import SshUseCases
from scorpio.server.application.use_cases.token import TokenUseCases
from scorpio.server.application.use_cases.update import UpdateUseCases
from scorpio.server.application.use_cases.version import VersionUseCases
from scorpio.server.http.controllers import Controllers
from scorpio.server.http.handler import Handler
from scorpio.server.infrastructure.local_environment import (
    LocalTokenEnvironment,
)


class MemorySocket:
    """Exercise the real request parser and response writer without networking."""

    def __init__(self, method, path, body):
        payload = json.dumps(body).encode() if body is not None else b""
        self.input = io.BytesIO(
            f"{method} {path} HTTP/1.0\r\nContent-Length: {len(payload)}\r\n\r\n".encode()
            + payload
        )
        self.output = bytearray()

    def makefile(self, *args):
        return self.input

    def sendall(self, data):
        self.output.extend(data)


class ServerBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "ssh": {"is_active": True},
            "docker_infra": {"status": "running"},
        }
        self.storage = Mock()
        self.storage.get.side_effect = lambda: self.data
        self.storage.update.side_effect = self.replace_storage
        self.remote = Mock(is_connected=True)
        self.remote.stream.return_value = iter([])
        self.jobs = Mock()
        self.jobs.get_status.return_value = {"status": "idle", "logs": []}
        self.jobs.start.return_value = True
        self.status = Mock()
        self.status.get_pypi_last_version.return_value = {
            "current_version": "1.0",
            "latest_version": "1.0",
        }
        self.releases = Mock()
        self.releases.get_latest_release.return_value = SimpleNamespace(
            version="v1.0"
        )
        self.host = Mock()
        self.host.get_package_version.return_value = "1.0"
        self.delivery = Mock()
        self.delivery.send.return_value = None
        self.environment = Mock()
        self.installer = Mock()
        self.controllers = Controllers(
            ssh=SshUseCases(self.storage, self.remote),
            setup=SetupUseCases(
                self.storage,
                self.remote,
                self.jobs,
                self.status,
                self.releases,
                self.host,
            ),
            infrastructure=InfrastructureUseCases(self.storage, self.remote),
            token=TokenUseCases(self.storage, self.environment),
            update=UpdateUseCases(
                self.storage, self.status, self.host, self.installer
            ),
            version=VersionUseCases(self.releases, self.host),
            discord=DiscordUseCases(self.storage, self.delivery),
        )
        self.logs = Mock()
        self.logs.stream.return_value = iter([])

    def replace_storage(self, data):
        self.data = data

    def request(self, method, path, body=None):
        socket = MemorySocket(method, path, body)
        Handler(
            socket,
            ("127.0.0.1", 1234),
            Mock(),
            controllers=self.controllers,
            setup_manager=self.jobs,
            live_logs_manager=self.logs,
        )
        head, payload = bytes(socket.output).split(b"\r\n\r\n", 1)
        code = int(head.split(b" ", 2)[1])
        return code, head, payload

    def json_request(self, method, path, body=None):
        code, head, payload = self.request(method, path, body)
        self.assertIn(b"Content-Type: application/json", head)
        self.assertIn(b"Access-Control-Allow-Origin:", head)
        self.assertIn(f"Content-Length: {len(payload)}".encode(), head)
        return code, json.loads(payload)

    def test_json_endpoint_contracts(self):
        cases = [
            (
                "GET",
                "/version",
                None,
                200,
                {"scorpio_cli": "1.0", "scorpio_project": "v1.0"},
            ),
            (
                "POST",
                "/ssh/login",
                {},
                400,
                {
                    "error": "Missing required fields: username, password, and hostname are required."
                },
            ),
            (
                "POST",
                "/ssh/login",
                {"hostname": "pi", "username": "user", "password": "secret"},
                200,
                {"message": "SSH login successful for user user."},
            ),
            (
                "POST",
                "/ssh/logout",
                {},
                200,
                {"message": "SSH logout successful."},
            ),
            (
                "POST",
                "/ssh/logout",
                {},
                400,
                {"error": "No active SSH session found."},
            ),
            (
                "POST",
                "/scorpio/setup",
                {},
                202,
                {"message": "Scorpio setup started.", "status": "running"},
            ),
            (
                "GET",
                "/scorpio/stop",
                None,
                200,
                {"message": "Scorpio stopped."},
            ),
            (
                "GET",
                "/scorpio/start",
                None,
                200,
                {"message": "Scorpio started."},
            ),
            (
                "GET",
                "/scorpio/setup/token",
                None,
                404,
                {"error": "Setup token not found."},
            ),
            (
                "POST",
                "/scorpio/setup/token",
                {"api_url": "https://api.test", "token": "token"},
                200,
                {"message": "Setup token updated."},
            ),
            (
                "GET",
                "/scorpio/setup/token",
                None,
                200,
                {"api_url": "https://api.test", "token": "token"},
            ),
            (
                "GET",
                "/scorpio/update",
                None,
                200,
                {"current_version": "1.0", "latest_version": "1.0"},
            ),
            (
                "POST",
                "/scorpio/update",
                {},
                200,
                {
                    "message": "Scorpio CLI is already up to date.",
                    "previous_version": "1.0",
                    "installed_version": "1.0",
                    "restart_required": False,
                },
            ),
            (
                "GET",
                "/discord/settings",
                None,
                200,
                {
                    "configured": False,
                    "channels": {},
                    "error_alert_gap_minutes": 5,
                },
            ),
            (
                "POST",
                "/discord/setup",
                {"token": " token "},
                200,
                {"message": "Discord token updated.", "configured": True},
            ),
            (
                "POST",
                "/discord/set-channel",
                {"tag": "errors", "channel_id": "42"},
                200,
                {
                    "message": "Discord channel updated.",
                    "channels": {"errors": "42"},
                },
            ),
            (
                "POST",
                "/discord/set-alert-gap",
                {"minutes": 8},
                200,
                {"message": "Discord alert interval updated.", "minutes": 8},
            ),
            (
                "POST",
                "/discord/notify",
                {"message": "hello", "tag": "errors"},
                200,
                {"message": "Discord notification sent.", "tag": "errors"},
            ),
            (
                "POST",
                "/discord/remove",
                {},
                200,
                {
                    "message": "Discord configuration removed.",
                    "configured": False,
                },
            ),
        ]
        for method, path, body, code, expected in cases:
            with self.subTest(method=method, path=path):
                self.assertEqual(
                    self.json_request(method, path, body), (code, expected)
                )
        self.environment.update.assert_called_once_with(
            "https://api.test", "token"
        )
        self.delivery.send.assert_called_once_with("token", "42", "hello")
        self.installer.upgrade.assert_not_called()

    def test_persisted_setup_status_and_start_conflicts(self):
        self.data["setup"] = {
            "completed": True,
            "completedAt": "2026-01-01",
            "version": {"scorpio_cli": "1.0"},
            "timezone": "UTC",
        }
        code, status = self.json_request("GET", "/scorpio/setup/status")
        self.assertEqual(code, 200)
        self.assertEqual(
            status,
            {
                "status": "completed",
                "logs": [],
                "ssh_active": True,
                "completedAt": "2026-01-01",
                "version": {"scorpio_cli": "1.0"},
                "timezone": "UTC",
                "infrastructure": {"status": "running"},
            },
        )
        self.assertEqual(
            self.json_request("POST", "/scorpio/setup", {})[0], 400
        )
        self.jobs.get_status.return_value = {"status": "running"}
        self.assertEqual(
            self.json_request("POST", "/scorpio/setup", {})[0], 409
        )
        self.jobs.start.assert_not_called()

    def test_setup_command_keeps_release_pinning_and_callback(self):
        self.json_request("POST", "/scorpio/setup", {})
        args = self.jobs.start.call_args.kwargs
        self.assertIs(args["executor"], self.remote)
        self.assertIn("git clone --depth 1 --branch v1.0", args["command"])
        self.assertIn("refs/tags/v1.0", args["command"])
        self.assertTrue(
            args["command"].endswith("make setup-host && make setup-docker")
        )
        self.assertTrue(callable(args["on_success"]))

    def test_ssh_connection_error_does_not_persist(self):
        self.remote.connect.side_effect = ConnectionError("Denied")
        self.assertEqual(
            self.json_request(
                "POST",
                "/ssh/login",
                {
                    "hostname": "pi",
                    "username": "user",
                    "password": "secret",
                },
            ),
            (401, {"error": "Denied"}),
        )
        self.storage.update.assert_not_called()

    def test_remote_commands_and_reboot(self):
        self.json_request("GET", "/scorpio/start")
        self.remote.stream.assert_called_with(
            "cd ~/.local/share/scorpio/Scorpio-Project && make start"
        )
        self.assertEqual(self.data["docker_infra"]["status"], "running")
        with patch(
            "scorpio.server.application.use_cases.infrastructure.threading.Thread"
        ) as thread:
            self.assertEqual(
                self.json_request("POST", "/scorpio/reboot", {}),
                (202, {"message": "Raspberry Pi reboot requested."}),
            )
            self.remote.stream.side_effect = ConnectionError("Disconnected")
            thread.call_args.kwargs["target"]()
            self.remote.close.assert_called_once()
            self.assertFalse(self.data["ssh"]["is_active"])
        self.remote.is_connected = False
        self.assertEqual(
            self.json_request("POST", "/scorpio/reboot", {})[0], 400
        )

    def test_sse_status_log_heartbeat_final_status_and_cleanup(self):
        subscriber = Mock()
        log = Mock()
        log.to_dict.return_value = {"message": "step completed"}
        subscriber.get.side_effect = [queue.Empty, log, None]
        self.jobs.subscribe.return_value = subscriber
        code, headers, body = self.request("GET", "/scorpio/setup/events")
        self.assertEqual(code, 200)
        self.assertIn(b"Content-Type: text/event-stream", headers)
        self.assertIn(b": heartbeat\n\n", body)
        events = [
            json.loads(line[6:])
            for line in body.splitlines()
            if line.startswith(b"data: ")
        ]
        self.assertEqual(
            [event["type"] for event in events], ["status", "log", "status"]
        )
        self.assertEqual(events[1]["data"], {"message": "step completed"})
        self.jobs.unsubscribe.assert_called_once_with(subscriber)
        self.remote.close.assert_not_called()

    def test_sse_disconnect_unsubscribes_without_closing_ssh(self):
        subscriber = Mock()
        subscriber.get.side_effect = BrokenPipeError
        self.jobs.subscribe.return_value = subscriber
        self.request("GET", "/scorpio/setup/events")
        self.jobs.unsubscribe.assert_called_once_with(subscriber)
        self.remote.close.assert_not_called()

    def test_live_logs_keep_existing_event_shape(self):
        event = {
            "type": "log",
            "source": "docker",
            "data": {"message": "ready"},
        }
        self.logs.stream.return_value = iter([event])
        code, _, body = self.request("GET", "/scorpio/logs/live")
        self.assertEqual(code, 200)
        self.assertEqual(body, f"data: {json.dumps(event)}\n\n".encode())
        self.remote.close.assert_not_called()

    def test_unknown_routes_and_static_files(self):
        self.assertEqual(self.request("POST", "/missing", {})[0], 404)
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text("<h1>Scorpio</h1>")
            with patch("scorpio.server.http.handler.UI_DIR", Path(directory)):
                code, _, body = self.request("GET", "/")
        self.assertEqual((code, body), (200, b"<h1>Scorpio</h1>"))

    def test_token_validation_has_no_side_effects(self):
        self.assertEqual(
            self.json_request("POST", "/scorpio/setup/token", {})[0], 400
        )
        self.environment.update.assert_not_called()
        self.storage.update.assert_not_called()

    def test_local_environment_preserves_other_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("OTHER=keep=me\nSCORPIO_API_TOKEN=old\n")
            LocalTokenEnvironment(Path(directory)).update(
                "https://api.test", "new"
            )
            self.assertEqual(
                path.read_text(),
                "OTHER=keep=me\nSCORPIO_API_TOKEN=new\nSCORPIO_API_URL=https://api.test\n",
            )

    def test_discord_delivery_failure_maps_to_bad_gateway(self):
        self.data["discord"] = {
            "auth_token": "token",
            "channels": {"errors": "42"},
        }
        self.delivery.send.return_value = "Could not connect to Discord."
        self.assertEqual(
            self.json_request(
                "POST",
                "/discord/notify",
                {"message": "hello", "tag": "errors"},
            ),
            (502, {"error": "Could not connect to Discord."}),
        )
        self.assertEqual(
            self.controllers.discord.set_alert_gap(0)[1], Outcome.BAD_REQUEST
        )
