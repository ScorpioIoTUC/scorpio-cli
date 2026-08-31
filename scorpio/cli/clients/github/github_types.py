from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    version: str
    download_url: str
