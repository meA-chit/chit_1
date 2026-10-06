from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .loader import load_file_module
from .paths import CONFIG_DIR, MODULES_DIR
from .router import ModuleRouter, Router

SURFACES = {"tv", "tablet", "web", "mobile-adult", "mobile-kid"}
DATA_STATES = {"available", "stale", "partial", "unavailable", "unconfigured", "demo", "manual", "forecast"}
SLOTS = {"topbar", "timeline", "left", "center", "right"}
PRIVACY_RANK = {"normal": 0, "sensitive": 1, "strict": 2}


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_manifests(modules_dir: Path = MODULES_DIR) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted(modules_dir.glob("*/module.manifest.yaml")):
        manifest = _read_yaml(path)
        if manifest.get("id") != path.parent.name:
            raise ValueError("%s: id must equal the folder name" % path)
        _validate(manifest, path)
        manifests[manifest["id"]] = manifest
    for manifest in manifests.values():
        for dependency in manifest.get("depends_on", []):
            if dependency != "core" and dependency not in manifests:
                raise ValueError("module %s depends on unknown module %s" % (manifest["id"], dependency))
    return manifests


def _validate(manifest: dict[str, Any], path: Path) -> None:
    submodules = {sub["id"] for sub in manifest.get("submodules", [])}
    for kind in ("cards", "views", "settings_sections"):
        for item in manifest.get(kind, []):
            if item.get("submodule") not in submodules:
                raise ValueError("%s: %s %r references an unknown submodule" % (path, kind, item.get("id")))
            unknown = set(item.get("surfaces", [])) - SURFACES
            if unknown:
                raise ValueError("%s: %s %r has unknown surfaces %s" % (path, kind, item.get("id"), sorted(unknown)))
    for card in manifest.get("cards", []):
        if card.get("slot") not in SLOTS:
            raise ValueError("%s: card %r needs a slot from %s" % (path, card["id"], sorted(SLOTS)))
        unknown = set(card.get("data_states", [])) - DATA_STATES
        if unknown:
            raise ValueError("%s: card %r uses undefined data states %s" % (path, card["id"], sorted(unknown)))


def register_routes(router: Router, manifests: dict[str, dict[str, Any]], modules_dir: Path = MODULES_DIR) -> None:
    """Load `modules/<m>/submodules/<s>/server/routes.py` and call its register(router)."""
    for module_id, manifest in manifests.items():
        for submodule in manifest.get("submodules", []):
            routes_file = modules_dir / module_id / "submodules" / submodule["id"] / "server" / "routes.py"
            if not routes_file.is_file():
                continue
            loaded = load_file_module(routes_file)
            register = getattr(loaded, "register", None)
            if register is None:
                raise ValueError("%s must define register(router)" % routes_file)
            register(ModuleRouter(router, module_id))


def load_surface(surface: str) -> dict[str, Any]:
    if surface not in SURFACES:
        raise ValueError("unknown surface")
    return _read_yaml(CONFIG_DIR / "surfaces" / ("%s.yaml" % surface))


def load_preset(preset: "str | None") -> "dict[str, Any] | None":
    if not preset:
        return None
    if not preset.replace("-", "").isalnum():
        raise ValueError("unknown preset")
    path = CONFIG_DIR / "household-presets" / ("%s.yaml" % preset)
    if not path.is_file():
        raise ValueError("unknown preset")
    return _read_yaml(path)


def module_catalog(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """What a household can switch on. `household` is the foundation and cannot be switched off."""
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "short_title": m.get("short_title", m["title"]),
            "status": m.get("status", "structure-only"),
            "privacy_class": m.get("privacy_class", "normal"),
            "audiences": m.get("audiences", []),
            "depends_on": [d for d in m.get("depends_on", []) if d != "core"],
            "submodules": [sub["id"] for sub in m.get("submodules", [])],
            "required": m["id"] == "household",
        }
        for m in manifests.values()
    ]


