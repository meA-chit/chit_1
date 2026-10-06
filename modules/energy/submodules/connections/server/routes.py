"""Energy connections (energy/connections): the Tibber token and the SolarEdge site, set in the household energy settings.

A key is verified against the provider before it is stored. Nothing here ever returns a key: the web client only
sees whether a provider is connected, a masked hint of the last four characters and non-secret details.
"""
from __future__ import annotations

from pathlib import Path

from chit_server.loader import load_file_module
from chit_server.router import HTTPError

shared = Path(__file__).parents[3] / "shared"
tibber = load_file_module(shared / "tibber.py")
solaredge = load_file_module(shared / "solaredge.py")
net = load_file_module(shared / "net.py")
household = load_file_module(shared / "household.py")

MESSAGES = {
    "auth": "The provider did not accept that key. Check it and try again.",
    "rate_limited": "The provider's request limit was reached. Try again in a few minutes.",
    "unavailable": "Could not reach the provider just now. Nothing was saved, try again.",
}


def _status(stored):
    out = {"tibber": {"connected": False}, "solaredge": {"connected": False}}
    for provider, row in stored.items():
        config = row["config"]
        if provider == "tibber":
            out["tibber"] = {"connected": True, "hint": row["hint"], "homes": config.get("homes")}
        elif provider == "solaredge":
            out["solaredge"] = {"connected": True, "hint": row["hint"], "site_id": config.get("site_id"),
                                "site_name": config.get("site_name"), "peak_kw": config.get("peak_kw")}
    return out


def _household_id(ctx):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        raise HTTPError(404, "Set up a household first")
    return household_id


def _text(body, field, limit):
    value = body.get(field) if isinstance(body, dict) else None
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise HTTPError(400, "%s is required" % field.replace("_", " "))
    return value.strip()


def status(ctx, request):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return 200, {"state": "unconfigured", **_status({})}
    return 200, {"state": "ready", **_status(ctx.store.list_energy_connections(household_id))}


def connect_tibber(ctx, request):
    household_id = _household_id(ctx)
    token = _text(request.json(), "token", 200)
    try:
        found = tibber.verify(token)
    except net.ProviderError as error:
        raise HTTPError(400 if error.kind == "auth" else 502, MESSAGES[error.kind]) from None
    ctx.store.set_energy_connection(household_id, "tibber", token, {"home_id": found["home_id"], "homes": found["homes"]})
    return 200, {"state": "ready", **_status(ctx.store.list_energy_connections(household_id))}


def connect_solaredge(ctx, request):
    household_id = _household_id(ctx)
    body = request.json()
    site_id = _text(body, "site_id", 20)
    if not site_id.isdigit():
        raise HTTPError(400, "The site id is the number in your SolarEdge monitoring URL")
    api_key = _text(body, "api_key", 100)
    try:
        found = solaredge.verify(site_id, api_key)
    except net.ProviderError as error:
        raise HTTPError(400 if error.kind == "auth" else 502, MESSAGES[error.kind]) from None
    ctx.store.set_energy_connection(household_id, "solaredge", api_key,
                                    {"site_id": site_id, "site_name": found["name"], "peak_kw": found["peak_kw"]})
    return 200, {"state": "ready", **_status(ctx.store.list_energy_connections(household_id))}


def disconnect(ctx, request):
    household_id = _household_id(ctx)
    provider = request.params["provider"]
    if provider not in ("tibber", "solaredge"):
        raise HTTPError(404, "Unknown provider")
    ctx.store.delete_energy_connection(household_id, provider)
    return 200, {"state": "ready", **_status(ctx.store.list_energy_connections(household_id))}


def register(router) -> None:
    router.get("/api/energy/connections")(status)
    router.put("/api/energy/connections/tibber")(connect_tibber)
    router.put("/api/energy/connections/solaredge")(connect_solaredge)
    router.delete("/api/energy/connections/{provider}")(disconnect)
