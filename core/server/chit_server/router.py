from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any, Callable
from urllib.parse import parse_qs

MAX_REQUEST_BYTES = 1_048_576


class HTTPError(Exception):
    def __init__(self, status: int, message: str, extra: "dict[str, Any] | None" = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.extra = extra or {}      # machine-readable fields sent next to "error" (the sign-in screens read them)


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, str]
    content_type: str
    body: bytes = b""
    params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)   # lower-case names
    client: str = ""                                         # caller's address (rate limits only; never stored raw)
    session: Any = None                                      # the signed-in account's session, when sign-in is on

    def json(self) -> Any:
        if self.content_type != "application/json":
            raise HTTPError(415, "Content-Type must be application/json")
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HTTPError(400, "Request body must be valid JSON") from None


@dataclass
class Context:
    """Services handed to every route. Modules get the store through here, never by import."""
    store: Any
    manifests: dict[str, Any] = field(default_factory=dict)
    log: Callable[[str], None] = lambda message: None
    # Public read APIs of other modules (docs/core/cross-module-contracts.md, rule 1): read("/api/planner/calendar/agenda") calls the owner's
    # GET route in-process and returns its payload. Only what the owner lists in its contracts.md may be read this way.
    read: "Callable[[str, dict | None], dict] | None" = None
    # Extra response headers a route wants sent (the sign-in routes set the session cookie here).
    response_headers: "list[tuple[str, str]]" = field(default_factory=list)


Handler = Callable[[Context, Request], "tuple[int, dict[str, Any]]"]


@dataclass
class Router:
    routes: dict[tuple[str, str], Handler] = field(default_factory=dict)
    patterns: list[tuple[str, re.Pattern, str, Handler]] = field(default_factory=list)

    def add(self, method: str, path: str, handler: Handler) -> None:
        if "{" in path:
            regex = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[A-Za-z0-9_-]{1,64})", path) + "$")
            self.patterns.append((method, regex, path, handler))
            return
        if (method, path) in self.routes:
            raise ValueError("duplicate route %s %s" % (method, path))
        self.routes[(method, path)] = handler

    def get(self, path: str) -> Callable[[Handler], Handler]:
        return self._decorator("GET", path)

    def post(self, path: str) -> Callable[[Handler], Handler]:
        return self._decorator("POST", path)

    def put(self, path: str) -> Callable[[Handler], Handler]:
        return self._decorator("PUT", path)

    def delete(self, path: str) -> Callable[[Handler], Handler]:
        return self._decorator("DELETE", path)

    def _decorator(self, method: str, path: str) -> Callable[[Handler], Handler]:
        def wrap(handler: Handler) -> Handler:
            self.add(method, path, handler)
            return handler
        return wrap

    def resolve(self, method: str, path: str) -> "tuple[Handler, dict[str, str]] | None":
        """Exact routes win over patterns, so /api/household/current is never read as {id}."""
        handler = self.routes.get((method, path))
        if handler:
            return handler, {}
        for route_method, regex, _, pattern_handler in self.patterns:
            match = regex.match(path)
            if route_method == method and match:
                return pattern_handler, match.groupdict()
        return None

    def has_path(self, path: str) -> bool:
        return any(route_path == path for _, route_path in self.routes) or any(
            regex.match(path) for _, regex, _, _ in self.patterns)


class ModuleRouter:
    """Router view handed to one module. Routes must live under /api/<module-id>/."""

    def __init__(self, router: Router, module_id: str):
        self._router = router
        self._prefix = "/api/%s/" % module_id

    def get(self, path: str) -> Callable[[Handler], Handler]:
        return self._scoped("GET", path)

    def post(self, path: str) -> Callable[[Handler], Handler]:
        return self._scoped("POST", path)

    def put(self, path: str) -> Callable[[Handler], Handler]:
        return self._scoped("PUT", path)

    def delete(self, path: str) -> Callable[[Handler], Handler]:
        return self._scoped("DELETE", path)

    def _scoped(self, method: str, path: str) -> Callable[[Handler], Handler]:
        if not path.startswith(self._prefix):
            raise ValueError("module route %r must start with %s" % (path, self._prefix))
        return self._router._decorator(method, path)


def parse_query(raw: str) -> dict[str, str]:
    return {key: values[-1] for key, values in parse_qs(raw).items()}
