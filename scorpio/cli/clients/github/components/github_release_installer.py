import json
import logging
import shutil
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path

from scorpio.cli.clients.github.github_types import Release
from scorpio.cli.clients.github.github_contract import GithubReleaseInstallerContract


logger = logging.getLogger(__name__)
ReleaseDownloader = Callable[[Release, Path], Path]


class GithubReleaseInstaller(GithubReleaseInstallerContract):
    """Install a downloaded GitHub release and preserve local configuration."""

    def __init__(
        self,
        install_directory: Path,
        metadata_path: Path,
        download_release: ReleaseDownloader,
    ) -> None:
        self.install_directory = install_directory
        self.metadata_path = metadata_path
        self.download_release = download_release
        self.backup_directory = install_directory.parent / ".Scorpio-Project.backup"

    @property
    def is_installed(self) -> bool:
        return (self.install_directory / "Makefile").exists()

    @property
    def installed_version(self) -> str | None:
        if not self.metadata_path.exists():
            return None

        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            return metadata.get("version")
        except (OSError, json.JSONDecodeError):
            logger.warning("Could not read installation metadata")
            return None

    def register_version(self, version: str) -> None:
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(
            json.dumps({"version": version}, indent=2),
            encoding="utf-8",
        )

    def install(self, release: Release) -> tuple[Path, str]:
        """Download, extract and atomically replace the current installation."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            archive = self.download_release(
                release,
                temporary_path / "scorpio.zip",
            )
            extracted_directory = temporary_path / "extracted"
            source_directory = self._extract_release(
                archive,
                extracted_directory,
            )
            self._replace_installation(source_directory, release.version)

        logger.info(
            "Scorpio %s installed at %s",
            release.version,
            self.install_directory,
        )
        return self.install_directory, release.version

    def _extract_release(self, archive: Path, destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        destination_root = destination.resolve()

        with zipfile.ZipFile(archive) as zip_file:
            for member in zip_file.infolist():
                member_path = (destination / member.filename).resolve()
                if (
                    member_path != destination_root
                    and destination_root not in member_path.parents
                ):
                    raise ValueError("Release archive contains an unsafe path")
            zip_file.extractall(destination)

        source_directories = [path for path in destination.iterdir() if path.is_dir()]
        if len(source_directories) != 1:
            raise ValueError("Release archive must contain one project directory")

        logger.info("Release extracted successfully")
        return source_directories[0]

    def _replace_installation(
        self,
        source_directory: Path,
        version: str,
    ) -> None:
        self.install_directory.parent.mkdir(parents=True, exist_ok=True)
        self._recover_interrupted_update()

        if self.install_directory.exists():
            logger.info("Creating temporary backup of the current installation")
            self.install_directory.rename(self.backup_directory)

        try:
            shutil.move(str(source_directory), self.install_directory)
            self._preserve_environment()
            self.register_version(version)
        except Exception:
            logger.exception("Update failed; restoring previous installation")
            if self.install_directory.exists():
                shutil.rmtree(self.install_directory)
            if self.backup_directory.exists():
                self.backup_directory.rename(self.install_directory)
            raise
        else:
            if self.backup_directory.exists():
                shutil.rmtree(self.backup_directory)

    def _recover_interrupted_update(self) -> None:
        if not self.backup_directory.exists():
            return

        if not self.install_directory.exists():
            logger.warning("Restoring installation from an interrupted update")
            self.backup_directory.rename(self.install_directory)
        else:
            shutil.rmtree(self.backup_directory)

    def _preserve_environment(self) -> None:
        previous_environment = self.backup_directory / ".env"
        if previous_environment.exists():
            shutil.copy2(
                previous_environment,
                self.install_directory / ".env",
            )
            logger.info("Existing .env configuration preserved")
