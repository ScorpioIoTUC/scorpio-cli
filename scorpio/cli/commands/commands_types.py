from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

"""
Command descriptions for the CLI help messages
"""


class CommandContract(ABC):
    @abstractmethod
    def execute(self):
        raise NotImplementedError("Subclasses must implement the execute method.")


class CommandKind(Enum):
    UI = "ui"
    MAKE = "make"
    RESET = "reset"


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    description: str
    kind: CommandKind
    target: str | None = None
    requires_latest_release: bool = False


COMMAND_DEFINITIONS = (
    CommandDefinition(
        name="ui",
        description="Start the Scorpio setup web interface.",
        kind=CommandKind.UI,
    ),
    CommandDefinition(
        name="setup",
        target="setup-all",
        description="Install Scorpio host dependencies.",
        kind=CommandKind.MAKE,
        requires_latest_release=True,
    ),
    CommandDefinition(
        name="setup-docker",
        target="setup-docker",
        description="Configure and start the Docker infrastructure.",
        kind=CommandKind.MAKE,
        requires_latest_release=True,
    ),
    CommandDefinition(
        name="start",
        target="start",
        description="Build and start Scorpio services.",
        kind=CommandKind.MAKE,
    ),
    CommandDefinition(
        name="stop",
        target="stop",
        description="Stop Scorpio services while preserving stored data.",
        kind=CommandKind.MAKE,
    ),
    CommandDefinition(
        name="status",
        target="ps",
        description="Show the current status of Scorpio services.",
        kind=CommandKind.MAKE,
    ),
    CommandDefinition(
        name="logs",
        target="logs",
        description="Follow logs from all Scorpio services.",
        kind=CommandKind.MAKE,
    ),
    CommandDefinition(
        name="build",
        target="build",
        description="Build the Scorpio Docker images.",
        kind=CommandKind.MAKE,
    ),
    CommandDefinition(
        name="reset",
        target="delete-all",
        description="Stop Scorpio and permanently remove its Docker data.",
        kind=CommandKind.RESET,
    ),
)
