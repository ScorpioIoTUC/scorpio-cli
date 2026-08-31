import paramiko
from abc import ABC, abstractmethod


class SSHContract(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Establish an SSH connection to the specified host."""
        return

    def execute_command(self, command: str) -> dict:
        """Execute a command on the remote host and return the output."""
        return {}

    def close_connection(self) -> None:
        """Close the SSH connection."""
        return
