from pathlib import Path

REPOSITORY = "ScorpioIoTUC/Scorpio-Project"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"

INSTALL_DIR = Path.home() / ".local" / "share" / "scorpio" / "Scorpio-Project"
INSTALL_METADATA_PATH = INSTALL_DIR.parent / "installation.json"
ALLOWED_TARGETS = {
    "setup": "setup-all",
    "setup-docker": "setup-docker",
    "start": "start",
    "stop": "stop",
    "status": "ps",
    "logs": "logs",
    "build": "build",
    "reset": "delete-all",
}

COMMAND_DESCRIPTIONS = {
    "setup": "Install Scorpio host dependencies.",
    "setup-docker": "Configure and start the Docker infrastructure.",
    "start": "Build and start Scorpio services.",
    "stop": "Stop Scorpio services while preserving stored data.",
    "status": "Show the current status of Scorpio services.",
    "logs": "Follow logs from all Scorpio services.",
    "build": "Build the Scorpio Docker images.",
    "reset": "Stop Scorpio and permanently remove its Docker data.",
}