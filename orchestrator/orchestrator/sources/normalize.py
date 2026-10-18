from __future__ import annotations

import time
from typing import Any, Callable

from ..models import GiftEvent


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    value = getattr(obj, name, default)
    return value if value is not None else default


def normalize_gift(event: Any, now: Callable[[], float] = time.time) -> GiftEvent:
    """Convert a TikTokLive GiftEvent into our normalized GiftEvent.

    Duck-typed against the real v7 model (gift.name/id/diamond_count/streakable,
    user.id/nickname/display_id, event.repeat_count, event.streaking) so it can be
    unit-tested with plain stand-in objects and survives minor library field changes.

    ``is_combo_end`` is ``not event.streaking``: a streakable gift reports
    ``streaking=True`` while the combo is ongoing (we drop those upstream) and
    ``False`` on the terminal event (where ``repeat_count`` is the full total);
    a non-streak gift reports ``streaking=False`` and fires once.
    """
    gift = getattr(event, "gift", None)
    user = getattr(event, "user", None)
    streaking = bool(getattr(event, "streaking", False))

    gift_name = str(_attr(gift, "name", "") or "")
    gift_id = int(_attr(gift, "id", 0) or getattr(event, "gift_id", 0) or 0)
    coins = int(_attr(gift, "diamond_count", 0) or 0)
    count = int(getattr(event, "repeat_count", 1) or 1)

    username = str(_attr(user, "nickname", "") or _attr(user, "display_id", "") or "anon")
    user_id = str(_attr(user, "id", "") or _attr(user, "sec_uid", "") or username)

    return GiftEvent(
        user_id=user_id,
        username=username,
        gift_id=gift_id,
        gift_name=gift_name,
        coins=coins,
        count=count,
        timestamp=now(),
        is_combo_end=not streaking,
    )
