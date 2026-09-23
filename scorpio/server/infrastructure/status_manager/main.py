from __future__ import annotations

import json
import re

import requests

from scorpio.cli.host.host import Host

from ..remote_executor import RemoteExecutor
from ..storage_handler import StorageHandler


class StatusManager:
    """Read the remote Docker Compose status."""

    def __init__(
        self, executor: RemoteExecutor, storage_handler: StorageHandler
    ) -> None:
        self.executor = executor
        self.storage_handler = storage_handler

    def get_docker_compose_status(self) -> dict:
        """Return a frontend-friendly infrastructure status snapshot."""
        if not self.executor.is_connected:
            return self._status()

        command = (
            "cd ~/.local/share/scorpio/Scorpio-Project && "
            "docker compose -f deploy/docker-compose.yml "
            "ps --all --format json"
        )

        try:
            output = "".join(self.executor.stream(command))
            cleaned_output = re.sub(
                r"\\x1b\\[[0-9;]*[A-Za-z]",
                "",
                output,
            ).strip()
            if not cleaned_output:
                return self._status()

            compose_data = self._parse_output(cleaned_output)
            services = (
                compose_data
                if isinstance(compose_data, list)
                else [compose_data]
            )
            normalized_services = [
                {
                    "name": service.get("Service") or service.get("Name"),
                    "state": service.get("State", "unknown"),
                    "status": service.get("Status", ""),
                }
                for service in services
                if isinstance(service, dict)
            ]
            running_count = sum(
                service["state"].lower() == "running"
                for service in normalized_services
            )

            return {
                "running": running_count > 0,
                "services": normalized_services,
            }
        except (ConnectionError, RuntimeError, OSError, json.JSONDecodeError):
            return self._status()

    def get_pypi_last_version(self) -> dict:
        URL = "https://pypi.org/pypi/scorpio-cli/json"
        storage_data = self.storage_handler.get()
        setup = storage_data.get("setup")
        versions = setup.get("version") if isinstance(setup, dict) else None
        stored_version = (
            versions.get("scorpio_cli") if isinstance(versions, dict) else None
        )
        installed_version = Host.get_package_version("scorpio-cli")
        current_version = installed_version or stored_version or "unknown"

        try:
            # Get the latest version and release date from PyPI
            response = requests.get(URL, timeout=5)
            response.raise_for_status()
            latest_version = (
                response.json().get("info", {}).get("version", "unknown")
            )
            releases = response.json().get("releases", {})
            details = (
                releases.get(latest_version, [])[0]
                if releases.get(latest_version)
                else {}
            )
            upload_time = details.get("upload_time_iso_8601") or details.get(
                "upload_time", "unknown"
            )
            need_to_update = (
                bool(current_version)
                and latest_version != "unknown"
                and current_version != latest_version
            )

            return {
                "current_version": current_version,
                "latest_version": latest_version,
                "upload_time": upload_time,
                "need_to_update": need_to_update,
            }
        except (requests.RequestException, json.JSONDecodeError) as error:
            return {
                "current_version": current_version or "unknown",
                "latest_version": "unknown",
                "upload_time": "unknown",
                "need_to_update": False,
                "error": f"Unable to check PyPI: {error}",
            }

    @staticmethod
    def _parse_output(output: str) -> list | dict:
        """Support Compose output as either an array or JSON lines."""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return [
                json.loads(line)
                for line in output.splitlines()
                if line.strip()
            ]

    @staticmethod
    def _status() -> dict:
        return {
            "running": False,
            "services": [],
        }
