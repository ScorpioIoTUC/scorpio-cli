"""Public endpoints. Paths and HTTP verbs are intentionally unchanged."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    """Select a controller action; stream actions write SSE instead of JSON."""

    resource: str
    action: str
    stream: bool = False


GET_ROUTES = {
    "/version": Route("version", "get_system_version"),
    "/scorpio/setup/status": Route("setup", "get_setup_status"),
    "/scorpio/setup/events": Route("events", "send_setup_events", stream=True),
    "/scorpio/stop": Route("infrastructure", "stop_scorpio"),
    "/scorpio/start": Route("infrastructure", "start_scorpio"),
    "/scorpio/logs/live": Route("events", "send_live_logs", stream=True),
    "/discord/settings": Route("discord", "get_settings"),
    "/scorpio/setup/token": Route("token", "get_setup_token"),
    "/scorpio/update": Route("update", "get_versions"),
}
POST_ROUTES = {
    "/ssh/login": Route("ssh", "ssh_login"),
    "/ssh/logout": Route("ssh", "ssh_logout"),
    "/scorpio/setup": Route("setup", "scorpio_setup"),
    "/scorpio/reboot": Route("infrastructure", "reboot"),
    "/discord/setup": Route("discord", "setup"),
    "/discord/set-channel": Route("discord", "set_channel"),
    "/discord/set-alert-gap": Route("discord", "set_alert_gap"),
    "/discord/remove": Route("discord", "remove"),
    "/discord/notify": Route("discord", "notify"),
    "/scorpio/setup/token": Route("token", "set_setup_token"),
    "/scorpio/update": Route("update", "update_scorpio"),
}
