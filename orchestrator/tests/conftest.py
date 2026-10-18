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
