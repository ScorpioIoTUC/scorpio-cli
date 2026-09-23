"""Install in the local UI host's Python environment, never over SSH."""

import subprocess
import sys

from scorpio.server.application.contracts.ports import PackageUpgradeError


class PipPackageInstaller:
    def upgrade(self) -> None:
        try:
            subprocess.run(
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
        except subprocess.CalledProcessError as error:
            raise PackageUpgradeError(
                (error.stderr or error.stdout or "").strip()
            ) from error
