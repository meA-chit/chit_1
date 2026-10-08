# `config/`

Example household presets and surface profiles. Real per-household enablement is stored data, not files; these are defaults. See `docs/core/enablement-and-audiences.md`.

- `event-icons.json`: which icon an activity or calendar event gets, chosen from its name (first matching rule wins; English and German words; category fallbacks). Edit it to change or add icons, no code change needed. Read by `core/server/chit_server/icons.py`.
