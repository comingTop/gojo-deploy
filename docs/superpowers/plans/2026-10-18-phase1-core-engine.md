# Phase 1 — Core Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the renderer-agnostic core of the TikTok gift-reaction system — a Python engine that maps normalized gift events to Gojo reactions with cooldowns, pacing, and a persisted gifter ranking, dispatching to a pluggable renderer adapter — and prove it end-to-end with a simulated gift stream and a mock adapter, with zero dependency on TikTok, GTA, or the cloud.

**Architecture:** An async pipeline `GiftSource → ReactionEngine → RendererAdapter`, plus a `StateStore` for TOP-3 / daily ranking. All boundaries are Protocols so real implementations (TikTokLive source, GTA adapter) drop in later without touching the engine. Phase 1 ships the `SimulatedGiftSource` and `MockAdapter` so the whole thing runs and is tested headless.

**Tech Stack:** Python 3.11+, pydantic v2 (config/models), pytest + pytest-asyncio (tests), stdlib `sqlite3` (state), stdlib `asyncio`. No network, no GUI.

**Spec:** `docs/superpowers/specs/2026-10-18-tiktok-gojo-gtav-live-design.md` (executors read both; this plan implements spec §3, §4.1 output contract, §4.2, §4.3 interface + MockAdapter, §4.7, §6).

## Global Constraints

- **Python 3.11+**; type hints everywhere; `from __future__ import annotations` in each module.
- **Renderer-agnostic:** the engine must NEVER import a concrete adapter/source — only the Protocols in `adapters/base.py` and `sources/base.py`. (Spec §3 "renderer-agnostic core".)
- **Config-driven:** gift→reaction mapping lives only in `config/reactions.json`; no gift names/ids hardcoded in engine logic. (Spec §6.)
- **Determinism for tests:** the engine takes an injected `now: Callable[[], float]` clock; no task asserts on wall-clock timing. (Spec §4.2 "clock injected".)
- **Timezone for daily reset:** `America/Sao_Paulo` default, configurable. (Spec §4.7.)
- **Licenses:** this repo's own code is the freelancer's deliverable; third-party deps must be commercial-OK (pydantic/pytest MIT/BSD). (Spec §2 voice/plugin licensing handled in later phases.)
- **Commits:** authored by the repo's configured git identity (`comingtop <comingtop01@gmail.com>`); **never add any AI/Claude/Co-Authored-By attribution line** to commit messages (user global rule). Commit after each task.
- **No secrets in git:** never commit real tokens, TikTok/AirGPU credentials, or stream keys; `config/config.example.json` holds placeholders only.

---

## File Structure (Phase 1)

```
orchestrator/
  pyproject.toml                  # package metadata, deps, pytest config
  orchestrator/
    __init__.py
    models.py                     # GiftEvent, Reaction, ActionSpec (runtime domain types)
    config.py                     # pydantic: GiftMatch, ReactionConfig, AppConfig + load_config()
    adapters/
      __init__.py
      base.py                     # RendererAdapter Protocol
      mock.py                     # MockAdapter (records dispatched reactions)
    sources/
      __init__.py
      base.py                     # GiftSource Protocol
      simulated.py                # SimulatedGiftSource (replays a scripted list)
    state.py                      # StateStore (sqlite3): record gifts, TOP-N, daily ranking + reset
    engine.py                     # ReactionEngine: match + cooldown + pacing + dispatch + state
    app.py                        # run_session(): wires source → engine
  config/
    reactions.json                # the default 7 Gojo reactions (spec §6 table)
    config.example.json           # AppConfig example with placeholders
  tests/
    __init__.py
    conftest.py                   # shared fixtures (fake clock, in-memory state)
    fixtures/gifts.json           # scripted gift events incl. a combo + a top-tier gift
    test_models.py
    test_config.py
    test_adapter_mock.py
    test_source_simulated.py
    test_state.py
    test_engine.py
    test_app_integration.py
```

**Responsibilities (one per file):** `models` = runtime types passed between stages; `config` = validated on-disk mapping; `adapters/base` + `sources/base` = the two swap points; `state` = persistence + ranking; `engine` = all decision/pacing logic (the brain); `app` = wiring only. Files that change together (an interface and its Phase-1 implementation) live in the same subpackage.

---

## Phase roadmap (context — later plans, not this document)

