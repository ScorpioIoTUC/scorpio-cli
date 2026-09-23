"""Application outcomes mapped to status codes by HTTP controllers."""

from enum import Enum, auto
from typing import Any

Payload = dict[str, Any]


class Outcome(Enum):
    """Success or failure categories independent of the HTTP transport."""

    OK = auto()
    ACCEPTED = auto()
    BAD_REQUEST = auto()
    UNAUTHORIZED = auto()
    NOT_FOUND = auto()
    CONFLICT = auto()
    INTERNAL_SERVER_ERROR = auto()
    BAD_GATEWAY = auto()


Result = tuple[Payload, Outcome]
