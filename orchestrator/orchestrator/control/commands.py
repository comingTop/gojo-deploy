from __future__ import annotations

from .controller import LiveController

HELP = "Comandos: /ligar · /desligar · /status · /ranking · /testar <id>"


def _format_top3(top3: list[tuple[str, int]]) -> str:
    if not top3:
        return "—"
    return "\n".join(f"{i}. {u}: {c}" for i, (u, c) in enumerate(top3, 1))


async def handle_command(
    text: str,
    chat_id: int,
    controller: LiveController,
    allowed_chat_ids: set[int] | None = None,
) -> str | None:
    """Map a Telegram text command to a controller action and a reply.

    Returns ``None`` (silent) for unauthorized chats or non-commands, so the bot
    only ever answers the owner. Pure dispatch — unit-testable without Telegram.
    """
    if allowed_chat_ids and chat_id not in allowed_chat_ids:
        return None

    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        return None
    cmd = parts[0].lower()

    if cmd == "/ligar":
        return await controller.start_live()
    if cmd == "/desligar":
        return await controller.stop_live(stop_vm=True)
    if cmd == "/status":
        s = controller.status()
        live = "🔴 ON" if s["live"] else "⚪ OFF"
        obs = "transmitindo" if s["obs_streaming"] else "parado"
        return f"Live: {live}\nOBS: {obs}\nTOP 3:\n{_format_top3(s['top3'])}"
    if cmd == "/ranking":
        return "TOP 3 do dia:\n" + _format_top3(controller.status()["top3"])
    if cmd == "/testar":
        if len(parts) < 2:
            return "Uso: /testar <id da reação> (ex.: /testar roxo)"
        return await controller.test_reaction(parts[1])
    if cmd in ("/ajuda", "/help", "/start"):
        return HELP
    return f"Comando não reconhecido. {HELP}"
