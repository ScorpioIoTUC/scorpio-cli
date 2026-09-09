from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class SetupLog:
    level: str
    module: str
    step: int | None
    total_steps: int | None
    step_id: str | None
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

