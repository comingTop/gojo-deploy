from __future__ import annotations

from pathlib import Path

from orchestrator.config import GiftMatch, load_config

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
