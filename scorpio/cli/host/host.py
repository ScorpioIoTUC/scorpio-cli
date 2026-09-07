from .host_contract import HostContract
import socket
from importlib.metadata import version, PackageNotFoundError
from tzlocal import get_localzone

class Host(HostContract):
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_local_ip() -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
            except OSError:
                return "127.0.0.1"
            finally:
                sock.close()

    @staticmethod
    def get_network_url(port: int = 8000) -> str:
        local_ip = Host.get_local_ip()
        return f"http://{local_ip}:{port}"

    @staticmethod
    def get_package_version(package_name: str) -> str:
        try:
            return version(package_name)
        except PackageNotFoundError:
            print(f"Package '{package_name}' not found.")
            return ""

    @staticmethod
    def get_local_timezone():
        return get_localzone()
