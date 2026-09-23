"""SSE framing, heartbeats and subscriber cleanup."""

import json
import queue
from http import HTTPStatus

from scorpio.server.config import UI_URL


class EventStreams:
    """SSE transport; disconnects preserve the shared SSH session."""

    def send_live_logs(self):
        # Check if the ssh client is active
        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", UI_URL)
            self.end_headers()

            for event in self.live_logs_manager.stream():
                self.wfile.write(
                    f"data: {json.dumps(event)}\n\n".encode("utf-8")
                )
                self.wfile.flush()
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionError,
            RuntimeError,
        ):
            # Closing one SSE client must not close the shared SSH session.
            return

    def send_setup_events(self):
        subscriber = self.setup_manager.subscribe()

        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", UI_URL)
            self.end_headers()

            # Permite al frontend conocer inmediatamente el estado actual.
            initial_status = {
                "type": "status",
                "data": self.controllers.setup.get_setup_status(),
            }

            self.wfile.write(
                f"data: {json.dumps(initial_status)}\n\n".encode("utf-8")
            )
            self.wfile.flush()

            while True:
                try:
                    log = subscriber.get(timeout=15)

                    if log is None:
                        final_status = {
                            "type": "status",
                            "data": self.controllers.setup.get_setup_status(),
                        }

                        self.wfile.write(
                            f"data: {json.dumps(final_status)}\n\n".encode(
                                "utf-8"
                            )
                        )
                        self.wfile.flush()
                        break
                    event = {"type": "log", "data": log.to_dict()}
                    self.wfile.write(
                        f"data: {json.dumps(event)}\n\n".encode("utf-8")
                    )
                    self.wfile.flush()

                except queue.Empty:
                    # Heartbeat to keep the connection alive
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()

        except (BrokenPipeError, ConnectionResetError):
            pass

        finally:
            self.setup_manager.unsubscribe(subscriber)
