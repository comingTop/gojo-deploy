from __future__ import annotations

from pathlib import Path

from orchestrator.runtime_config import RuntimeConfig, load_runtime_config

EXAMPLE = Path(__file__).resolve().parents[1] / "config" / "config.example.json"


def test_loads_example_runtime_config():
    rt = load_runtime_config(EXAMPLE)
    assert rt.obs_websocket.port == 4455
    assert rt.gta_adapter.base_url == "http://127.0.0.1:6721"
    assert rt.airgpu.stop_on_idle_minutes == 15
    assert rt.telegram.allowed_chat_ids == [111111111]


def test_runtime_config_has_safe_defaults_when_empty():
    rt = RuntimeConfig()
    assert rt.telegram.bot_token == ""
    assert rt.obs_websocket.host == "127.0.0.1"
    assert rt.eulerstream.api_key == ""
