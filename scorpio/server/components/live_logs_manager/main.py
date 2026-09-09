from __future__ import annotations

from collections.abc import Iterator

from ..remote_executor import RemoteExecutor
from .types import DockerLog
from .utils import parse_docker_log


class LiveLogsManager:
    def __init__(self, executor: RemoteExecutor) -> None:
        self.executor = executor

    def stream(self) -> Iterator[dict]:
        """Yield one serializable event dict for every Docker log line."""
        command = (
            "cd ~/.local/share/scorpio/Scorpio-Project && "
            "docker compose -f deploy/docker-compose.yml "
            "logs -f --no-color --timestamps"
        )

        for line in self.executor.stream(command):
            parsed = parse_docker_log(line)
            if parsed is not None:
                yield {"type": "log", "source": "docker", "data": parsed.to_dict()}

    @staticmethod
    def parse(line: str) -> DockerLog | None:
        return parse_docker_log(line)
