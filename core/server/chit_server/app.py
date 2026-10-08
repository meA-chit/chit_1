from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from . import registry
from .paths import WEB_DIST
from .router import MAX_REQUEST_BYTES, Context, HTTPError, Request, Router, parse_query

# ADR-0007: loopback only until the identity ADR lands. Do not make this configurable without it.
HOST = "127.0.0.1"
PORT = int(os.environ.get("CHIT_PORT", "8765"))

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "same-origin",
    "Cache-Control": "no-store",
}


def build_router(manifests: dict) -> Router:
    router = Router()

    @router.get("/api/health")
    def health(ctx: Context, request: Request):
        return 200, {"status": "ready", "storage": "plain-sqlite-dev" if ctx.store.plain else "encrypted-sqlite"}

    @router.get("/api/modules")
    def modules(ctx: Context, request: Request):
        return 200, {"modules": registry.module_catalog(manifests)}

    @router.get("/api/shell")
    def shell(ctx: Context, request: Request):
        try:
            return 200, registry.resolve_shell(
                manifests, request.query.get("surface", "web"), request.query.get("preset"),
                store=ctx.store, member_id=request.query.get("member"),
            )
        except ValueError as error:
            raise HTTPError(400, str(error)) from None

    registry.register_routes(router, manifests)
    return router


def safe_file(root: Path, relative: str) -> "Path | None":
    """Resolve `relative` under `root`; None when it escapes root or is not a file."""
    root = root.resolve()
    candidate = (root / relative.lstrip("/")).resolve()
    if candidate.is_relative_to(root) and candidate.is_file():
        return candidate
    return None


class ChitHandler(BaseHTTPRequestHandler):
    server_version = "ChitHub/0.2"

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PUT(self) -> None:
        self._dispatch("PUT")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    def _dispatch(self, method: str) -> None:
        parts = urlsplit(self.path)
        path = parts.path
        try:
            if path.startswith("/api/"):
                self._api(method, path, parts.query)
            elif method == "GET":
                self._static(path)
            else:
                raise HTTPError(405, "Method not allowed")
        except HTTPError as error:
            self._json(error.status, {"error": error.message})
        except Exception as error:  # never leak internals to the client
            self.log_error("unhandled %s: %s", type(error).__name__, error)
            self._json(500, {"error": "Internal error"})

    def _api(self, method: str, path: str, query: str) -> None:
        router: Router = self.server.router
        resolved = router.resolve(method, path)
        if resolved is None:
            raise HTTPError(405 if router.has_path(path) else 404, "Not found")
        handler, params = resolved
        body = b""
        if method in {"POST", "PUT"}:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise HTTPError(400, "Invalid Content-Length") from None
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise HTTPError(413, "Request body must be between 1 byte and 1 MiB")
            body = self.rfile.read(length)
        request = Request(method, path, parse_query(query), self.headers.get_content_type(), body, params,
                          {name.lower(): value for name, value in self.headers.items()})
        ctx = Context(store=self.server.store, manifests=self.server.manifests, log=lambda message: self.log_error("%s", message),
                      read=self._reader())
        status, payload = handler(ctx, request)
        self._json(status, payload)

    def _reader(self):
        """In-process GET of a public read API. Resolves in the hub's full router even when this listener (the phone gateway) serves less."""
        full: Router = getattr(self.server, "full_router", self.server.router)

        def read(path: str, query: "dict | None" = None) -> dict:
            resolved = full.resolve("GET", path)
            if resolved is None:
                raise HTTPError(404, "No such read API")
            handler, params = resolved
            ctx = Context(store=self.server.store, manifests=self.server.manifests, log=lambda message: self.log_error("%s", message), read=read)
            status, payload = handler(ctx, Request("GET", path, dict(query or {}), "", b"", params, {}))
            return payload
        return read

    def _static(self, path: str) -> None:
        root = getattr(self.server, "static_root", WEB_DIST)
        allow = getattr(self.server, "static_allow", None)   # the phone gateway serves an explicit list of files only
        file_path = safe_file(root, path) if path != "/" else None
        if file_path is not None and allow is not None and file_path.relative_to(root.resolve()).as_posix() not in allow:
            file_path = None
        if file_path is None:
            if "." in path.rsplit("/", 1)[-1] and path != "/":
                raise HTTPError(404, "Not found")
            # Single-page app: unknown routes fall back to the shell.
            file_path = safe_file(root, "index.html")
            if file_path is None:
                raise HTTPError(503, "Web client not built. Run `npm run build` or use `npm run dev`.")
        self._file(file_path)

    def _file(self, file_path: Path) -> None:
        content = file_path.read_bytes()
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
            mime += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        for name, value in {**SECURITY_HEADERS, **getattr(self.server, "extra_headers", {})}.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, content: dict) -> None:
        body = json.dumps(content).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in {**SECURITY_HEADERS, **getattr(self.server, "extra_headers", {})}.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        message = format % args
        if "POST" in message or "PUT" in message:
            message = message.split(" HTTP/")[0] + " [request details omitted]"
        super().log_message("%s", message)


def make_server(store, host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ChitHandler)
    server.daemon_threads = True
    server.store = store
    server.manifests = registry.load_manifests()
    server.router = build_router(server.manifests)
    return server


def main() -> None:
    from chit_store import EncryptedHouseholdStore

    store = EncryptedHouseholdStore()
    if store.plain and os.environ.get("CHIT_SEED", "1") != "0" and store.latest_household_id() is None:
        from .seed import seed_all  # dev convenience, ADR-0010

        print("Empty development database seeded: %s" % seed_all(store))
    server = make_server(store)
    print("Chit hub: http://%s:%d  (loopback only, ADR-0007)" % (HOST, PORT))
    from . import gateway

    if gateway.enabled():
        gateway.start(store, server.manifests, server.router)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Chit hub")
    finally:
        server.server_close()
