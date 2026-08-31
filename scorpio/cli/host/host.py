from .host_contract import HostContract
import socket


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