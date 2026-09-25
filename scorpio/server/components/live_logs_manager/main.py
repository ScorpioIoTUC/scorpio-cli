from __future__ import annotations

from collections.abc import Iterator

from ..remote_executor import RemoteExecutor
from .types import DockerLog
from .utils import parse_docker_log


class LiveLogsManager:
    def __init__(self, executor: RemoteExecutor) -> None:
        self.executor = executor

    def stream(self, include_debug: bool = False) -> Iterator[dict]:
        """Yield one serializable event dict for every Docker log line."""
        command = (
            "cd ~/.local/share/scorpio/Scorpio-Project && "
            "docker compose -f deploy/docker-compose.yml "
            "logs -f --tail=200 --no-color --timestamps"
        )

        for line in self.executor.stream(command):
            parsed = parse_docker_log(line)
            if parsed is not None and (
                include_debug or (parsed.level or "").lower() != "debug"
            ):
                yield {"type": "log", "source": "docker", "data": parsed.to_dict()}

    @staticmethod
    def parse(line: str) -> DockerLog | None:
        return parse_docker_log(line)
