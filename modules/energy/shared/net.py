"""Outbound HTTP for the energy providers, plus a small cache with stale fallback.

The browser never talks to a provider (ADR-0007); the hub does, so keys never leave it. Error messages never
include the URL because SolarEdge puts its key in the query string.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import time
from urllib.error import HTTPError as UrlHTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(Exception):
    """kind: auth (key rejected) | rate_limited | unavailable (network or provider problem)."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def request_json(url: str, *, body: "dict | None" = None, headers: "dict | None" = None, timeout: int = 10, max_bytes: int = 2_000_000):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=data, headers={"User-Agent": "Chit-Energy/1.0", "Accept": "application/json",
                                               **({"Content-Type": "application/json"} if data else {}), **(headers or {})})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read(max_bytes).decode("utf-8"))
    except UrlHTTPError as error:
        payload = ""
        try:
            payload = error.read(2000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 - best effort, only used to classify the failure
            pass
        if error.code in (401, 403) or (error.code == 400 and ("token" in payload.lower() or "UNAUTHENTICATED" in payload)):
            raise ProviderError("auth", "the provider rejected the key") from None
        if error.code == 429:
            raise ProviderError("rate_limited", "the provider's request limit was reached") from None
        raise ProviderError("unavailable", "the provider answered with HTTP %d" % error.code) from None
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise ProviderError("unavailable", "could not reach the provider (%s)" % type(error).__name__) from None


def fingerprint(*parts: str) -> str:
    """Cache key part for a credential, so the secret itself is not used as a dictionary key."""
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:16]


class Cache:
    """key -> (monotonic time, wall time, value). A failed refresh returns the last good value flagged stale."""

    def __init__(self):
        self.items: dict = {}

    def clear(self) -> None:
        self.items.clear()

    def fetch(self, key, ttl_seconds: int, producer):
        cached = self.items.get(key)
        if cached and time.monotonic() - cached[0] < ttl_seconds:
            return cached[2], cached[1], False
        try:
            value = producer()
        except ProviderError as error:
            if cached and error.kind != "auth":
                return cached[2], cached[1], True
            raise
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.items[key] = (time.monotonic(), stamp, value)
        return value, stamp, False


CACHE = Cache()
