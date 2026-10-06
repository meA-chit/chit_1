# UI composition

## Units
- **Card** — the unit of composition: a self-contained widget with sizes (s/m/l/xl), supported surfaces, permissions and all data states. Modules register cards in the manifest.
- **View** — a full-screen page for a module or submodule.
- **Shell** (`core/web`) — reads effective enablement and layout, loads registered cards, arranges them. It knows nothing about card internals.

## Layout
A layout is data: ordered card slots per household and surface, optionally per member. Defaults come from presets; users rearrange within what is enabled.

## Per-surface design
- **tv**: 5-7 large cards, high contrast, glanceable from a distance, screen-safe, no actions.
- **tablet/web**: denser, interactive, management.
- **mobile**: single-column, stackable cards, notification entry points.
- **mobile-kid**: simplified, age-appropriate, only adult-enabled cards.

## Card requirements
Renders `available`, `stale`, `partial`, `unavailable`, `unconfigured`, demo; shows source and freshness; no hidden dependencies on other modules' DOM or state; accessible (contrast, keyboard, touch targets).

## Design system
Shared tokens and primitives live in `core/web`; modules compose them and do not fork them.
