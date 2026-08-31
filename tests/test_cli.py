import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scorpio.cli.clients.github.github_client import GithubClient
from scorpio.cli.clients.github.github_types import Release
from scorpio.cli.commands.make_command import MakeCommand
from scorpio.cli.main import ScorpioCLI, main


class ScorpioCLITests(unittest.TestCase):
    def test_console_entry_point_is_callable(self) -> None:
        self.assertTrue(callable(main))

    def test_all_commands_can_be_created(self) -> None:
        cli = ScorpioCLI()

        self.assertEqual(
            set(cli.commands),
            {
                "ui",
                "setup",
                "setup-docker",
                "start",
                "stop",
                "status",
                "logs",
                "build",
                "reset",
            },
        )

    @patch("scorpio.cli.commands.make_command.subprocess.run")
    def test_make_command_can_require_latest_release(self, run: Mock) -> None:
        github_client = Mock()
        github_client.ensure_latest_release.return_value = (Path("/tmp/project"), "1.0")
        command = MakeCommand(github_client, "setup-docker", ensure_latest=True)

        command.execute()

        github_client.ensure_latest_release.assert_called_once_with()
        github_client.ensure_project_installed.assert_not_called()
        run.assert_called_once_with(
            ["make", "setup-docker"],
            cwd=Path("/tmp/project"),
            check=True,
        )

    @patch("scorpio.cli.commands.make_command.subprocess.run")
    def test_make_command_uses_installed_release_by_default(self, run: Mock) -> None:
        github_client = Mock()
        github_client.ensure_project_installed.return_value = (
            Path("/tmp/project"),
            "1.0",
        )
        command = MakeCommand(github_client, "status")

        command.execute()

        github_client.ensure_project_installed.assert_called_once_with()
        github_client.ensure_latest_release.assert_not_called()

    @patch("scorpio.cli.commands.make_command.subprocess.run")
    def test_make_failure_exits_without_python_traceback(self, run: Mock) -> None:
        github_client = Mock()
        github_client.ensure_project_installed.return_value = (
            Path("/tmp/project"),
            "1.0",
        )
        run.side_effect = subprocess.CalledProcessError(
            returncode=2,
            cmd=["make", "status"],
        )

        with self.assertRaises(SystemExit) as context:
            MakeCommand(github_client, "status").execute()

        self.assertEqual(context.exception.code, 2)


class GithubClientTests(unittest.TestCase):
    def test_installation_without_metadata_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            install_directory = root / "Scorpio-Project"
            install_directory.mkdir()
            (install_directory / "Makefile").touch()
            client = GithubClient(
                repository="owner/project",
                install_directory=install_directory,
                metadata_path=root / "installation.json",
            )
            release = Release(version="0.0.3", download_url="https://example.test")
            client.get_latest_release = Mock(return_value=release)
            client.release_installer.install = Mock(
                return_value=(install_directory, release.version)
            )

            result = client.ensure_latest_release()

            client.release_installer.install.assert_called_once_with(release)
            self.assertEqual(result, (install_directory, "0.0.3"))


if __name__ == "__main__":
    unittest.main()
