"""Composition root: construct adapters and inject them into use cases."""

import logging
from functools import partial

from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host

from .application.use_cases.discord import DiscordUseCases
from .application.use_cases.infrastructure import InfrastructureUseCases
from .application.use_cases.setup import SetupUseCases
from .application.use_cases.ssh import SshUseCases
from .application.use_cases.token import TokenUseCases
from .application.use_cases.update import UpdateUseCases
from .application.use_cases.version import VersionUseCases
from .config import (
    PORT,
    SCORPIO_PROJECT_DIR,
    SERVER_STORAGE_INIT_DATA,
    SERVER_STORAGE_PATH,
    SERVER_URL,
)
from .http.controllers import Controllers
from .http.handler import Handler
from .http.server import ScorpioHTTPServer
from .infrastructure.discord_delivery import DiscordHttpDelivery
from .infrastructure.live_logs_manager import LiveLogsManager
from .infrastructure.local_environment import LocalTokenEnvironment
from .infrastructure.package_installer import PipPackageInstaller
from .infrastructure.remote_executor import RemoteExecutor
from .infrastructure.setup_manager.main import SetupManager
from .infrastructure.status_manager import StatusManager
from .infrastructure.storage_handler import StorageHandler

logging.basicConfig(level=logging.INFO)


def run_server(github_client: GithubContract):
    storage = StorageHandler.get_instance(
        path=SERVER_STORAGE_PATH,
        initial_data=SERVER_STORAGE_INIT_DATA,
    )
    storage.create()
    setup = SetupManager()
    remote = RemoteExecutor(storage)
    logs = LiveLogsManager(remote)
    status = StatusManager(remote, storage)
    controllers = Controllers(
        ssh=SshUseCases(storage, remote),
        setup=SetupUseCases(
            storage, remote, setup, status, github_client, Host
        ),
        infrastructure=InfrastructureUseCases(storage, remote),
        token=TokenUseCases(
            storage, LocalTokenEnvironment(SCORPIO_PROJECT_DIR)
        ),
        update=UpdateUseCases(storage, status, Host, PipPackageInstaller()),
        version=VersionUseCases(github_client, Host),
        discord=DiscordUseCases(storage, DiscordHttpDelivery()),
    )
    handler = partial(
        Handler,
        controllers=controllers,
        setup_manager=setup,
        live_logs_manager=logs,
    )
    logging.info("Server started at %s", SERVER_URL)
    ScorpioHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