1. **Phase 1 — Core engine (this plan).** Headless, fully tested.
2. Phase 2 — Voice: Chatterbox pt-BR generation pipeline + `lines.pt-br.json` + `VoicePlayer`.
3. Phase 3 — Real gift source: `TikTokLiveGiftSource` (TikTokLive + EulerStream) with reconnect/backoff + recorded-fixture tests.
4. Phase 4 — GTA adapter + forked `smeysu` SHVDN plugin (verify HTTP command vocabulary).
5. Phase 5 — Overlays: `overlay_hub` (FastAPI+WebSocket) + OBS browser pages (gift menu, TOP-3, daily ranking).
6. Phase 6 — Telegram bot + obs-websocket stream control + AirGPU VM auto-stop (bill protection).
7. Phase 7 — Integration + **AirGPU/GTA machine runbook** + autostart.

---

## Task 1: Project scaffold

**Files:**
- Create: `orchestrator/pyproject.toml`
- Create: `orchestrator/orchestrator/__init__.py`
- Create: `orchestrator/tests/__init__.py`
- Create: `orchestrator/tests/conftest.py`
- Create: `orchestrator/tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing.
- Produces: an installable package `orchestrator` and a working `pytest` run (with asyncio mode enabled) that later tasks extend.

- [ ] **Step 1: Write the smoke test**

```python
# orchestrator/tests/test_smoke.py
from __future__ import annotations
import orchestrator

def test_package_imports():
    assert orchestrator.__version__ == "0.1.0"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator'` (package not installed yet).

- [ ] **Step 3: Create the package + pyproject**

```toml
# orchestrator/pyproject.toml
[project]
name = "orchestrator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.6,<3"]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["orchestrator*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```python
# orchestrator/orchestrator/__init__.py
from __future__ import annotations
__version__ = "0.1.0"
```

```python
# orchestrator/tests/__init__.py
```

```python
# orchestrator/tests/conftest.py
from __future__ import annotations
import pytest

class FakeClock:
    """Monotonic clock the tests advance by hand; injected into the engine."""
    def __init__(self, start: float = 1000.0) -> None:
        self._t = start
    def __call__(self) -> float:
        return self._t
    def advance(self, seconds: float) -> None:
        self._t += seconds

@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()
```

- [ ] **Step 4: Install the package and run the test**

Run: `cd orchestrator && pip install -e ".[dev]" && python -m pytest tests/test_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/pyproject.toml orchestrator/orchestrator/__init__.py orchestrator/tests/
git commit -m "feat(orchestrator): scaffold package + pytest asyncio setup"
```

---

## Task 2: Domain models

**Files:**
- Create: `orchestrator/orchestrator/models.py`
- Test: `orchestrator/tests/test_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `ActionSpec(command: str, params: dict[str, Any])` — frozen dataclass.
  - `GiftEvent(user_id: str, username: str, gift_id: int, gift_name: str, coins: int, count: int, timestamp: float, is_combo_end: bool = True)` — frozen dataclass; `total_coins` property returns `coins * count`.
  - `Reaction(id: str, label: str, action: ActionSpec, voice_clip: str | None, overlay_cue: str | None, cooldown_s: float)` — frozen dataclass.

- [ ] **Step 1: Write the failing test**

```python
# orchestrator/tests/test_models.py
from __future__ import annotations
from orchestrator.models import ActionSpec, GiftEvent, Reaction

def test_gift_event_total_coins_multiplies_count():
    ev = GiftEvent(user_id="u1", username="lucas", gift_id=5655,
                   gift_name="Rose", coins=1, count=5, timestamp=1000.0)
    assert ev.total_coins == 5
    assert ev.is_combo_end is True  # default

def test_models_are_frozen():
    a = ActionSpec(command="explode", params={"radius": 15})
    r = Reaction(id="roxo", label="Hollow Purple", action=a,
                 voice_clip="voice/output/roxo.wav", overlay_cue="menu.roxo",
                 cooldown_s=8.0)
    assert r.action.params["radius"] == 15
    try:
        r.cooldown_s = 1.0  # type: ignore[misc]
        assert False, "Reaction must be immutable"
    except Exception:
        pass
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator.models'`.

- [ ] **Step 3: Implement the models**

```python
# orchestrator/orchestrator/models.py
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/models.py orchestrator/tests/test_models.py
git commit -m "feat(orchestrator): add GiftEvent, Reaction, ActionSpec domain models"
```

---

## Task 3: Config schema, loader, and default reactions

**Files:**
- Create: `orchestrator/orchestrator/config.py`
- Create: `orchestrator/config/reactions.json`
- Create: `orchestrator/config/config.example.json`
- Test: `orchestrator/tests/test_config.py`

