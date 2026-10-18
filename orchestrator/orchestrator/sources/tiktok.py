from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from ..models import GiftEvent
from .normalize import normalize_gift


class TikTokLiveGiftSource:
    """Live gift source backed by the TikTokLive library (+ EulerStream signing).

    Reads a public live — no login or creator permission needed; the creator just
    has to be live. Only combo-end (and single) gifts are emitted; mid-combo ticks
    are dropped so a reaction fires once per gift/streak. Reconnects with a fixed
    backoff on disconnect so one drop never ends the session.

    TikTokLive is imported lazily (install the ``live`` extra) so the rest of the
    package — and the ``normalize_gift`` tests — need no network dependency.
    """

    def __init__(
        self,
        username: str,
        sign_api_key: str | None = None,
        reconnect_delay_s: float = 5.0,
    ) -> None:
        self.username = username if str(username).startswith("@") else f"@{username}"
        self.sign_api_key = sign_api_key
        self.reconnect_delay_s = reconnect_delay_s

    def _make_client(self):
        from TikTokLive import TikTokLiveClient

        if self.sign_api_key:
            os.environ.setdefault("SIGN_API_KEY", self.sign_api_key)
        client = TikTokLiveClient(unique_id=self.username)
        if self.sign_api_key:
            signer = getattr(getattr(client, "web", None), "signer", None)
            if signer is not None and hasattr(signer, "sign_api_key"):
                try:
                    signer.sign_api_key = self.sign_api_key
                except Exception:
                    pass
        return client

    async def stream(self) -> AsyncIterator[GiftEvent]:
        from TikTokLive.events import GiftEvent as TikTokGiftEvent

        queue: asyncio.Queue[GiftEvent] = asyncio.Queue()

        while True:
            client = self._make_client()

            @client.on(TikTokGiftEvent)
            async def _on_gift(event, _queue=queue) -> None:
                gift = normalize_gift(event)
                if gift.is_combo_end:  # drop mid-combo ticks
                    await _queue.put(gift)

            run_task = asyncio.create_task(client.connect())
            try:
                while not run_task.done():
                    get_task = asyncio.create_task(queue.get())
                    done, _ = await asyncio.wait(
                        {get_task, run_task}, return_when=asyncio.FIRST_COMPLETED
                    )
                    if get_task in done:
                        yield get_task.result()
                    else:
                        get_task.cancel()
                run_task.result()  # surface a connect() exception, if any
            except Exception:
                pass  # fall through to backoff + reconnect
            finally:
                if not run_task.done():
                    run_task.cancel()
                try:
                    await client.disconnect()
                except Exception:
                    pass
            await asyncio.sleep(self.reconnect_delay_s)
