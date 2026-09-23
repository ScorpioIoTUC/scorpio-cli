"""Persist local project configuration in the existing .env format."""

from pathlib import Path


class LocalTokenEnvironment:
    def __init__(self, project_dir: Path) -> None:
        self.path = project_dir / ".env"

    def update(self, api_url: str, token: str) -> None:
        env_vars = {}
        if self.path.exists():
            with open(self.path, "r") as env_file:
                for line in env_file:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
        env_vars["SCORPIO_API_URL"] = api_url
        env_vars["SCORPIO_API_TOKEN"] = token
        with open(self.path, "w") as env_file:
            for key, value in env_vars.items():
                env_file.write(f"{key}={value}\n")
