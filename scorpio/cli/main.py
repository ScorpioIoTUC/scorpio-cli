import argparse


from scorpio.cli.clients.github import GithubClient
from scorpio.cli.config import (
    INSTALL_DIR,
    INSTALL_METADATA_PATH,
    REPOSITORY,
)
from .commands.make_command import MakeCommand, ResetCommand
from .commands.ui_command import UICommand
from .commands.commands_types import (
    CommandContract,
    COMMAND_DEFINITIONS,
    CommandDefinition,
    CommandKind,
)


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
        args = self.parser.parse_args()
        command = self.commands.get(args.command)
        if command is None:
            self.parser.error(f"Unknown command: {args.command}")
        command.execute()

    def _create_command(self, definition: CommandDefinition) -> CommandContract:
        if definition.kind is CommandKind.UI:
            return UICommand(self.github_client)
        if definition.kind in (CommandKind.MAKE, CommandKind.RESET):
            if definition.target is None:
                raise ValueError(f"Command '{definition.name}' requires a Make target.")

            command: CommandContract = MakeCommand(
                github_client=self.github_client,
                target=definition.target,
                ensure_latest=definition.requires_latest_release,
            )

            if definition.kind is CommandKind.RESET:
                command = ResetCommand(command)
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
