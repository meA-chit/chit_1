"""The sign-in gate in front of every API route (ADR-0014). Off by default (the local hub has no accounts, ADR-0007); the
hosted profile turns it on with CHIT_AUTH=1, after which only the routes listed below are reachable without a session.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

from .router import HTTPError, Request

COOKIE = "chit_session"
UNSAFE = {"POST", "PUT", "DELETE", "PATCH"}
# Reachable without a session: the health probe, the sign-in routes (they check what they need themselves), and the kid phone's
# own routes, which carry a device token instead (ADR-0012).
PUBLIC_PATHS = {"/api/health"}
DEVICE_PREFIX = "/api/kids/phone/device/"
AUTH_PREFIX = "/api/auth/"


@dataclass
class AuthSettings:
    cookie_secure: bool = True                    # False only for plain-http local development
    trusted_proxy_hops: int = 0                   # how many proxies in front of us set X-Forwarded-For (Cloud Run: 1)
    allowed_origins: frozenset = field(default_factory=frozenset)
    terms_url: str = ""
    cookie_max_age: int = 30 * 24 * 3600


class AuthGate:
    def __init__(self, accounts, settings: "AuthSettings | None" = None):
        self.accounts = accounts
        self.settings = settings or AuthSettings()

    def cookie_header(self, token: str) -> "tuple[str, str]":
        value = "%s=%s; HttpOnly; SameSite=Lax; Path=/; Max-Age=%d" % (COOKIE, token, self.settings.cookie_max_age)
        return "Set-Cookie", value + ("; Secure" if self.settings.cookie_secure else "")

    def clearing_cookie_header(self) -> "tuple[str, str]":
        value = "%s=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0" % COOKIE
        return "Set-Cookie", value + ("; Secure" if self.settings.cookie_secure else "")


def session_token(request: Request) -> "str | None":
    raw = request.headers.get("cookie", "")
    if not raw:
        return None
    jar = SimpleCookie()
    try:
        jar.load(raw)
    except Exception:
        return None
    morsel = jar.get(COOKIE)
    return morsel.value if morsel else None


def _origin_ok(auth: AuthGate, request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:                       # not a browser form/fetch from another site; cookies would not have been attached anyway
        return True
    netloc = urlsplit(origin).netloc
    hosts = [request.headers.get("host", "")]
    if auth.settings.trusted_proxy_hops:                # behind our own proxy the public hostname arrives as X-Forwarded-Host
        hosts.append(request.headers.get("x-forwarded-host", "").split(",")[0].strip())
    return origin in auth.settings.allowed_origins or netloc in hosts


def gate(auth: AuthGate, request: Request, path: str, method: str) -> "str | None":
    """Attach the session to the request and return the household this request may serve (None: none)."""
    token = session_token(request)
    session = auth.accounts.authenticate(token) if token else None
    request.session = session
    if token and method in UNSAFE and not _origin_ok(auth, request):
        raise HTTPError(403, "bad_origin")
    if path in PUBLIC_PATHS or path.startswith(DEVICE_PREFIX):
        return None
    if path.startswith(AUTH_PREFIX):
        return session.household_id if session else None
    if session is None:
        raise HTTPError(401, "auth_required")
    if not session.terms_ok:
        raise HTTPError(403, "terms_required", {"terms_version": auth.accounts.terms_version})
    if not session.household_id:
        raise HTTPError(409, "household_required")
    return session.household_id


def from_env(store) -> "AuthGate | None":
    """CHIT_AUTH=1 turns sign-in on. Needs the postgres backend."""
    if os.environ.get("CHIT_AUTH") != "1":
        return None
    from chit_store import mailer
    from chit_store.accounts import Accounts

    accounts = Accounts(store, mailer.from_env(), os.environ.get("CHIT_TERMS_VERSION", "2026-10-beta-1"),
                        pepper=os.environ.get("CHIT_AUTH_PEPPER", ""))
    origins = frozenset(o.strip() for o in os.environ.get("CHIT_ALLOWED_ORIGINS", "").split(",") if o.strip())
    settings = AuthSettings(cookie_secure=os.environ.get("CHIT_COOKIE_SECURE", "1") != "0",
                            trusted_proxy_hops=int(os.environ.get("CHIT_TRUSTED_PROXY_HOPS", "0")),
                            allowed_origins=origins, terms_url=os.environ.get("CHIT_TERMS_URL", ""))
    return AuthGate(accounts, settings)
