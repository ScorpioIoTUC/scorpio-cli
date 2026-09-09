from pathlib import Path

REPOSITORY = "ScorpioIoTUC/Scorpio-Project"

INSTALL_DIR = Path.home() / ".local" / "share" / "scorpio" / "Scorpio-Project"
INSTALL_METADATA_PATH = INSTALL_DIR.parent / "installation.json"

SCORPIO_DATA_DIR = Path(__file__).home() / ".local" / "share" / "scorpio"
STORAGE_PATH = SCORPIO_DATA_DIR / "storage.json"