**Interfaces:**
- Consumes: `models.ActionSpec`, `models.Reaction`.
- Produces:
  - `GiftMatch(name: str | None, id: int | None, min_coins: int = 1)` — pydantic model; `matches(gift_name: str, gift_id: int, total_coins: int) -> bool`.
  - `ReactionConfig(id, label, gift: GiftMatch, action: ActionSpec-shaped, voice_clip: str|None, overlay_cue: str|None, cooldown_s: float = 5.0)`; `.to_reaction() -> Reaction`.
  - `AppConfig(tiktok_username: str, timezone: str = "America/Sao_Paulo", global_min_interval_s: float = 1.5, reactions: list[ReactionConfig])`.
  - `load_config(path: str | Path) -> AppConfig`.

- [ ] **Step 1: Write the failing test**

```python
# orchestrator/tests/test_config.py
from __future__ import annotations
from pathlib import Path
from orchestrator.config import load_config, GiftMatch

REPO_CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"

def test_default_config_has_seven_reactions():
    cfg = load_config(REPO_CONFIG)
    assert cfg.tiktok_username  # non-empty
    assert len(cfg.reactions) == 7
    ids = [r.id for r in cfg.reactions]
    assert len(set(ids)) == 7, "reaction ids must be unique"

def test_gift_match_by_name_is_case_insensitive():
    m = GiftMatch(name="Rose")
    assert m.matches("rose", 5655, 1) is True
    assert m.matches("Galaxy", 5655, 1) is False

def test_gift_match_by_coin_tier_when_no_name_or_id():
    m = GiftMatch(min_coins=100)
    assert m.matches("Anything", 999, 150) is True
    assert m.matches("Anything", 999, 50) is False

def test_reaction_config_converts_to_runtime_reaction():
    cfg = load_config(REPO_CONFIG)
    r = cfg.reactions[0].to_reaction()
    assert r.action.command  # has a command
    assert r.cooldown_s > 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator.config'`.

- [ ] **Step 3: Implement config models + loader**

```python
# orchestrator/orchestrator/config.py
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

class ReactionConfig(BaseModel):
    id: str
    label: str
    gift: GiftMatch
    action: ActionConfig
    voice_clip: str | None = None
    overlay_cue: str | None = None
    cooldown_s: float = 5.0

    def to_reaction(self) -> Reaction:
        return Reaction(
            id=self.id, label=self.label,
            action=ActionSpec(command=self.action.command, params=dict(self.action.params)),
            voice_clip=self.voice_clip, overlay_cue=self.overlay_cue,
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
```

- [ ] **Step 4: Create the default reactions.json (spec §6)**

```json
// orchestrator/config/reactions.json
{
  "tiktok_username": "jailton.mma",
  "timezone": "America/Sao_Paulo",
  "global_min_interval_s": 1.5,
  "reactions": [
    {"id": "flash", "label": "Flash / Teleporte", "gift": {"name": "Rose", "min_coins": 1},
     "action": {"command": "teleport_fly", "params": {}}, "voice_clip": "voice/output/flash.wav",
     "overlay_cue": "menu.flash", "cooldown_s": 6},
    {"id": "azul", "label": "Azul - atracao", "gift": {"name": "GG", "min_coins": 1},
     "action": {"command": "pull_npcs", "params": {"radius": 12}}, "voice_clip": "voice/output/azul.wav",
     "overlay_cue": "menu.azul", "cooldown_s": 6},
    {"id": "vermelho", "label": "Vermelho - repulsao", "gift": {"name": "Perfume", "min_coins": 20},
     "action": {"command": "push_npcs", "params": {"force": 150}}, "voice_clip": "voice/output/vermelho.wav",
     "overlay_cue": "menu.vermelho", "cooldown_s": 8},
    {"id": "roxo", "label": "Roxo - Hollow Purple", "gift": {"name": "Galaxy", "min_coins": 100},
     "action": {"command": "explode", "params": {"radius": 15}}, "voice_clip": "voice/output/roxo.wav",
     "overlay_cue": "menu.roxo", "cooldown_s": 10},
    {"id": "infinito", "label": "Infinito / Limitless", "gift": {"name": "Diamond", "min_coins": 300},
     "action": {"command": "invincible_slowmo", "params": {"duration_s": 10, "scale": 0.4}},
     "voice_clip": "voice/output/infinito.wav", "overlay_cue": "menu.infinito", "cooldown_s": 15},
    {"id": "seis_olhos", "label": "Seis Olhos", "gift": {"name": "Fireworks", "min_coins": 500},
     "action": {"command": "bullet_time", "params": {"duration_s": 8, "scale": 0.3}},
     "voice_clip": "voice/output/seis_olhos.wav", "overlay_cue": "menu.seis_olhos", "cooldown_s": 15},
    {"id": "dominio", "label": "Expansao de Dominio", "gift": {"name": "Universe", "min_coins": 1000},
     "action": {"command": "domain_expansion", "params": {"weather": "THUNDER", "attackers": 6}},
     "voice_clip": "voice/output/dominio.wav", "overlay_cue": "menu.dominio", "cooldown_s": 30}
  ]
}
```

