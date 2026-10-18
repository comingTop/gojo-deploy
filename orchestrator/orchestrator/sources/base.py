from __future__ import annotations

from typing import AsyncIterator, Protocol

from ..models import GiftEvent


class GiftSource(Protocol):
    def stream(self) -> AsyncIterator[GiftEvent]: ...
