from abc import ABC, abstractmethod
from pathlib import Path

from .github_types import Release


class GithubContract(ABC):
    @abstractmethod
    def get_latest_release(self) -> Release:
        """Get the latest release information from GitHub.

        :return Release: An instance of the Release class containing the version and download
        URL of the latest release.
        """
        raise NotImplementedError

    @abstractmethod
    def download_release(self, release: Release, destination: Path) -> Path:
        """Download the specified release to the given destination.
        :param release: The release to download.
        :param destination: The path where the release should be downloaded.

        :return: The path to the downloaded release file.
        """
        raise NotImplementedError

    @abstractmethod
    def install_latest_release(self) -> tuple[Path, str]:
        """Download and install the latest repository release.

        :return tuple[Path, str]: A tuple containing the path to the installed
        release and its version.
        """
        raise NotImplementedError

    @abstractmethod
    def ensure_project_installed(self) -> tuple[Path, str]:
        """Install the project only when it is not already available."""
        raise NotImplementedError

    @abstractmethod
    def ensure_latest_release(self) -> tuple[Path, str]:
        """Install or update the project to the latest available release."""
        raise NotImplementedError


class GithubReleaseInstallerContract(ABC):
    @property
    @abstractmethod
    def is_installed(self) -> bool:
        """Check if the project is already installed.

        :return bool: True if the project is installed, False otherwise.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def installed_version(self) -> str | None:
        """Get the version of the currently installed project.

        :return str | None: The version of the installed project, or None if not installed.
        """
        raise NotImplementedError

    @abstractmethod
    def register_version(self, version: str) -> None:
        """Register the version of the installed project.

        :param version: The version to register.
        """
        raise NotImplementedError

    @abstractmethod
    def install(self, release: Release) -> tuple[Path, str]:
        """Install the specified release of the project.

        :param release: The release to install.

        :return tuple[Path, str]: A tuple containing the path to the installed
        release and its version.
        """
        raise NotImplementedError
