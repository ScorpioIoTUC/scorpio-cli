import paramiko
from abc import ABC, abstractmethod
from collections.abc import Iterator


class SSHContract(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Establish an SSH connection to the specified host."""
        return

    def execute_command(self, command: str) -> dict:
        """Execute a command on the remote host and return the output."""
        return {}

    def execute_streaming(self, command: str) -> Iterator[str]:
        raise NotImplementedError

    def close_connection(self) -> None:
        """Close the SSH connection."""
        return