> NOTE (spec §6, §11 P2): gift names/ids above are **placeholders chosen to be reassigned with the client**; the matcher supports name, id, or coin-tier so the final mapping is a config edit, not a code change. Gift `id`s will be filled from real TikTok data in Phase 3.

```json
// orchestrator/config/config.example.json
{
  "telegram": {"bot_token": "PUT-TELEGRAM-BOT-TOKEN-HERE", "allowed_chat_ids": [111111111]},
  "obs_websocket": {"host": "127.0.0.1", "port": 4455, "password": "PUT-OBS-WS-PASSWORD-HERE"},
  "gta_adapter": {"base_url": "http://127.0.0.1:6721"},
  "eulerstream": {"api_key": ""},
  "airgpu": {"stop_on_idle_minutes": 15}
}
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_config.py -v`
Expected: PASS (7 reactions, matcher cases green).

- [ ] **Step 6: Commit**

```bash
git add orchestrator/orchestrator/config.py orchestrator/config/ orchestrator/tests/test_config.py
git commit -m "feat(orchestrator): config schema, loader, and default 7-reaction mapping"
```

---

## Task 4: Renderer adapter Protocol + MockAdapter

**Files:**
- Create: `orchestrator/orchestrator/adapters/__init__.py`
- Create: `orchestrator/orchestrator/adapters/base.py`
- Create: `orchestrator/orchestrator/adapters/mock.py`
- Test: `orchestrator/tests/test_adapter_mock.py`

**Interfaces:**
- Consumes: `models.Reaction`.
- Produces:
  - `RendererAdapter` Protocol: `async def play(self, reaction: Reaction) -> None`; `async def health(self) -> bool`.
  - `MockAdapter`: attribute `played: list[Reaction]`; optional `fail: bool` to simulate a dead renderer; `play` appends (or raises `RuntimeError` if `fail`); `health` returns `not self.fail`.

- [ ] **Step 1: Write the failing test**

```python
# orchestrator/tests/test_adapter_mock.py
from __future__ import annotations
import pytest
from orchestrator.models import ActionSpec, Reaction
from orchestrator.adapters.mock import MockAdapter

def _reaction() -> Reaction:
    return Reaction(id="roxo", label="Hollow Purple",
                    action=ActionSpec("explode", {"radius": 15}),
                    voice_clip=None, overlay_cue=None, cooldown_s=8.0)

async def test_mock_records_played_reactions():
    a = MockAdapter()
    assert await a.health() is True
    await a.play(_reaction())
    assert [r.id for r in a.played] == ["roxo"]

async def test_mock_can_simulate_failure():
    a = MockAdapter(fail=True)
    assert await a.health() is False
    with pytest.raises(RuntimeError):
        await a.play(_reaction())
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_adapter_mock.py -v`
Expected: FAIL — module `orchestrator.adapters.mock` missing.

- [ ] **Step 3: Implement the Protocol + MockAdapter**

```python
# orchestrator/orchestrator/adapters/__init__.py
```

```python
# orchestrator/orchestrator/adapters/base.py
from __future__ import annotations
from typing import Protocol, runtime_checkable
from ..models import Reaction

@runtime_checkable
class RendererAdapter(Protocol):
    async def play(self, reaction: Reaction) -> None: ...
    async def health(self) -> bool: ...
```

```python
# orchestrator/orchestrator/adapters/mock.py
from __future__ import annotations
from ..models import Reaction

class MockAdapter:
    """Records dispatched reactions; used for headless engine tests."""
    def __init__(self, fail: bool = False) -> None:
        self.played: list[Reaction] = []
        self.fail = fail

    async def play(self, reaction: Reaction) -> None:
        if self.fail:
            raise RuntimeError("renderer down")
        self.played.append(reaction)

    async def health(self) -> bool:
        return not self.fail
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_adapter_mock.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/adapters/ orchestrator/tests/test_adapter_mock.py
git commit -m "feat(orchestrator): RendererAdapter protocol + MockAdapter"
```

---

## Task 5: Gift source Protocol + SimulatedGiftSource

**Files:**
- Create: `orchestrator/orchestrator/sources/__init__.py`
- Create: `orchestrator/orchestrator/sources/base.py`
- Create: `orchestrator/orchestrator/sources/simulated.py`
- Create: `orchestrator/tests/fixtures/gifts.json`
- Test: `orchestrator/tests/test_source_simulated.py`

**Interfaces:**
- Consumes: `models.GiftEvent`.
- Produces:
  - `GiftSource` Protocol: `def stream(self) -> AsyncIterator[GiftEvent]`.
  - `SimulatedGiftSource(events: list[GiftEvent], delay_s: float = 0.0)`; `stream()` yields each event (sleeping `delay_s` between). Classmethod `from_json(path) -> SimulatedGiftSource` builds events from a fixture list of dicts.

