from __future__ import annotations

from datetime import datetime
import re

from .types import DockerLog
from scorpio.cli.host.host import Host

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def parse_docker_log(line: str) -> DockerLog | None:
    """Parse the pipe-delimited format emitted by Scorpio services."""
    line = ANSI_ESCAPE.sub("", line).strip()
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
    formatted_timestamp = _format_timestamp(timestamp)

    level = fields[1] if len(fields) > 1 and fields[1] else None
    layer = fields[2] if len(fields) > 2 and fields[2] else None
    message = fields[3] if len(fields) > 3 else (fields[-1] if fields else "")

    return DockerLog(
        service=service.strip(),
        timestamp=formatted_timestamp,
        level=level,
        layer=layer,
        message=message,
    )


def _format_timestamp(timestamp: str | None) -> str | None:
    """Format the timestamp to a more readable format."""
    if not timestamp:
        return None
    try:
        date = timestamp.split(" ")[1]
        time = timestamp.split(" ")[2]
        timezone = Host.get_local_timezone()
        timestamp = f"{date} {time}"
        parsed_timestamp = datetime.fromisoformat(timestamp)
        if parsed_timestamp.tzinfo is None:
            parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone)
        else:
            parsed_timestamp = parsed_timestamp.astimezone(timezone)
        return parsed_timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
