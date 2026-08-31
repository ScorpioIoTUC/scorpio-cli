# Scorpio CLI

Command-line installer and local setup interface for Scorpio IoT UC.

# Installation
## Install on Debian or Raspberry Pi OS

Debian-based systems protect the system Python environment. Install Scorpio CLI
with `pipx` instead of using `sudo pip` or `--break-system-packages`.

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
source ~/.profile
pipx install scorpio-cli
```


## Commands

```text
scorpio ui             Start the setup interface
scorpio setup          Install host dependencies
scorpio setup-docker   Configure and start Docker infrastructure
scorpio start          Start Scorpio services
scorpio stop           Stop Scorpio services and preserve data
scorpio status         Show service status
scorpio logs           Follow service logs
scorpio build          Build Docker images
scorpio reset          Stop services and permanently remove Docker data
```

`scorpio reset` requires explicit confirmation because it removes the MQTT and
SQLite Docker volumes.

Upgrade or uninstall the CLI with:

```bash
pipx upgrade scorpio-cli
pipx uninstall scorpio-cli
```
