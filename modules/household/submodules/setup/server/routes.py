"""Household setup and edit: one document shape for create, read and edit (ADR-0010)."""
from __future__ import annotations

from chit_server.registry import validate_module_selection
from chit_server.router import HTTPError


def _document(ctx, request):
    body = request.json()
    if not isinstance(body, dict):
        raise HTTPError(400, "Request body must be a JSON object")
    try:
        return validate_module_selection(ctx.manifests, body)
    except ValueError as error:
        raise HTTPError(400, str(error)) from None


def summary(ctx, request):
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return 200, {"state": "unconfigured"}
    document = ctx.store.get_household_document(household_id)
    members = [{"id": m["client_id"], "name": m["name"], "role": m["role"], "avatar": m.get("avatar"),
                "color": m.get("color")} for m in document["members"]]
    return 200, {"state": "configured", "household": {
        "id": household_id, "name": document["household"]["name"], "members": members,
        "modules": document["modules"],
    }}


def current(ctx, request):
    """The latest household that was set up, as an editable document."""
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return 200, {"state": "unconfigured"}
    return 200, {"state": "configured", "document": ctx.store.get_household_document(household_id)}


def read(ctx, request):
    try:
        return 200, {"state": "configured", "document": ctx.store.get_household_document(request.params["id"])}
    except LookupError:
        raise HTTPError(404, "Household not found") from None


def setup(ctx, request):
    document = _document(ctx, request)
    try:
        return 201, ctx.store.save_household_setup(document)
    except ValueError as error:
        raise HTTPError(400, str(error)) from None
    except Exception as error:
        ctx.log("setup save failed: %s: %s" % (type(error).__name__, error))
        raise HTTPError(400, "Setup could not be saved; check required fields and assignments") from None


def edit(ctx, request):
    document = _document(ctx, request)
    try:
        return 200, ctx.store.update_household(request.params["id"], document)
    except LookupError:
        raise HTTPError(404, "Household not found") from None
    except ValueError as error:
        raise HTTPError(400, str(error)) from None
    except Exception as error:
        ctx.log("household edit failed: %s: %s" % (type(error).__name__, error))
        raise HTTPError(400, "Changes could not be saved; check required fields and assignments") from None


def register(router) -> None:
    router.get("/api/household/summary")(summary)
    router.get("/api/household/current")(current)
    router.get("/api/household/{id}")(read)
    router.post("/api/household/setup")(setup)
    router.put("/api/household/{id}")(edit)
