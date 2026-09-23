import json
from pathlib import Path
from threading import RLock
from typing import Any


class StorageHandler:
    """Manage the server JSON storage through one shared instance."""

    _instance: "StorageHandler | None" = None
    _instance_lock = RLock()

    def __init__(self, path: Path, initial_data: dict[str, Any]):
        self._path = path
        self._initial_data = initial_data
        self._lock = RLock()

    @classmethod
    def get_instance(
        cls, path: Path | None = None, initial_data: dict[str, Any] | None = None
    ) -> "StorageHandler":
        """Return the singleton instance of StorageHandler.
        - If the instance does not exist, it will be created with the provided path and initial data.
        - If the instance already exists, the provided path and initial data will be ignored.
        """

        with cls._instance_lock:
            if cls._instance is None:
                if path is None or initial_data is None:
                    raise RuntimeError(
                        "StorageHandler must be initialized with path and initial data."
                    )

                cls._instance = cls(path, initial_data)
            return cls._instance

    def __new__(
        cls, path: Path | None = None, initial_data: dict[str, Any] | None = None
    ) -> "StorageHandler":
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialize(path, initial_data)
                cls._instance = instance
            return cls._instance

    def _initialize(
        self, path: Path | None, initial_data: dict[str, Any] | None
    ) -> None:
        self._path = path
        self._initial_data = initial_data or {}
        self._lock = RLock()

    def create(self) -> dict[str, Any]:
        """Create the storage file when it does not exist."""
        if self._path is None:
            raise RuntimeError("Storage path has not been configured.")

        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if not self._path.exists():
                self._write(self._initial_data)
            return self.get()

    def get(self) -> dict[str, Any]:
        """Read and return the complete storage document."""
        if self._path is None:
            raise RuntimeError("Storage path has not been configured.")

        with self._lock:
            if not self._path.exists():
                return {}
            with self._path.open("r", encoding="utf-8") as storage_file:
                return json.load(storage_file)

    def update(self, data: dict[str, Any]) -> None:
        """Replace the storage document with the provided data."""
        if self._path is None:
            raise RuntimeError("Storage path has not been configured.")

        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._write(data)

    def update_scorpio_cli_version(self, version: str) -> None:
        """Persist the Scorpio CLI version without replacing the setup data."""
        if not version:
            raise ValueError("Scorpio CLI version cannot be empty.")

        with self._lock:
            storage = self.get()
            setup = storage.get("setup")
            if not isinstance(setup, dict):
                setup = {}
                storage["setup"] = setup

            versions = setup.get("version")
            if not isinstance(versions, dict):
                versions = {}
                setup["version"] = versions

            versions["scorpio_cli"] = version
            self.update(storage)

    def _write(self, data: dict[str, Any]) -> None:
        with self._path.open("w", encoding="utf-8") as storage_file:
            json.dump(data, storage_file, indent=4)
