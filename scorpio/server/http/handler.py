"""HTTP transport: parse JSON, dispatch routes, serve static UI assets."""

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler

from scorpio.server.config import UI_DIR, UI_URL

from .controllers import Controllers
from .events import EventStreams
from .routes import GET_ROUTES, POST_ROUTES


class Handler(EventStreams, SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        controllers: Controllers,
        setup_manager,
        live_logs_manager,
        **kwargs,
    ):
        self.controllers = controllers
        self.setup_manager = setup_manager
        self.live_logs_manager = live_logs_manager
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def do_GET(self):
        route = GET_ROUTES.get(self.path)
        if route is None:
            return super().do_GET()
        if route.stream:
            return getattr(self, route.action)()
        self.send_json(*self.controllers.dispatch(route, {}))

    def do_POST(self):
        body = self._body()
        route = POST_ROUTES.get(self.path)
        if route is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found.")
            return
        self.send_json(*self.controllers.dispatch(route, body))

    def _body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        return json.loads(body) if body else {}

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", UI_URL)
        super().end_headers()
