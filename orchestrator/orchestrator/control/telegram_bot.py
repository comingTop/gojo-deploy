from __future__ import annotations

from .commands import handle_command
from .controller import LiveController


class TelegramControl:
    """Thin python-telegram-bot wiring around the pure ``handle_command`` dispatcher.

    Lazy-imports telegram (opt-in ``control`` extra). All command logic and auth
    live in ``commands.handle_command`` (unit-tested); this only forwards messages.
    """

    def __init__(self, token: str, controller: LiveController, allowed_chat_ids):
        self.token = token
        self.controller = controller
        self.allowed = set(allowed_chat_ids or [])

    def build_app(self):
        from telegram.ext import ApplicationBuilder, MessageHandler, filters

        app = ApplicationBuilder().token(self.token).build()

        async def _on_message(update, _context):
            if update.message is None or update.effective_chat is None:
                return
            reply = await handle_command(
                update.message.text or "",
                update.effective_chat.id,
                self.controller,
                self.allowed,
            )
            if reply:
                await update.message.reply_text(reply)

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.COMMAND, _on_message))
        return app

    def run(self) -> None:
        self.build_app().run_polling()
