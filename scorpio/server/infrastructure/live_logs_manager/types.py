from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DockerLog:
    service: str
    timestamp: str | None
    level: str | None
    layer: str | None
    message: str

    def to_dict(self) -> dict:
        return asdict(self)
