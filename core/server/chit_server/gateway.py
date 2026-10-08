"""The phone gateway (ADR-0012): the only listener that leaves loopback, and only when asked to (CHIT_PHONE=1).

It serves the child's phone app and the device routes under /api/kids/phone/device/. Nothing else from the hub is reachable
through it: no parent, household, finance or management routes. The hub itself stays on 127.0.0.1.
"""
from __future__ import annotations

import os
import socket
import threading
from http.server import ThreadingHTTPServer

from .app import ChitHandler
from .paths import KID_APP
from .router import Router

DEVICE_PREFIX = "/api/kids/phone/device/"
PORT = int(os.environ.get("CHIT_PHONE_PORT", "8766"))
# The only files the gateway serves from apps/kid-app.
STATIC_ALLOW = frozenset({"index.html", "sw.js", "manifest.webmanifest", "icon.svg", "icon-180.png", "icon-512.png"})
HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                               "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def enabled() -> bool:
    return os.environ.get("CHIT_PHONE") == "1"


def device_router(full: Router) -> Router:
    """A copy of `full` holding only the device routes. Parent routes are simply absent, so they answer 404."""
    narrow = Router()
    for (method, path), handler in full.routes.items():
        if path.startswith(DEVICE_PREFIX):
            narrow.add(method, path, handler)
    for method, _, path, handler in full.patterns:
        if path.startswith(DEVICE_PREFIX):
            narrow.add(method, path, handler)
    return narrow


def lan_address() -> "str | None":
    """This machine's address on the local network (no packet is sent)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def base_url() -> "str | None":
    """Where a phone reaches the gateway; None while the gateway is off. CHIT_PHONE_URL overrides (e.g. a hostname or HTTPS proxy)."""
    if not enabled():
        return None
    override = os.environ.get("CHIT_PHONE_URL", "").strip().rstrip("/")
    if override:
        return override
    address = lan_address()
    return "http://%s:%d" % (address, PORT) if address else None


def make_gateway(store, manifests, full_router: Router, host: str = "0.0.0.0", port: int = PORT) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ChitHandler)
    server.daemon_threads = True
    server.store = store
    server.manifests = manifests
    server.router = device_router(full_router)
    server.full_router = full_router           # server-side reads of public contracts; never reachable from the network
    server.static_root = KID_APP
    server.static_allow = STATIC_ALLOW
    server.extra_headers = HEADERS
    return server


def start(store, manifests, full_router: Router) -> ThreadingHTTPServer:
    server = make_gateway(store, manifests, full_router)
    threading.Thread(target=server.serve_forever, daemon=True, name="phone-gateway").start()
    print("Phone gateway: %s  (kid app and /api/kids/phone/device only; ADR-0012)" % (base_url() or "http://0.0.0.0:%d" % PORT))
    return server
