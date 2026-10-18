from __future__ import annotations

import argparse
import asyncio
import random
import time
from pathlib import Path

from .adapters.mock import MockAdapter
from .config import load_config
from .coordinator import run_live_session
from .engine import ReactionEngine
from .models import GiftEvent
from .overlay.hub import OverlayHub
from .runtime_config import load_runtime_config
from .state import StateStore


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


async def _run_sim(overlay_port: int) -> None:
    """Full app with a simulated gift stream + mock renderer. No TikTok/GTA/cloud.
    Open overlays/top3.html?ws=ws://127.0.0.1:<port> to watch it live.
    """
    app_cfg = load_config(_repo_root() / "config" / "reactions.json")
    engine = ReactionEngine(app_cfg, MockAdapter(), StateStore(tz=app_cfg.timezone))
    overlay = OverlayHub()
    await overlay.serve("127.0.0.1", overlay_port)
    print(f"[sim] overlay hub on ws://127.0.0.1:{overlay_port}")
    print(f"[sim] open:  overlays/top3.html?ws=ws://127.0.0.1:{overlay_port}")
    print(f"[sim]        overlays/menu.html?ws=ws://127.0.0.1:{overlay_port}")

    samples = [("Rose", 5655, 1), ("GG", 6001, 1), ("Perfume", 7001, 20),
               ("Galaxy", 8888, 100), ("Diamond", 9001, 300),
               ("Fireworks", 9500, 500), ("Universe", 9999, 1000)]
    users = [("u1", "lucas"), ("u2", "enrihzoka"), ("u3", "bia_mant"),
             ("u4", "david"), ("u5", "igor")]

    class InfiniteSim:
        async def stream(self):
            while True:
                name, gid, coins = random.choice(samples)
                uid, nick = random.choice(users)
                yield GiftEvent(uid, nick, gid, name, coins, 1, time.time())
                await asyncio.sleep(1.5)

    await run_live_session(InfiniteSim(), engine, overlay)


async def _run_live(config_dir: Path) -> None:
    """Production wiring: TikTok source -> engine -> GTA adapter + overlays, with
    the Telegram bot and idle watchdog on one event loop. Validated on the host.
    """
    from .adapters.gta import GtaAdapter
    from .control.controller import LiveController
    from .control.obs import ObsController
    from .control.telegram_bot import TelegramControl
    from .control.watchdog import IdleWatchdog
    from .sources.tiktok import TikTokLiveGiftSource
    from .voice.player import VoicePlayer

    app_cfg = load_config(config_dir / "reactions.json")
    rt = load_runtime_config(config_dir / "config.local.json")

    state = StateStore(str(_repo_root() / "gojo.sqlite"), tz=app_cfg.timezone)
    engine = ReactionEngine(app_cfg, GtaAdapter(base_url=rt.gta_adapter.base_url), state)
    overlay = OverlayHub()
    await overlay.serve()
    obs = ObsController(rt.obs_websocket.host, rt.obs_websocket.port, rt.obs_websocket.password)

    async def _vm_shutdown() -> None:
        await asyncio.create_subprocess_shell("shutdown /s /t 0")  # Windows bill protection

    controller = LiveController(engine, obs, vm_stop=_vm_shutdown)
    watchdog = IdleWatchdog(rt.airgpu.stop_on_idle_minutes * 60,
                            on_idle=lambda: controller.stop_live(stop_vm=True))
    source = TikTokLiveGiftSource(app_cfg.tiktok_username,
                                  sign_api_key=rt.eulerstream.api_key or None)
    voice = VoicePlayer(root=str(_repo_root()), device=rt.voice.device)

    tg = TelegramControl(rt.telegram.bot_token, controller, rt.telegram.allowed_chat_ids).build_app()
    await tg.initialize()
    await tg.start()
    await tg.updater.start_polling()

    async def _watchdog_loop() -> None:
        while True:
            await watchdog.check()
            await asyncio.sleep(30)

    try:
        await asyncio.gather(
            run_live_session(source, engine, overlay, voice=voice, watchdog=watchdog),
            _watchdog_loop(),
        )
    finally:
        await tg.updater.stop()
        await tg.stop()
        await tg.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(prog="orchestrator")
    parser.add_argument("--sim", action="store_true",
                        help="simulated gift stream + mock renderer (no TikTok/GTA/cloud)")
    parser.add_argument("--overlay-port", type=int, default=8765)
    parser.add_argument("--config-dir", default=str(_repo_root() / "config"))
    args = parser.parse_args()
    if args.sim:
        asyncio.run(_run_sim(args.overlay_port))
    else:
        asyncio.run(_run_live(Path(args.config_dir)))


if __name__ == "__main__":
    main()
