"""The latest household and its local clock, for energy routes."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def latest(ctx):
    """-> (household_id, document, local now) or (None, None, None) when nothing is set up."""
    household_id = ctx.store.latest_household_id()
    if household_id is None:
        return None, None, None
    document = ctx.store.get_household_document(household_id)
    return household_id, document, datetime.now(ZoneInfo(document["household"]["timezone"]))
