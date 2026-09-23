"""Ssh application operations, independent of HTTP and concrete adapters."""

from ..contracts.ports import RemoteCommands, Storage
from ..contracts.result import Outcome, Result


class SshUseCases:
    def __init__(
        self, storage_handler: Storage, remote_executor: RemoteCommands
    ) -> None:
        self.storage_handler = storage_handler
        self.remote_executor = remote_executor

    def ssh_set_is_active(self, hostname: str, username: str, password: str):
        storage_data = self.storage_handler.get()
        if not storage_data.get("ssh"):
            storage_data["ssh"] = {}

        storage_data["ssh"]["is_active"] = True
        storage_data["ssh"]["hostname"] = hostname
        storage_data["ssh"]["username"] = username
        storage_data["ssh"]["password"] = password
        self.storage_handler.update(storage_data)

    def ssh_reset(self):
        storage_data = self.storage_handler.get()
        storage_data["ssh"]["is_active"] = False
        storage_data["ssh"]["hostname"] = ""
        storage_data["ssh"]["username"] = ""
        storage_data["ssh"]["password"] = ""
        self.storage_handler.update(storage_data)

    def ssh_login(self, body: dict) -> Result:
        username = body.get("username")
        password = body.get("password")
        hostname = body.get("hostname")
        if not username or not password or not hostname:
            return {
                "error": (
                    "Missing required fields: username, password, "
                    "and hostname are required."
                )
            }, Outcome.BAD_REQUEST

        try:
            self.remote_executor.connect(hostname, username, password)
            self.ssh_set_is_active(hostname, username, password)

        except ConnectionError as e:
            return {"error": str(e)}, Outcome.UNAUTHORIZED

        return {
            "message": f"SSH login successful for user {username}."
        }, Outcome.OK

    def ssh_logout(self) -> Result:
        storage = self.storage_handler.get()
        if not storage.get("ssh") or not storage["ssh"].get("is_active"):
            return {
                "error": "No active SSH session found."
            }, Outcome.BAD_REQUEST
        self.ssh_reset()
        self.remote_executor.close()
        return {"message": "SSH logout successful."}, Outcome.OK
