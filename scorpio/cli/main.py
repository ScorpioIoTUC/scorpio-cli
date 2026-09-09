import argparse
import os
import json

from scorpio.cli.clients.github import GithubClient
from scorpio.cli.config import (
    INSTALL_DIR,
    INSTALL_METADATA_PATH,
    REPOSITORY,
    STORAGE_PATH,
)
from .commands import (
    MakeCommand,
    ResetCommand,
    UICommand,
    VersionCommand,
    CommandContract,
    CommandDefinition,
    CommandKind,
    COMMAND_DEFINITIONS,
)
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class ScorpioCLI:
    def __init__(self):
        self.github_client = GithubClient(
            repository=REPOSITORY,
            install_directory=INSTALL_DIR,
            metadata_path=INSTALL_METADATA_PATH,
        )
        self.definitions = COMMAND_DEFINITIONS
        self.parser = self._create_parser()
        self.commands = self._create_commands()

    def run(self) -> None:
        self._ensure_data_storage()

        args = self.parser.parse_args()
        self.execute_command(args.command)

    def execute_command(
        self,
        command_name: str,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        command = self.commands.get(command_name)
        if command is None:
            raise ValueError(f"Unknown command: {command_name}")
        if isinstance(command, MakeCommand):
            command.execute(output_callback=output_callback)
        else:
            command.execute()

    def _ensure_data_storage(self):
        if not STORAGE_PATH.parent.exists():
            STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not STORAGE_PATH.exists():
            with open(STORAGE_PATH, "w") as f:
                json.dump({}, f, indent=4)

    def _create_command(self, definition: CommandDefinition) -> CommandContract:
        if definition.kind is CommandKind.UI:
            return UICommand(self.github_client, self.execute_command)

        if definition.kind in (CommandKind.MAKE, CommandKind.RESET):
            if definition.target is None:
                raise ValueError(f"Command '{definition.name}' requires a Make target.")

            command: CommandContract = MakeCommand(
                github_client=self.github_client,
                target=definition.target,
                ensure_latest=definition.requires_latest_release,
                name=definition.name,
            )

            if definition.kind is CommandKind.RESET:
                command = ResetCommand(command)
            return command

        if definition.kind is CommandKind.VERSION:
            command: CommandContract = VersionCommand(github_client=self.github_client)
            return command

        raise ValueError(f"Unsupported command kind: {definition.kind}")

    def _create_commands(self) -> dict[str, CommandContract]:
        return {
            command.name: self._create_command(command) for command in self.definitions
        }

    def _create_parser(self):
        parser = argparse.ArgumentParser(
            prog="scorpio",
            description="Scorpio IoT command-line interface.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)
        for definition in self.definitions:
            subparsers.add_parser(
                definition.name,
                help=definition.description,
                description=definition.description,
            )
        return parser


def main() -> None:
    ScorpioCLI().run()


if __name__ == "__main__":
    main()
