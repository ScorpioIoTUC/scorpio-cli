from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

class HostContract(ABC):
    @staticmethod
    @abstractmethod
    def get_local_ip() -> str:
        """Get the local IP address of the host."""
        return ""
    
    @staticmethod
    @abstractmethod
    def get_network_url(port: int = 8000) -> str:
        """Get the network URL of the host."""
        return ""
    
    @staticmethod
    @abstractmethod
    def get_package_version(package_name: str) -> str:
        """Get the version of a package installed on the host."""
        return ""
    
    @staticmethod
    @abstractmethod
    def get_local_timezone() -> ZoneInfo:
        """Get the local timezone of the host."""
        return ZoneInfo("UTC")
