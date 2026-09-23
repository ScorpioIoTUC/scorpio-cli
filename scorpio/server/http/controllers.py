"""Translate request bodies and application outcomes at the HTTP boundary."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from scorpio.server.application.contracts.result import Outcome, Result
from scorpio.server.application.use_cases.discord import DiscordUseCases
from scorpio.server.application.use_cases.infrastructure import (
    InfrastructureUseCases,
)
from scorpio.server.application.use_cases.setup import SetupUseCases
from scorpio.server.application.use_cases.ssh import SshUseCases
from scorpio.server.application.use_cases.token import TokenUseCases
from scorpio.server.application.use_cases.update import UpdateUseCases
from scorpio.server.application.use_cases.version import VersionUseCases

from .routes import Route

STATUS_CODES = {outcome: HTTPStatus[outcome.name] for outcome in Outcome}


def to_http(result: Result) -> tuple[dict, HTTPStatus]:
    """Preserve response keys and map application outcomes to wire status."""
    payload, outcome = result
    return payload, STATUS_CODES[outcome]


@dataclass
class Controllers:
    """Use cases are injected once and share the existing runtime adapters."""

    ssh: SshUseCases
    setup: SetupUseCases
    infrastructure: InfrastructureUseCases
    token: TokenUseCases
    update: UpdateUseCases
    version: VersionUseCases
    discord: DiscordUseCases

    def dispatch(self, route: Route, body: dict[str, Any]) -> tuple[dict, int]:
        action = getattr(getattr(self, route.resource), route.action)
        if route.action in {"ssh_login", "scorpio_setup", "set_setup_token"}:
            result = action(body)
        elif route.resource == "discord" and route.action == "setup":
            result = action(body.get("token"))
        elif route.action == "set_channel":
            result = action(body.get("tag"), body.get("channel_id"))
        elif route.action == "set_alert_gap":
            result = action(body.get("minutes"))
        elif route.action == "notify":
            result = action(body.get("message"), body.get("tag"))
        else:
            result = action()
        if isinstance(result, tuple):
            return to_http(result)
        return result, HTTPStatus.OK
