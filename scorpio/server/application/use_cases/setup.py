"""Setup application operations, independent of HTTP and concrete adapters."""

import shlex
from datetime import datetime

from ..contracts.ports import (
    HostInfo,
    Releases,
    RemoteCommands,
    SetupJobs,
    StatusQueries,
    Storage,
)
from ..contracts.result import Outcome, Result


class SetupUseCases:
    def __init__(
        self,
        storage_handler: Storage,
        remote_executor: RemoteCommands,
        setup_manager: SetupJobs,
        status_manager: StatusQueries,
        github_client: Releases,
        host: HostInfo,
    ) -> None:
        self.storage_handler = storage_handler
        self.remote_executor = remote_executor
        self.setup_manager = setup_manager
        self.status_manager = status_manager
        self.github_client = github_client
        self.host = host

    def setup_is_completed(self) -> bool:
        storage = self.storage_handler.get()
        if storage.get("setup") is None:
            return False

        setup_completed = storage["setup"].get("completed", False)
        return setup_completed

    def get_setup_status(self) -> dict:
        """Combine live state with persisted installation metadata."""
        status = self.setup_manager.get_status()
        status["ssh_active"] = self.remote_executor.is_connected
        storage = self.storage_handler.get()
        persisted_setup = storage.get("setup") or {}

        if persisted_setup.get("completed"):
            status["status"] = "completed"
            status["completedAt"] = persisted_setup.get("completedAt")
            status["timezone"] = persisted_setup.get("timezone")
            status["version"] = persisted_setup.get("version")

        docker_infra_status = (
            self.storage_handler.get()
            .get("docker_infra", {})
            .get("status", "unknown")
        )
        if docker_infra_status == "unknown":
            docker_status = self.status_manager.get_docker_compose_status()
            docker_infra_status = docker_status.get("running", False)
            docker_infra_status = (
                "running" if docker_infra_status else "stopped"
            )
            status["infrastructure"] = {"status": docker_infra_status}
        else:
            status["infrastructure"] = {"status": docker_infra_status}

        return status

    def scorpio_setup(self, body: dict) -> Result:
        current_status = self.setup_manager.get_status()["status"]
        if current_status == "running":
            return {
                "error": "Scorpio setup is already in progress."
            }, Outcome.CONFLICT

        if self.setup_is_completed():
            return {
                "error": "Scorpio setup has already been completed."
            }, Outcome.BAD_REQUEST

        try:
            latest_release = self.github_client.get_latest_release()
        except Exception as error:
            return {
                "error": (
                    f"Unable to determine the latest Scorpio release: {error}"
                )
            }, Outcome.BAD_GATEWAY

        release_tag = shlex.quote(latest_release.version)
        project_dir = "~/.local/share/scorpio/Scorpio-Project"

        started = self.setup_manager.start(
            executor=self.remote_executor,
            command=(
                "mkdir -p ~/.local/share/scorpio && "
                f"if [ ! -d {project_dir}/.git ]; then "
                "git clone --depth 1 --branch "
                f"{release_tag} "
                "https://github.com/ScorpioIoTUC/Scorpio-Project.git "
                f"{project_dir}; "
                "else "
                f"git -C {project_dir} fetch --depth 1 origin "
                f"refs/tags/{release_tag} && "
                f"git -C {project_dir} checkout --force FETCH_HEAD; "
                "fi && "
                f"cd {project_dir} && make setup-host && make setup-docker"
            ),
            on_success=self.mark_setup_as_completed,
        )

        if not started:
            return {
                "error": "Unable to start Scorpio setup."
            }, Outcome.CONFLICT

        return {
            "message": "Scorpio setup started.",
            "status": "running",
        }, Outcome.ACCEPTED

    def mark_setup_as_completed(self) -> None:
        storage = self.storage_handler.get()
        scorpio_proj_version = self.github_client.get_latest_release().version
        scorpio_cli_version = self.host.get_package_version("scorpio-cli")
        timezone = self.host.get_local_timezone()

        storage["setup"] = {
            "completed": True,
            "completedAt": datetime.now(tz=timezone).isoformat(),
            "timezone": str(timezone),
            "version": {
                "scorpio_project": scorpio_proj_version,
                "scorpio_cli": scorpio_cli_version,
            },
        }
        self.storage_handler.update(storage)
