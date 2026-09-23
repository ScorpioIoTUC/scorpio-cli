"""Application operations independent of HTTP and concrete adapters."""

import logging
import threading

from ..contracts.ports import RemoteCommands, Storage
from ..contracts.result import Outcome, Result


class InfrastructureUseCases:
    def __init__(
        self, storage_handler: Storage, remote_executor: RemoteCommands
    ) -> None:
        self.storage_handler = storage_handler
        self.remote_executor = remote_executor

    def stop_scorpio(self) -> Result:
        try:
            self.execute_remote("make stop")
            # Persist the resulting infrastructure status.
            storage = self.storage_handler.get()
            storage["docker_infra"]["status"] = "stopped"
            self.storage_handler.update(storage)
            return {"message": "Scorpio stopped."}, Outcome.OK
        except Exception as e:
            logging.error("Error stopping Scorpio: %s", e)
            return {
                "error": "Failed to stop Scorpio."
            }, Outcome.INTERNAL_SERVER_ERROR

    def close_connection(self) -> None:
        """Close SSH and persist the inactive connection state."""
        self.remote_executor.close()
        storage = self.storage_handler.get()
        storage.setdefault("ssh", {})["is_active"] = False
        self.storage_handler.update(storage)

    def start_scorpio(self) -> Result:
        try:
            self.execute_remote("make start")
            # Store this information in the storage
            storage = self.storage_handler.get()
            storage["docker_infra"]["status"] = "running"
            self.storage_handler.update(storage)
            return {"message": "Scorpio started."}, Outcome.OK
        except Exception as e:
            logging.error("Error starting Scorpio: %s", e)
            return {
                "error": "Failed to start Scorpio."
            }, Outcome.INTERNAL_SERVER_ERROR

    def execute_remote(self, command: str) -> None:
        remote_command = (
            f"cd ~/.local/share/scorpio/Scorpio-Project && {command}"
        )
        for _ in self.remote_executor.stream(remote_command):
            pass

    def reboot(self) -> Result:
        if not self.remote_executor.is_connected:
            return {"error": "No active SSH connection."}, Outcome.BAD_REQUEST

        def reboot_remote_host() -> None:
            try:
                for _ in self.remote_executor.stream("sudo reboot"):
                    pass
            except (ConnectionError, RuntimeError, OSError):
                # The connection will be closed when the Raspberry Pi reboots.
                self.close_connection()

        threading.Thread(target=reboot_remote_host, daemon=True).start()
        return {"message": "Raspberry Pi reboot requested."}, Outcome.ACCEPTED
