from __future__ import annotations

import json
import re

from ..remote_executor import RemoteExecutor


class StatusManager:
    """Read the remote Docker Compose status."""

    def __init__(self, executor: RemoteExecutor) -> None:
        self.executor = executor

    def get_docker_compose_status(self) -> dict:
        """Return a frontend-friendly infrastructure status snapshot."""
        if not self.executor.is_connected:
            return self._status()

        command = (
            "cd ~/.local/share/scorpio/Scorpio-Project && "
            "docker compose -f deploy/docker-compose.yml ps --all --format json"
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
                compose_data if isinstance(compose_data, list) else [compose_data]
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
                service["state"].lower() == "running" for service in normalized_services
            )

            return {
                "running": running_count > 0,
                "services": normalized_services,
            }
        except (ConnectionError, RuntimeError, OSError, json.JSONDecodeError):
            return self._status()

    @staticmethod
    def _parse_output(output: str) -> list | dict:
        """Support Compose output as either an array or JSON lines."""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return [json.loads(line) for line in output.splitlines() if line.strip()]

    @staticmethod
    def _status() -> dict:
        return {
            "running": False,
            "services": [],
        }
