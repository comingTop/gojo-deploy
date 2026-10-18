from __future__ import annotations

import asyncio
import urllib.error
import urllib.request

from ..models import Reaction


class GtaAdapter:
    """Renderer adapter that drives the in-game GTA plugin (forked smeysu
    GTA5-TikTok-Integration) over its local HTTP command server.

    The plugin listens on http://127.0.0.1:6721 and takes commands shaped
    ``/<command>:<param1>,<param2>``. Each reaction's ``action.command`` maps to a
    plugin endpoint (optionally renamed via ``command_map``) and its ``action.params``
    values become the colon-separated argument list. The exact endpoint names are
    finalized against the forked plugin; ``command_map`` lets us remap without code
    changes.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:6721",
        timeout: float = 3.0,
        command_map: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.command_map = command_map or {}
        self.last_error: str | None = None

    def build_path(self, reaction: Reaction) -> str:
        endpoint = self.command_map.get(reaction.action.command, reaction.action.command)
        param_str = ",".join(str(v) for v in reaction.action.params.values())
        return f"/{endpoint}:{param_str}" if param_str else f"/{endpoint}"

    def _get(self, path: str) -> int:
        try:
            with urllib.request.urlopen(self.base_url + path, timeout=self.timeout) as resp:
                return resp.status
        except urllib.error.URLError as exc:
            self.last_error = str(exc)
            raise

    async def play(self, reaction: Reaction) -> None:
        await asyncio.to_thread(self._get, self.build_path(reaction))

    async def health(self) -> bool:
        try:
            await asyncio.to_thread(self._get, "/health")
            return True
        except Exception:
            return False
