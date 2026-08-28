from pathlib import Path

PORT = 8000
SERVER_URL = f"http://localhost:{PORT}"
UI_URL = SERVER_URL

PACKAGE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = PACKAGE_DIR / "ui"
SYSTEM_JSON_PATH = Path(__file__).resolve().parent / "system.json"
