"""Update application operations, independent of HTTP and concrete adapters."""

import logging

from ..contracts.ports import (
    HostInfo,
    PackageInstaller,
    PackageUpgradeError,
    StatusQueries,
    Storage,
)
from ..contracts.result import Outcome, Result


class UpdateUseCases:
    def __init__(
        self,
        storage_handler: Storage,
        status_manager: StatusQueries,
        host: HostInfo,
        installer: PackageInstaller,
    ) -> None:
        self.storage_handler = storage_handler
        self.status_manager = status_manager
        self.host = host
        self.installer = installer

    def get_versions(self) -> dict:
        """Read current/latest CLI versions without starting an upgrade."""
        return self.status_manager.get_pypi_last_version()

    def update_scorpio(self) -> Result:
        previous_version = self.host.get_package_version("scorpio-cli")
        # Check if the pypi.org version is newer than the installed version
        pypi_version = self.status_manager.get_pypi_last_version()
        current_version = pypi_version.get("current_version")
        latest_version = pypi_version.get("latest_version")
        if current_version == "unknown" or latest_version == "unknown":
            return {
                "error": (
                    "Unable to determine the current or latest "
                    "version of Scorpio CLI."
                )
            }, Outcome.INTERNAL_SERVER_ERROR
        elif current_version == latest_version:
            return {
                "message": "Scorpio CLI is already up to date.",
                "previous_version": current_version,
                "installed_version": current_version,
                "restart_required": False,
            }, Outcome.OK

        try:
            self.installer.upgrade()

            installed_version = self.host.get_package_version("scorpio-cli")
            if not installed_version:
                raise RuntimeError(
                    "Unable to verify the installed Scorpio CLI version."
                )

            self.storage_handler.update_scorpio_cli_version(installed_version)

            return {
                "message": "Scorpio CLI updated successfully.",
                "previous_version": previous_version,
                "installed_version": installed_version,
                "restart_required": True,
            }, Outcome.OK
        except PackageUpgradeError as error:
            details = str(error)
            logging.error("Error updating Scorpio CLI: %s", details or error)
            return {
                "error": "Failed to update Scorpio CLI.",
                "details": details,
            }, Outcome.INTERNAL_SERVER_ERROR
        except (OSError, RuntimeError, ValueError) as error:
            logging.error("Error updating Scorpio CLI: %s", error)
            return {"error": str(error)}, Outcome.INTERNAL_SERVER_ERROR