- [ ] **Step 1: Write the failing test**

```python
# orchestrator/tests/test_source_simulated.py
from __future__ import annotations
from pathlib import Path
from orchestrator.models import GiftEvent
from orchestrator.sources.simulated import SimulatedGiftSource

FIX = Path(__file__).resolve().parent / "fixtures" / "gifts.json"

async def _drain(src) -> list[GiftEvent]:
    return [ev async for ev in src.stream()]

async def test_simulated_source_yields_in_order():
    events = [
        GiftEvent("u1", "lucas", 5655, "Rose", 1, 1, 1.0),
        GiftEvent("u2", "bia", 9999, "Universe", 1000, 1, 2.0),
    ]
    out = await _drain(SimulatedGiftSource(events))
    assert [e.gift_name for e in out] == ["Rose", "Universe"]

async def test_simulated_source_from_json_fixture():
    out = await _drain(SimulatedGiftSource.from_json(FIX))
    assert len(out) >= 3
    assert any(e.gift_name == "Universe" for e in out)
    # the fixture includes a combo: intermediate ticks marked is_combo_end=False
    assert any(e.is_combo_end is False for e in out)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_source_simulated.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement the Protocol, source, and fixture**

```python
# orchestrator/orchestrator/sources/__init__.py
```

```python
# orchestrator/orchestrator/sources/base.py
from __future__ import annotations
from typing import AsyncIterator, Protocol
from ..models import GiftEvent

class GiftSource(Protocol):
    def stream(self) -> AsyncIterator[GiftEvent]: ...
```

```python
# orchestrator/orchestrator/sources/simulated.py
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import AsyncIterator
from ..models import GiftEvent

class SimulatedGiftSource:
    """Replays a scripted list of GiftEvents. Phase-1 stand-in for TikTok."""
    def __init__(self, events: list[GiftEvent], delay_s: float = 0.0) -> None:
        self._events = events
        self._delay_s = delay_s

    async def stream(self) -> AsyncIterator[GiftEvent]:
        for ev in self._events:
            if self._delay_s:
                await asyncio.sleep(self._delay_s)
            yield ev

    @classmethod
    def from_json(cls, path: str | Path, delay_s: float = 0.0) -> "SimulatedGiftSource":
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        events = [GiftEvent(**row) for row in rows]
        return cls(events, delay_s=delay_s)
```

```json
// orchestrator/tests/fixtures/gifts.json
[
  {"user_id": "u1", "username": "lucas", "gift_id": 5655, "gift_name": "Rose", "coins": 1, "count": 1, "timestamp": 1.0, "is_combo_end": true},
  {"user_id": "u2", "username": "enrihzoka", "gift_id": 5655, "gift_name": "Rose", "coins": 1, "count": 3, "timestamp": 2.0, "is_combo_end": false},
  {"user_id": "u2", "username": "enrihzoka", "gift_id": 5655, "gift_name": "Rose", "coins": 1, "count": 5, "timestamp": 2.4, "is_combo_end": true},
  {"user_id": "u3", "username": "bia_mant", "gift_id": 8888, "gift_name": "Galaxy", "coins": 100, "count": 1, "timestamp": 5.0, "is_combo_end": true},
  {"user_id": "u4", "username": "david", "gift_id": 9999, "gift_name": "Universe", "coins": 1000, "count": 1, "timestamp": 9.0, "is_combo_end": true}
]
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_source_simulated.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/sources/ orchestrator/tests/fixtures/gifts.json orchestrator/tests/test_source_simulated.py
git commit -m "feat(orchestrator): GiftSource protocol + SimulatedGiftSource + gift fixture"
```

---

## Task 6: StateStore (SQLite) — gifters, TOP-N, daily ranking

**Files:**
- Create: `orchestrator/orchestrator/state.py`
- Test: `orchestrator/tests/test_state.py`

**Interfaces:**
- Consumes: nothing (stores primitives).
- Produces:
  - `StateStore(db_path: str = ":memory:", tz: str = "America/Sao_Paulo")`.
  - `record_gift(user_id: str, username: str, total_coins: int, at: float) -> None` — `at` is a POSIX timestamp (seconds).
  - `top_gifters(n: int, at: float) -> list[tuple[str, int]]` — `(username, coins)` for the local day containing `at`, descending, limited to `n`.
  - `day_key(at: float) -> str` — `YYYY-MM-DD` in `tz`; used for the daily reset (a new day key => a fresh ranking, no deletion needed).

- [ ] **Step 1: Write the failing test**

```python
# orchestrator/tests/test_state.py
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from orchestrator.state import StateStore

