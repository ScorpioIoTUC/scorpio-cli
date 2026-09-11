from scorpio.cli.clients.github.github_client import GithubClient
from scorpio.cli.config import (
    INSTALL_DIR,
    INSTALL_METADATA_PATH,
    REPOSITORY,
)
from scorpio.server.main import run_server


def main():
    github_client = GithubClient(
        repository=REPOSITORY,
        install_directory=INSTALL_DIR,
        metadata_path=INSTALL_METADATA_PATH,
    )

    run_server(github_client)


if __name__ == "__main__":
    main()
