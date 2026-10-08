"""The icon for an activity or calendar event, chosen from its name (config/event-icons.json).

Used by every screen that shows activities or events, so one football training looks the same on the dashboard, the family calendar and the
child's phone. Pure and offline: nothing is looked up, a name that matches no rule falls back to its calendar category, then to no icon.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from .paths import CONFIG_DIR

FILE = CONFIG_DIR / "event-icons.json"


def _fold(text: str) -> str:
    """Lower case, accents removed and ß written ss, so 'Fußball' and 'Fussball' and 'FÜSSBALL' are the same word."""
    text = text.lower().replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def _rules() -> "tuple[list[tuple[str, tuple[str, ...]]], dict[str, str]]":
    data = json.loads(FILE.read_text(encoding="utf-8"))
    rules = [(rule["icon"], tuple(_fold(word) for word in rule["words"])) for rule in data.get("rules", [])]
    return rules, dict(data.get("categories", {}))


def reload() -> None:
    _rules.cache_clear()


def icon_for(text: "str | None", category: "str | None" = None) -> "str | None":
    """The emoji for `text` (an activity name or event title), else the category's icon, else None."""
    rules, categories = _rules()
    folded = _fold(text or "")
    tokens = set(re.findall(r"[a-z0-9]+", folded))
    for icon, words in rules:
        for word in words:
            # short words must be a whole word (so 'ag' is not found in 'magic'); longer ones also match inside German compounds
            if (word in tokens) if len(word) < 4 else (word in folded):
                return icon
    return categories.get(category or "")