# 2026-10-18 12:00 and 23:30 UTC are the SAME day in UTC but DIFFERENT local
# days in America/Sao_Paulo (UTC-3) only across midnight; pick clear cases.
NOON_UTC = datetime(2026, 10, 18, 15, 0, tzinfo=timezone.utc).timestamp()      # 12:00 BRT
NEXT_DAY = datetime(2026, 10, 19, 15, 0, tzinfo=timezone.utc).timestamp()      # next day 12:00 BRT

def test_top_gifters_sums_and_ranks_within_day():
    s = StateStore()
    s.record_gift("u1", "lucas", 50, NOON_UTC)
    s.record_gift("u2", "bia", 100, NOON_UTC)
    s.record_gift("u1", "lucas", 70, NOON_UTC)   # lucas now 120 > bia 100
    assert s.top_gifters(3, NOON_UTC) == [("lucas", 120), ("bia", 100)]

def test_daily_ranking_resets_on_new_day():
    s = StateStore()
    s.record_gift("u1", "lucas", 500, NOON_UTC)
    assert s.top_gifters(3, NEXT_DAY) == []          # new day => empty ranking
    s.record_gift("u2", "bia", 10, NEXT_DAY)
    assert s.top_gifters(3, NEXT_DAY) == [("bia", 10)]

def test_day_key_is_local_date():
    s = StateStore()
    assert s.day_key(NOON_UTC) == "2026-10-18"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_state.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement StateStore**

```python
# orchestrator/orchestrator/state.py
from __future__ import annotations
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

class StateStore:
    def __init__(self, db_path: str = ":memory:", tz: str = "America/Sao_Paulo") -> None:
        self._tz = ZoneInfo(tz)
        self._db = sqlite3.connect(db_path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS gifts ("
            " day TEXT NOT NULL, user_id TEXT NOT NULL, username TEXT NOT NULL,"
            " coins INTEGER NOT NULL, at REAL NOT NULL)"
        )
        self._db.commit()

    def day_key(self, at: float) -> str:
        return datetime.fromtimestamp(at, self._tz).strftime("%Y-%m-%d")

    def record_gift(self, user_id: str, username: str, total_coins: int, at: float) -> None:
        self._db.execute(
            "INSERT INTO gifts(day, user_id, username, coins, at) VALUES(?,?,?,?,?)",
            (self.day_key(at), user_id, username, total_coins, at),
        )
        self._db.commit()

    def top_gifters(self, n: int, at: float) -> list[tuple[str, int]]:
        cur = self._db.execute(
            "SELECT username, SUM(coins) AS total FROM gifts"
            " WHERE day = ? GROUP BY user_id ORDER BY total DESC, MAX(at) ASC LIMIT ?",
            (self.day_key(at), n),
        )
        return [(row[0], int(row[1])) for row in cur.fetchall()]
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_state.py -v`
Expected: PASS (ranking, daily reset, day_key all green).

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/state.py orchestrator/tests/test_state.py
git commit -m "feat(orchestrator): SQLite StateStore with daily-reset TOP-N ranking"
```

---

## Task 7: ReactionEngine — match, pace, dispatch, record

**Files:**
- Create: `orchestrator/orchestrator/engine.py`
- Test: `orchestrator/tests/test_engine.py`

**Interfaces:**
- Consumes: `config.AppConfig`, `adapters/base.RendererAdapter`, `state.StateStore`, `models.GiftEvent/Reaction`.
- Produces:
  - `ReactionEngine(config: AppConfig, adapter: RendererAdapter, state: StateStore, now: Callable[[], float] = time.monotonic)`.
  - `match(event: GiftEvent) -> ReactionConfig | None` — first config whose `gift.matches(...)` is True (order = config order).
  - `async handle_gift(event: GiftEvent) -> Reaction | None` — rules, in order:
    1. If `event.is_combo_end` is False → return None (don't fire on intermediate combo ticks).
    2. Always record the gift to state (even if no reaction / on cooldown), using `event.timestamp`.
    3. `match(event)`; if None → return None.
    4. Per-reaction cooldown: if `now() - last_fired[id] < cooldown_s` → return None.
    5. Global pace: if `now() - last_any_fired < global_min_interval_s` → return None.
    6. Else `await adapter.play(reaction)`, set `last_fired[id]` and `last_any_fired` to `now()`, return the Reaction.

- [ ] **Step 1: Write the failing tests**

```python
# orchestrator/tests/test_engine.py
from __future__ import annotations
from pathlib import Path
from orchestrator.config import load_config
from orchestrator.models import GiftEvent
from orchestrator.adapters.mock import MockAdapter
from orchestrator.state import StateStore
from orchestrator.engine import ReactionEngine

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"

