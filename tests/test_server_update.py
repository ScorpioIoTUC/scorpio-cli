import subprocess
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock, patch

from scorpio.server.components.storage_handler import StorageHandler
from scorpio.server.application.use_cases.update import UpdateUseCases
from scorpio.server.http.controllers import to_http
from scorpio.server.infrastructure.package_installer import PipPackageInstaller
from scorpio.cli.host.host import Host


class StorageVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_instance = StorageHandler._instance
        StorageHandler._instance = None

    def tearDown(self) -> None:
        StorageHandler._instance = self.previous_instance

    def test_cli_version_update_preserves_existing_setup_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage = StorageHandler.get_instance(
                path=Path(temporary_directory) / "storage.json",
                initial_data={
                    "setup": {
                        "completed": True,
                        "completedAt": "2026-09-11T14:50:58-03:00",
                        "version": {
                            "scorpio_project": "0.0.7",
                            "scorpio_cli": "0.1.0.9",
                        },
                    }
                },
            )
            storage.create()

            storage.update_scorpio_cli_version("0.1.0.10")

            setup = storage.get()["setup"]
            self.assertTrue(setup["completed"])
            self.assertEqual(setup["version"]["scorpio_project"], "0.0.7")
            self.assertEqual(setup["version"]["scorpio_cli"], "0.1.0.10")


class ScorpioUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = UpdateUseCases(
            Mock(), Mock(), Host, PipPackageInstaller()
        )
        self.handler.storage_handler = Mock()
        self.handler.status_manager = Mock()
        self.handler.status_manager.get_pypi_last_version.return_value = {
            "current_version": "0.1.0.9",
            "latest_version": "0.1.0.10",
        }

    @patch("scorpio.server.infrastructure.package_installer.subprocess.run")
    @patch("scorpio.cli.host.host.Host.get_package_version")
    def test_successful_update_persists_installed_version(
        self,
        get_package_version: Mock,
        run: Mock,
    ) -> None:
        get_package_version.side_effect = ["0.1.0.9", "0.1.0.10"]

        payload, status = to_http(self.handler.update_scorpio())

        run.assert_called_once_with(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "scorpio-cli",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.handler.storage_handler.update_scorpio_cli_version.assert_called_once_with(
            "0.1.0.10"
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["installed_version"], "0.1.0.10")
        self.assertTrue(payload["restart_required"])

    @patch("scorpio.server.infrastructure.package_installer.subprocess.run")
    @patch(
        "scorpio.cli.host.host.Host.get_package_version",
        return_value="0.1.0.10",
    )
    def test_up_to_date_version_skips_pip(
        self,
        _get_package_version: Mock,
        run: Mock,
    ) -> None:
        self.handler.status_manager.get_pypi_last_version.return_value = {
            "current_version": "0.1.0.10",
            "latest_version": "0.1.0.10",
        }

        payload, status = to_http(self.handler.update_scorpio())

        run.assert_not_called()
        self.handler.storage_handler.update_scorpio_cli_version.assert_not_called()
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(
            payload["message"], "Scorpio CLI is already up to date."
        )
        self.assertEqual(payload["installed_version"], "0.1.0.10")
        self.assertFalse(payload["restart_required"])

    @patch("scorpio.server.infrastructure.package_installer.subprocess.run")
    @patch(
        "scorpio.cli.host.host.Host.get_package_version",
        return_value="0.1.0.9",
    )
    def test_failed_update_does_not_modify_storage(
        self,
        _get_package_version: Mock,
        run: Mock,
    ) -> None:
        run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=[sys.executable, "-m", "pip"],
            stderr="upgrade failed",
        )

        payload, status = to_http(self.handler.update_scorpio())

        self.handler.storage_handler.update_scorpio_cli_version.assert_not_called()
        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(payload["details"], "upgrade failed")


if __name__ == "__main__":
    unittest.main()
