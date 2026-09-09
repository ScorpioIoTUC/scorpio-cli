from __future__ import annotations

from datetime import datetime

from .types import DockerLog


def parse_docker_log(line: str) -> DockerLog | None:
    """Parse the pipe-delimited format emitted by Scorpio services."""
    line = line.strip()
    if not line:
        return None

    service, separator, payload = line.partition("|")
    if not separator:
        return DockerLog(
            service="unknown",
            timestamp=None,
            level=None,
            layer=None,
            message=line,
        )

    fields = [field.strip() for field in payload.split("|", 3)]
    timestamp = fields[0] if fields else None
    if timestamp:
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            timestamp = None

    level = fields[1] if len(fields) > 1 and fields[1] else None
    layer = fields[2] if len(fields) > 2 and fields[2] else None
    message = fields[3] if len(fields) > 3 else (fields[-1] if fields else "")

    return DockerLog(
        service=service.strip(),
        timestamp=timestamp,
        level=level,
        layer=layer,
        message=message,
    )
