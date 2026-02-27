"""
Telegram bot setup — builds the Application instance used throughout FINOVA.
"""

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config import settings
from src.telegram.handlers import (
    cmd_ajuda,
    cmd_carteira,
    cmd_extrato,
    cmd_saldo,
    cmd_start,
    handle_text,
)

logger = logging.getLogger(__name__)


def build_application() -> Application:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("extrato", cmd_extrato))
    app.add_handler(CommandHandler("carteira", cmd_carteira))

    # Free-text intent handler (fallback)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Telegram application built.")
    return app
