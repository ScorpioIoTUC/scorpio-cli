import json
import logging
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from scorpio.cli.config import INSTALL_DIR, INSTALL_METADATA_PATH, RELEASE_API


logger = logging.getLogger(__name__)


def get_latest_release():
    logger.info("Checking latest Scorpio release from %s", RELEASE_API)
    request = urllib.request.Request(
        RELEASE_API, headers={"User-Agent": "scorpio-iotuc"}
    )

    with urllib.request.urlopen(request) as response:
        release = json.load(response)

    logger.info("Latest Scorpio release is %s", release["tag_name"])
    return release


def get_installed_version():
    if not INSTALL_METADATA_PATH.exists():
        return None

    try:
        metadata = json.loads(INSTALL_METADATA_PATH.read_text())
        return metadata.get("version")
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not read installation metadata")
        return None


def _write_installed_version(version):
    INSTALL_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSTALL_METADATA_PATH.write_text(json.dumps({"version": version}, indent=2))


def _replace_installation(source_directory, version):
    backup_directory = INSTALL_DIR.parent / ".Scorpio-Project.backup"
    INSTALL_DIR.parent.mkdir(parents=True, exist_ok=True)

    if backup_directory.exists():
        if not INSTALL_DIR.exists():
            logger.warning("Restoring installation from a previous interrupted update")
            backup_directory.rename(INSTALL_DIR)
        else:
            shutil.rmtree(backup_directory)

    if INSTALL_DIR.exists():
        logger.info("Creating temporary backup of the current installation")
        INSTALL_DIR.rename(backup_directory)

    try:
        shutil.move(source_directory, INSTALL_DIR)

        previous_env = backup_directory / ".env"
        if previous_env.exists():
            shutil.copy2(previous_env, INSTALL_DIR / ".env")
            logger.info("Existing .env configuration preserved")

        _write_installed_version(version)
    except Exception:
        logger.exception("Update failed; restoring previous installation")
        if INSTALL_DIR.exists():
            shutil.rmtree(INSTALL_DIR)
        if backup_directory.exists():
            backup_directory.rename(INSTALL_DIR)
        raise
    else:
        if backup_directory.exists():
            shutil.rmtree(backup_directory)


def _install_release(release):
    version = release["tag_name"]
    download_url = release["zipball_url"]

    logger.info("Downloading Scorpio %s", version)

    with tempfile.TemporaryDirectory() as temporary_directory:
        archive = Path(temporary_directory) / "scorpio.zip"

        urllib.request.urlretrieve(download_url, archive)
        logger.info("Release downloaded successfully")

        extracted = Path(temporary_directory) / "extracted"
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(extracted)
        logger.info("Release extracted successfully")

        source_directory = next(extracted.iterdir())
        _replace_installation(source_directory, version)


    logger.info("Scorpio %s installed at %s", version, INSTALL_DIR)
    return INSTALL_DIR, version


def install_latest_release():
    return _install_release(get_latest_release())


def ensure_project_installed():
    if (INSTALL_DIR / "Makefile").exists():
        return INSTALL_DIR, get_installed_version() or "unknown"
    return install_latest_release()


def ensure_latest_release():
    try:
        release = get_latest_release()
    except urllib.error.URLError:
        if (INSTALL_DIR / "Makefile").exists():
            version = get_installed_version() or "unknown"
            logger.warning(
                "Could not check GitHub; using installed Scorpio version %s", version
            )
            return INSTALL_DIR, version
        raise

    latest_version = release["tag_name"]
    installed_version = get_installed_version()

    if (INSTALL_DIR / "Makefile").exists() and installed_version == latest_version:
        logger.info("Scorpio %s is already up to date", latest_version)
        return INSTALL_DIR, installed_version

    if (INSTALL_DIR / "Makefile").exists() and installed_version is None:
        logger.warning(
            "Existing installation has no version metadata; registering it as %s",
            latest_version,
        )
        _write_installed_version(latest_version)
        return INSTALL_DIR, latest_version

    if installed_version:
        logger.info("Updating Scorpio from %s to %s", installed_version, latest_version)

    return _install_release(release)