def _engine(clock):
    cfg = load_config(CONFIG)
    adapter = MockAdapter()
    engine = ReactionEngine(cfg, adapter, StateStore(), now=clock)
    return cfg, adapter, engine

def _rose(ts=1.0, count=1, combo_end=True):
    return GiftEvent("u1", "lucas", 5655, "Rose", 1, count, ts, is_combo_end=combo_end)

async def test_matching_rose_fires_flash(clock):
    _, adapter, engine = _engine(clock)
    r = await engine.handle_gift(_rose())
    assert r is not None and r.id == "flash"
    assert [x.id for x in adapter.played] == ["flash"]

async def test_intermediate_combo_tick_does_not_fire(clock):
    _, adapter, engine = _engine(clock)
    assert await engine.handle_gift(_rose(combo_end=False)) is None
    assert adapter.played == []

async def test_per_reaction_cooldown_blocks_repeat(clock):
    _, adapter, engine = _engine(clock)
    await engine.handle_gift(_rose())            # fires flash (cooldown 6s)
    clock.advance(1.0)
    assert await engine.handle_gift(_rose()) is None   # still cooling down
    clock.advance(6.0)
    assert (await engine.handle_gift(_rose())).id == "flash"  # cooldown elapsed

async def test_global_min_interval_blocks_cross_reaction_spam(clock):
    cfg, adapter, engine = _engine(clock)
    universe = GiftEvent("u4", "david", 9999, "Universe", 1000, 1, 9.0)
    galaxy = GiftEvent("u3", "bia", 8888, "Galaxy", 100, 1, 9.1)
    assert (await engine.handle_gift(universe)).id == "dominio"
    # within global_min_interval_s (1.5s) a different reaction is paced out
    assert await engine.handle_gift(galaxy) is None

async def test_gift_is_recorded_even_when_no_reaction(clock):
    _, _, engine = _engine(clock)
    # coins below every tier and no matching name => no reaction, but recorded
    unknown = GiftEvent("u9", "ghost", 1, "UnknownGift", 0, 1, 50.0)
    assert await engine.handle_gift(unknown) is None
    assert engine.state.top_gifters(3, 50.0) == [("ghost", 0)]
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_engine.py -v`
Expected: FAIL — module `orchestrator.engine` missing.

- [ ] **Step 3: Implement the engine**

```python
# orchestrator/orchestrator/engine.py
from __future__ import annotations
import time
from typing import Callable
from .adapters.base import RendererAdapter
from .config import AppConfig, ReactionConfig
from .models import GiftEvent, Reaction
from .state import StateStore

class ReactionEngine:
    def __init__(self, config: AppConfig, adapter: RendererAdapter,
                 state: StateStore, now: Callable[[], float] = time.monotonic) -> None:
        self.config = config
        self.adapter = adapter
        self.state = state
        self._now = now
        self._last_fired: dict[str, float] = {}
        self._last_any_fired: float = float("-inf")

    def match(self, event: GiftEvent) -> ReactionConfig | None:
        for rc in self.config.reactions:
            if rc.gift.matches(event.gift_name, event.gift_id, event.total_coins):
                return rc
        return None

    async def handle_gift(self, event: GiftEvent) -> Reaction | None:
        if not event.is_combo_end:
            return None
        self.state.record_gift(event.user_id, event.username, event.total_coins, event.timestamp)
        rc = self.match(event)
        if rc is None:
            return None
        t = self._now()
        if t - self._last_fired.get(rc.id, float("-inf")) < rc.cooldown_s:
            return None
        if t - self._last_any_fired < self.config.global_min_interval_s:
            return None
        reaction = rc.to_reaction()
        await self.adapter.play(reaction)
        self._last_fired[rc.id] = t
        self._last_any_fired = t
        return reaction
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd orchestrator && python -m pytest tests/test_engine.py -v`
Expected: PASS (all five behaviors green).

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/engine.py orchestrator/tests/test_engine.py
git commit -m "feat(orchestrator): ReactionEngine with matching, cooldowns, pacing, state"
```

---

## Task 8: Wiring + end-to-end simulated session

**Files:**
- Create: `orchestrator/orchestrator/app.py`
- Test: `orchestrator/tests/test_app_integration.py`

**Interfaces:**
- Consumes: `sources/base.GiftSource`, `engine.ReactionEngine`.
- Produces:
  - `async run_session(source: GiftSource, engine: ReactionEngine) -> list[Reaction]` — iterates `source.stream()`, calls `engine.handle_gift`, returns the list of reactions that actually fired (skips/None filtered out). This is the real run loop (Phase 3 swaps the source for TikTok, Phase 4 swaps the adapter for GTA — `run_session` itself does not change).

