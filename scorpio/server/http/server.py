"""Threaded HTTP server with the existing disconnect handling."""

import sys
from http.server import ThreadingHTTPServer


class ScorpioHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type in (ConnectionResetError, BrokenPipeError):
            return
        if (
            exc_type is RuntimeError
            and "Remote command failed with code -1" in str(exc_value)
        ):
            return
        super().handle_error(request, client_address)
