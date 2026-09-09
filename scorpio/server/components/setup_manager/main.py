from __future__ import annotations

import queue
import threading

from datetime import datetime, timezone
from .types import SetupLog
from .utils import parse_setup_log
from collections.abc import Callable
from ..remote_executor import RemoteExecutor


class SetupManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: set[queue.Queue[SetupLog | None]] = set()
        self._logs: list[SetupLog] = []
        self._thread: threading.Thread | None = None

        self.status = "idle"
        self.error: str | None = None
        self.started_at: str | None = None
        self.finished_at: str | None = None

    def _publish(self, log: SetupLog) -> None:
        with self._lock:
            self._logs.append(log)
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(log)

    def _finish_subscribers(self) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(None)

    def _run(
        self,
        executor: RemoteExecutor,
        command: str,
        on_success: Callable[[], None] | None,
    ) -> None:
        try:
            for line in executor.stream(command):
                self._handle_output(line)
            if on_success is not None:
                on_success()
            with self._lock:
                self.status = "completed"
                self.finished_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            with self._lock:
                self.status = "failed"
                self.error = str(exc)
                self.finished_at = datetime.now(timezone.utc).isoformat()
        finally:
            self._finish_subscribers()

    def _handle_output(self, line: str) -> None:
        parsed_log = parse_setup_log(line)
        if parsed_log is None and line.strip():
            parsed_log = SetupLog(
                level="info",
                module="setup",
                step=None,
                total_steps=None,
                step_id="command",
                message=line.strip(),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if parsed_log is not None:
            self._publish(parsed_log)



    def get_status(self) -> dict:
        with self._lock:
            current_log = self._logs[-1] if self._logs else None

            return {
                "status": self.status,
                "error": self.error,
                "startedAt": self.started_at,
                "finishedAt": self.finished_at,
                "lastLog": current_log.to_dict() if current_log else None,
                "logs": [log.to_dict() for log in self._logs],
            }

    def start(
        self,
        executor: RemoteExecutor,
        command: str,
        on_success: Callable[[], None] | None = None,
    ) -> bool:
        with self._lock:
            if self.status == "running":
                return False

            self.status = "running"
            self._logs.clear()
            self.error = None

            self.started_at = datetime.now(timezone.utc).isoformat()
            self.finished_at = None

            self._thread = threading.Thread(
                target=self._run,
                args=(executor, command, on_success),
                daemon=True,
            )
            self._thread.start()
        return True

    def subscribe(self) -> queue.Queue[SetupLog | None]:
        subscriber: queue.Queue[SetupLog | None] = queue.Queue()
        with self._lock:
            self._subscribers.add(subscriber)

        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[SetupLog | None]) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)