def validate_module_selection(manifests: dict[str, dict[str, Any]], document: dict[str, Any]) -> dict[str, Any]:
    """Check a household document's `modules` (and each member's) against the manifests; returns it normalised."""
    modules = document.get("modules")
    if modules is not None:
        unknown = set(modules) - set(manifests)
        if unknown:
            raise ValueError("unknown modules: %s" % ", ".join(sorted(unknown)))
        modules = sorted(set(modules) | {"household"})
        for module_id in modules:
            missing = [d for d in manifests[module_id].get("depends_on", []) if d != "core" and d not in modules]
            if missing:
                raise ValueError("%s needs %s to be enabled" % (manifests[module_id]["title"], ", ".join(missing)))
        document["modules"] = modules
    for member in document.get("members", []):
        listed = member.get("modules")
        if listed is None:
            continue
        unknown = set(listed) - set(manifests)
        if unknown:
            raise ValueError("unknown modules: %s" % ", ".join(sorted(unknown)))
        for module_id in listed:
            if member.get("role") not in manifests[module_id].get("audiences", []):
                raise ValueError("%s is not available to %s members" % (manifests[module_id]["title"], member.get("role")))
    return document


def resolve_shell(manifests: dict[str, dict[str, Any]], surface: str, preset: "str | None" = None,
                  store: Any = None, member_id: "str | None" = None) -> dict[str, Any]:
    """Enablement layers 1-5 (docs/core/enablement-and-audiences.md); module level.

    1 platform defaults: every module. 2 preset: only when no household exists to override it.
    3 latest household's stored modules. 4 member narrowing (view-as; becomes identity with the auth ADR).
    5 surface profile. Nothing here names who sees what.
    Submodule-level enablement is not stored yet.
    """
    surface_cfg = load_surface(surface)
    preset_cfg = load_preset(preset)
    household = None
    members: list[dict[str, str]] = []
    member = None
    enabled = set(preset_cfg["modules"]) if preset_cfg else set(manifests)
    household_id = store.latest_household_id() if store is not None else None
    if household_id is not None:
        enablement = store.household_enablement(household_id)
        document = store.get_household_document(household_id)
        household = {"id": household_id, "name": document["household"]["name"]}
        members = [{"id": m["client_id"], "name": m["name"], "role": m["role"], "avatar": m.get("avatar"),
                    "color": m.get("color")} for m in document["members"]]
        if enablement["modules"] is not None:
            enabled = set(enablement["modules"]) | {"household"}
        if member_id:
            info = enablement["members"].get(member_id)
            if info is None:
                raise ValueError("unknown member")
            member = next(m for m in members if m["id"] == member_id)
            if info["modules"] is not None:
                enabled &= info["modules"]
            enabled = {m for m in enabled if info["role"] in manifests[m].get("audiences", [])}
    elif store is not None:
        enabled = {"household"}  # nothing is set up yet: only the way to set it up
    enabled &= set(manifests)
    hide_sensitive = surface_cfg.get("sensitive_modules") == "hidden"

    def allowed(module_id: str, item: dict[str, Any]) -> bool:
        privacy = item.get("privacy_class", manifests[module_id].get("privacy_class", "normal"))
        return (
            module_id in enabled
            and surface in item.get("surfaces", [])
            and not (hide_sensitive and PRIVACY_RANK[privacy] > 0)
        )

    cards, views, sections = [], [], []
    for module_id, manifest in manifests.items():
        for card in manifest.get("cards", []):
            if allowed(module_id, card):
                cards.append({**card, "module": module_id})
        for view in manifest.get("views", []):
            if allowed(module_id, view):
                views.append({**view, "module": module_id})
        for section in manifest.get("settings_sections", []):
            if allowed(module_id, section):
                sections.append({**section, "module": module_id})
    sections.sort(key=lambda section: section.get("order", 100))
    cards.sort(key=lambda card: card.get("order", 100))
    max_cards = surface_cfg.get("max_cards")
    if max_cards:
        cards = cards[:max_cards]
    return {
        "surface": surface,
        "preset": preset,
        "screen_safe": bool(surface_cfg.get("screen_safe")),
        "interactive": bool(surface_cfg.get("interactive")),
        "household": household,
        "member": member,
        "members": members,
        "modules": [
            {"id": m["id"], "title": m["title"], "short_title": m.get("short_title", m["title"]),
             "privacy_class": m.get("privacy_class", "normal")}
            for module_id, m in sorted(manifests.items(), key=lambda item: item[1].get("nav_order", 100)) if module_id in enabled
        ],
        "cards": cards,
        "views": views,
        "settings_sections": sections,
    }
