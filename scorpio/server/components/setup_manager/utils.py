from .types import SetupLog
from datetime import datetime, timezone
import re


ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

_ERROR_WORDS = ("error", "failed", "failure", "denied", "not found")
_DOCKER_BUILD_PREFIXES = ("#", "=>", "dockerfile:", "load build", "exporting ")


def parse_setup_log(line: str) -> SetupLog | None:
    line = ANSI_ESCAPE.sub("", line).strip()
    if "log:" in line and not line.startswith("log:"):
        line = line[line.index("log:") :]
    if not line.startswith("log:"):
        return None
    parts = line.split(":", 5)

    if len(parts) != 6:
        return None
    _, level, module, section, step_data, message = parts
    step = None
    total_steps = None
    step_id = None

    if section == "step":
        if "/" in step_data:
            current_step, total = step_data.split("/", 1)
            try:
                step = int(current_step)
                total_steps = int(total)
            except ValueError:
                pass
        message_parts = message.split(":", 1)
        if len(message_parts) == 2:
            step_id, message = message_parts
        else:
            step_id = step_data
    else:
        step_id = step_data
    return SetupLog(
        level=level,
        module=module,
        step=step,
        total_steps=total_steps,
        step_id=step_id,
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def clean_setup_line(line: str) -> str:
    """Remove terminal control codes from command output."""
    return ANSI_ESCAPE.sub("", line).strip()


def is_error_output(line: str) -> bool:
    """Keep actionable errors even while noisy output is suppressed."""
    lowered = line.lower()
    return any(word in lowered for word in _ERROR_WORDS)


def is_docker_build_output(line: str) -> bool:
    """Identify Docker BuildKit progress that is not useful in the UI."""
    lowered = line.lower().lstrip()
    return lowered.startswith(_DOCKER_BUILD_PREFIXES) or " dockerfile" in lowered


def infer_setup_layer(line: str, current_layer: str) -> str:
    """Assign a useful layer to unstructured setup command output."""
    lowered = line.lower()
    if any(value in lowered for value in ("apt ", "apt-get", "package", "dpkg")):
        return "system_packages"
    if any(value in lowered for value in ("git ", "cloning", "fetch", "checkout")):
        return "source"
    if any(value in lowered for value in ("docker compose", "container ", "network ")):
        return "docker_compose"
    if any(value in lowered for value in ("cmake", "make[", "building ")):
        return "build"
    return current_layer or "setup"
