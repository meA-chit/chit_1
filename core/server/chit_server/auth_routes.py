"""Sign-in routes (ADR-0014): /api/auth/*. Registered only when sign-in is on."""
from __future__ import annotations

import functools
from typing import Any

from chit_store.accounts import AuthError

from .auth_gate import AuthGate
from .router import Context, HTTPError, Request, Router


def _body(request: Request) -> dict[str, Any]:
    data = request.json()
    if not isinstance(data, dict):
        raise HTTPError(400, "Request body must be a JSON object")
    return data


def _guard(handler):
    """Turn the accounts service's errors into HTTP answers with a machine-readable code and a human message."""
    @functools.wraps(handler)
    def wrapped(ctx: Context, request: Request):
        try:
            return handler(ctx, request)
        except AuthError as error:
            raise HTTPError(error.status, error.code, {"message": error.message, **error.extra}) from None
    return wrapped


def _session(request: Request):
    if request.session is None:
        raise HTTPError(401, "auth_required")
    return request.session


def _ready(request: Request):
    """A session that may act on a household: signed in, Terms accepted, a household chosen."""
    session = _session(request)
    if not session.terms_ok:
        raise HTTPError(403, "terms_required")
    if not session.household_id:
        raise HTTPError(409, "household_required")
    return session


def register(router: Router, gate: AuthGate) -> None:
    accounts = gate.accounts

    def route(method: str, path: str):
        def wrap(handler):
            router.add(method, path, _guard(handler))
            return handler
        return wrap

    @route("GET", "/api/auth/terms")
    def terms(ctx, request):
        return 200, {"version": accounts.terms_version, "url": gate.settings.terms_url}

    # --- enrolment: invitation, Terms, email -------------------------------------------------------------
    @route("POST", "/api/auth/pairing/redeem")
    def redeem(ctx, request):
        data = _body(request)
        return 200, {"enrolment": accounts.redeem_pairing(str(data.get("link", "")), str(data.get("code", "")), request.client)}

    @route("POST", "/api/auth/enrol/email")
    def enrol_email(ctx, request):
        data = _body(request)
        accounts.enrol_send_code(str(data.get("enrolment", "")), data.get("email"), data.get("accept_terms"), data.get("terms_version"), request.client)
        return 202, {"sent": True}

    @route("POST", "/api/auth/enrol/verify")
    def enrol_verify(ctx, request):
        data = _body(request)
        token, info = accounts.enrol_complete(str(data.get("enrolment", "")), data.get("email"), str(data.get("code", "")), request.client,
                                              request.headers.get("user-agent", ""))
        ctx.response_headers.append(gate.cookie_header(token))
        return 200, {"signed_in": True, **info}

    # --- sign-in with an emailed code ---------------------------------------------------------------------
    @route("POST", "/api/auth/login/start")
    def login_start(ctx, request):
        accounts.login_send_code(_body(request).get("email"), request.client)
        return 202, {"sent": True}                    # the same answer whether or not the address has an account

    @route("POST", "/api/auth/login/verify")
    def login_verify(ctx, request):
        data = _body(request)
        token = accounts.login_verify(data.get("email"), str(data.get("code", "")), request.client, request.headers.get("user-agent", ""))
        ctx.response_headers.append(gate.cookie_header(token))
        return 200, {"signed_in": True}

    # --- the signed-in person ---------------------------------------------------------------------------------
    @route("GET", "/api/auth/me")
    def me(ctx, request):
        return 200, accounts.me(_session(request))

    @route("POST", "/api/auth/terms/accept")
    def accept_terms(ctx, request):
        accounts.accept_terms(_session(request), _body(request).get("terms_version"))
        return 200, {"accepted": True}

    @route("POST", "/api/auth/household/select")
    def select_household(ctx, request):
        accounts.select_household(_session(request), str(_body(request).get("household_id", "")))
        return 200, {"selected": True}

    @route("POST", "/api/auth/logout")
    def logout(ctx, request):
        accounts.logout(_session(request))
        ctx.response_headers.append(gate.clearing_cookie_header())
        return 200, {"signed_out": True}

    @route("GET", "/api/auth/sessions")
    def sessions(ctx, request):
        return 200, {"sessions": accounts.list_sessions(_session(request))}

    @route("DELETE", "/api/auth/sessions/{id}")
    def revoke(ctx, request):
        accounts.revoke_session(_session(request), request.params["id"])
        return 200, {"revoked": True}

    # --- confirming it is you before something sensitive -------------------------------------------------------
    @route("POST", "/api/auth/reauth/start")
    def reauth_start(ctx, request):
        accounts.reauth_send_code(_session(request), request.client)
        return 202, {"sent": True}

    @route("POST", "/api/auth/reauth/verify")
    def reauth_verify(ctx, request):
        accounts.reauth_verify(_session(request), str(_body(request).get("code", "")), request.client)
        return 200, {"confirmed": True}

    # --- the household owner's controls --------------------------------------------------------------------------
    @route("GET", "/api/auth/members")
    def members(ctx, request):
        return 200, {"members": accounts.members(_ready(request))}

    @route("POST", "/api/auth/invites")
    def invite(ctx, request):
        pairing = accounts.invite_adult(_ready(request), str(_body(request).get("member_id", "")))
        return 201, {"link": pairing["link"], "code": pairing["code"], "expires_at": pairing["expires_at"]}

    @route("POST", "/api/auth/owner/transfer")
    def transfer(ctx, request):
        accounts.transfer_ownership(_ready(request), str(_body(request).get("member_id", "")))
        return 200, {"transferred": True}
