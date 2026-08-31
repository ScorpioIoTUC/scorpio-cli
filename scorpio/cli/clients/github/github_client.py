import json
import logging
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from .components import GithubReleaseInstaller
from .github_contract import GithubContract
from .github_types import Release


logger = logging.getLogger(__name__)


class GithubClient(GithubContract):
    def __init__(
        self,
        repository: str,
        install_directory: Path,
        metadata_path: Path,
        user_agent: str = "scorpio-iotuc",
        timeout: float = 15,
    ) -> None:
        self.repository = repository
        self.api_url = f"https://api.github.com/repos/{repository}"
        self.user_agent = user_agent
        self.timeout = timeout
        self.release_installer = GithubReleaseInstaller(
            install_directory=install_directory,
            metadata_path=metadata_path,
            download_release=self.download_release,
        )

    def get_latest_release(self) -> Release:
        url = f"{self.api_url}/releases/latest"
        logger.info("Checking latest Scorpio release from %s", url)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent},
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)

        release = Release(
            version=payload["tag_name"],
            download_url=payload["zipball_url"],
        )
        logger.info("Latest Scorpio release is %s", release.version)
        return release

    def download_release(self, release: Release, destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            release.download_url,
            headers={"User-Agent": self.user_agent},
        )

        logger.info("Downloading Scorpio %s", release.version)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            with destination.open("wb") as archive:
                shutil.copyfileobj(response, archive)

        logger.info("Release downloaded successfully")
        return destination

    def install_latest_release(self) -> tuple[Path, str]:
        release = self.get_latest_release()
        return self.release_installer.install(release)

    def ensure_project_installed(self) -> tuple[Path, str]:
        if self.release_installer.is_installed:
            version = self.release_installer.installed_version or "unknown"
            return self.release_installer.install_directory, version
        return self.install_latest_release()

    def ensure_latest_release(self) -> tuple[Path, str]:
        try:
            release = self.get_latest_release()
        except urllib.error.URLError:
            if self.release_installer.is_installed:
                version = self.release_installer.installed_version or "unknown"
                logger.warning(
                    "Could not check GitHub; using installed Scorpio version %s",
                    version,
                )
                return self.release_installer.install_directory, version
            raise

        installed_version = self.release_installer.installed_version

        if self.release_installer.is_installed and installed_version == release.version:
            logger.info("Scorpio %s is already up to date", release.version)
            return self.release_installer.install_directory, release.version

        if self.release_installer.is_installed and installed_version is None:
            logger.warning(
                "Existing installation has no version metadata; replacing it with %s",
                release.version,
            )
            return self.release_installer.install(release)

        if installed_version:
            logger.info(
                "Updating Scorpio from %s to %s",
                installed_version,
                release.version,
            )

        return self.release_installer.install(release)
