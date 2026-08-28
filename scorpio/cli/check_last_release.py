import json
import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


logger = logging.getLogger(__name__)

REPOSITORY = "ScorpioIoTUC/Scorpio-Project"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"

INSTALL_DIR = Path.home() / ".local" / "share" / "scorpio" / "Scorpio-Project"


def get_latest_release():
    logger.info("Checking latest Scorpio release from %s", RELEASE_API)
    request = urllib.request.Request(
        RELEASE_API, headers={"User-Agent": "scorpio-iotuc"}
    )

    with urllib.request.urlopen(request) as response:
        release = json.load(response)

    logger.info("Latest Scorpio release is %s", release["tag_name"])
    return release


def install_latest_release():
    release = get_latest_release()
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

        if INSTALL_DIR.exists():
            logger.warning("Replacing existing Scorpio installation at %s", INSTALL_DIR)
            shutil.rmtree(INSTALL_DIR)

        INSTALL_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source_directory, INSTALL_DIR)

    logger.info("Scorpio %s installed at %s", version, INSTALL_DIR)
    return INSTALL_DIR, version
