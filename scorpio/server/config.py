from pathlib import Path

PORT = 8000
SERVER_URL = f"http://localhost:{PORT}"
UI_URL = SERVER_URL

PACKAGE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = PACKAGE_DIR / "ui" / "dist"

SCORPIO_DATA_DIR = Path(__file__).home() / ".local" / "share" / "scorpio"
SERVER_STORAGE_PATH = SCORPIO_DATA_DIR / "server_storage.json"
SERVER_STORAGE_INIT_DATA = {
    "ssh": {
        "is_active": False,
        "hostname": "",
        "username": "",
        "password": "",
    }
}