- [ ] **Step 1: Write the failing integration test**

```python
# orchestrator/tests/test_app_integration.py
from __future__ import annotations
from pathlib import Path
from orchestrator.config import load_config
from orchestrator.adapters.mock import MockAdapter
from orchestrator.state import StateStore
from orchestrator.engine import ReactionEngine
from orchestrator.sources.simulated import SimulatedGiftSource
from orchestrator.app import run_session

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"
FIX = Path(__file__).resolve().parent / "fixtures" / "gifts.json"

async def test_full_simulated_session(clock):
    cfg = load_config(CONFIG)
    adapter = MockAdapter()
    engine = ReactionEngine(cfg, adapter, StateStore(), now=clock)

    # advance the injected clock between events so cooldown/pace don't block the
    # distinct reactions in the fixture; simulated source has no real delay.
    class Ticking(SimulatedGiftSource):
        async def stream(self):
            async for ev in super().stream():
                clock.advance(60.0)
                yield ev

    fired = await run_session(Ticking.from_json(FIX), engine)
    # fixture: Rose(combo tick, ignored) -> Rose(combo end) -> Galaxy -> Universe
    assert [r.id for r in fired] == ["flash", "flash", "roxo", "dominio"]
    # david(Universe,1000) tops the day
    assert engine.state.top_gifters(1, 9.0)[0][0] == "david"
```

> Note: the first `flash` is the `lucas` Rose(count 1, combo_end); the `enrihzoka` Rose appears twice (combo tick `is_combo_end=false` is ignored, combo end fires the second `flash`). This verifies combo collapsing end-to-end.

- [ ] **Step 2: Run to verify it fails**

Run: `cd orchestrator && python -m pytest tests/test_app_integration.py -v`
Expected: FAIL — `orchestrator.app` missing.

- [ ] **Step 3: Implement run_session**

```python
# orchestrator/orchestrator/app.py
from __future__ import annotations
from .engine import ReactionEngine
from .models import Reaction
from .sources.base import GiftSource

async def run_session(source: GiftSource, engine: ReactionEngine) -> list[Reaction]:
    fired: list[Reaction] = []
    async for event in source.stream():
        reaction = await engine.handle_gift(event)
        if reaction is not None:
            fired.append(reaction)
    return fired
```

- [ ] **Step 4: Run the full suite**

Run: `cd orchestrator && python -m pytest -v`
Expected: PASS — every test from Tasks 1–8 green.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator/app.py orchestrator/tests/test_app_integration.py
git commit -m "feat(orchestrator): run_session wiring + end-to-end simulated session test"
```

---

## Self-Review

**1. Spec coverage (Phase 1 scope):**
- Spec §3 renderer-agnostic pipeline → Tasks 4,5,7,8 (Protocols + engine never imports concretes). ✅
- Spec §4.1 normalized gift output contract + combo end → `GiftEvent` (Task 2) + combo-tick rule (Task 7). ✅
- Spec §4.2 reaction engine (map, cooldown, global interval, injected clock) → Task 7. ✅
- Spec §4.3 adapter interface + MockAdapter → Task 4. ✅
- Spec §4.7 state/TOP-N/daily reset → Task 6. ✅
- Spec §6 config-driven mapping + 7 reactions → Task 3. ✅
- Deferred by design (later phases, noted in roadmap): voice playback (§4.4), TikTok source (§4.1 impl / §3), GTA adapter (§4.3 impl), overlays (§4.5), Telegram (§4.6), queue for simultaneous big gifts (§4.2) — Phase 1 paces via cooldown+interval; a true async queue lands with the real async source in Phase 3.

**2. Placeholder scan:** No "TBD/TODO/handle edge cases" — every step has real test + impl code. The gift names/ids in `reactions.json` are explicitly flagged as client-finalized config (spec §11 P2), not code placeholders. ✅

**3. Type consistency:** `GiftEvent`/`Reaction`/`ActionSpec` field names identical across Tasks 2–8; `RendererAdapter.play/health` signatures match MockAdapter (Task 4) and engine call (Task 7); `StateStore.record_gift/top_gifters/day_key` signatures match engine + integration usage (Tasks 6–8); `ReactionConfig.to_reaction()` and `GiftMatch.matches()` used consistently (Tasks 3,7). ✅

---

## Execution Handoff

Phase 1 is independently runnable and testable with **no external services**. After it is green, Phase 2 (voice) and Phase 4 (GTA adapter/plugin) can proceed in parallel, and Phase 3 (TikTok source) swaps in behind the same `GiftSource` Protocol with `run_session` unchanged.
