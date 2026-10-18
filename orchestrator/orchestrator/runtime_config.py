from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class TelegramCfg(BaseModel):
    bot_token: str = ""
    allowed_chat_ids: list[int] = Field(default_factory=list)


class ObsCfg(BaseModel):
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""


class GtaCfg(BaseModel):
    base_url: str = "http://127.0.0.1:6721"


class EulerCfg(BaseModel):
    api_key: str = ""


class AirgpuCfg(BaseModel):
    stop_on_idle_minutes: int = 15


class RuntimeConfig(BaseModel):
    """Host-local settings + secrets (config.local.json, gitignored)."""

    telegram: TelegramCfg = Field(default_factory=TelegramCfg)
    obs_websocket: ObsCfg = Field(default_factory=ObsCfg)
    gta_adapter: GtaCfg = Field(default_factory=GtaCfg)
    eulerstream: EulerCfg = Field(default_factory=EulerCfg)
    airgpu: AirgpuCfg = Field(default_factory=AirgpuCfg)


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return RuntimeConfig.model_validate(data)
