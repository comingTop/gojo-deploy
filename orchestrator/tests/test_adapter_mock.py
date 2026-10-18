from __future__ import annotations

import pytest

from orchestrator.adapters.mock import MockAdapter
from orchestrator.models import ActionSpec, Reaction


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
