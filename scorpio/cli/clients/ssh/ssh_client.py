from .ssh_contract import SSHContract
import paramiko
from .ssh_types import SSHException
from collections.abc import Iterator
import shlex


class SSHClient(SSHContract):
    def __init__(self, hostname: str, username: str, password: str, port=22) -> None:
        self.port = port  # Default SSH port
        self.hostname = hostname
        self.username = username
        self.password = password

        self.client = paramiko.SSHClient()

    def connect(self) -> None:
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
            )
        except paramiko.AuthenticationException:
            raise ConnectionError("Authentication failed, please verify your credentials.")
        except paramiko.SSHException as sshException:
            raise ConnectionError(f"Unable to establish SSH connection: {sshException}")

    def execute_command(self, command: str) -> dict:
        _, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        return {
            "exit_code": exit_code,
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
        }

    def execute_streaming(self, command: str) -> Iterator[str]:
        escaped_password = shlex.quote(self.password)
        remote_command = (
            f"printf '%s\\n' {escaped_password} | "
            "sudo -S -p '' -v >/dev/null 2>&1 && "
            f"bash -lc {shlex.quote(command)}"
        )

        _, stdout, stderr = self.client.exec_command(remote_command, get_pty=True)
        try:
            for line in iter(stdout.readline, ""):
                yield line.rstrip("\n")

            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                error = stderr.read().decode().strip()
                raise RuntimeError(
                    error or f"Remote command failed with code {exit_code}"
                )
        finally:
            stdout.channel.close()

    def close_connection(self) -> None:
        """Close the SSH connection."""
        self.client.close()
