from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .models import ActionSpec, Reaction


class GiftMatch(BaseModel):
    name: str | None = None
    id: int | None = None
    min_coins: int = 1

    def matches(self, gift_name: str, gift_id: int, total_coins: int) -> bool:
        if self.id is not None:
            return gift_id == self.id
        if self.name is not None:
            return gift_name.casefold() == self.name.casefold()
        return total_coins >= self.min_coins


class ActionConfig(BaseModel):
    command: str
    params: dict[str, Any] = Field(default_factory=dict)


class PowerConfig(BaseModel):
    mod: str = ""
    key: str | None = None  # Gojo powers-mod keybind to simulate (e.g. "I")


class ReactionConfig(BaseModel):
    id: str
    label: str
    gift: GiftMatch
    action: ActionConfig
    power: PowerConfig | None = None
    voice_clip: str | None = None
    overlay_cue: str | None = None
    cooldown_s: float = 5.0

    def to_reaction(self) -> Reaction:
        return Reaction(
            id=self.id,
            label=self.label,
            action=ActionSpec(
                command=self.action.command,
                params=dict(self.action.params),
                key=(self.power.key if self.power else None),
            ),
            voice_clip=self.voice_clip,
            overlay_cue=self.overlay_cue,
            cooldown_s=self.cooldown_s,
        )


class AppConfig(BaseModel):
    tiktok_username: str
    timezone: str = "America/Sao_Paulo"
    global_min_interval_s: float = 1.5
    reactions: list[ReactionConfig]


def load_config(path: str | Path) -> AppConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig.model_validate(data)
