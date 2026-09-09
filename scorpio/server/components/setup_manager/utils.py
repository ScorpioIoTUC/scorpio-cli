from .types import SetupLog
from datetime import datetime, timezone
import re


ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def parse_setup_log(line: str) -> SetupLog | None:
    line = ANSI_ESCAPE.sub("", line).strip()
    if "log:" in line and not line.startswith("log:"):
        line = line[line.index("log:"):]
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
