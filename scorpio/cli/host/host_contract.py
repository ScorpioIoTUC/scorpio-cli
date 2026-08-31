from abc import ABC, abstractmethod


class HostContract(ABC):
    @staticmethod
    @abstractmethod
    def get_local_ip() -> str:
        """Get the local IP address of the host."""
        return ""
