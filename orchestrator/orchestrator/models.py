from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ActionSpec:
    command: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GiftEvent:
    user_id: str
    username: str
    gift_id: int
    gift_name: str
    coins: int
    count: int
    timestamp: float
    is_combo_end: bool = True

    @property
    def total_coins(self) -> int:
        return self.coins * self.count


@dataclass(frozen=True, slots=True)
class Reaction:
    id: str
    label: str
    action: ActionSpec
    voice_clip: str | None
    overlay_cue: str | None
    cooldown_s: float
