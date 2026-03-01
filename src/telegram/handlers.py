"""
Telegram message handlers — intent routing for user commands and free text.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from src.agents.intent_classifier import classify_intent
from src.agents.orchestrator import handle_intent
from src.config import settings

logger = logging.getLogger(__name__)


def _is_authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == settings.telegram_chat_id


def _get_greeting() -> str:
    hour = datetime.now(ZoneInfo("America/Sao_Paulo")).hour
    if 5 <= hour < 12:
        return "Bom dia"
    elif 12 <= hour < 18:
        return "Boa tarde"
    elif 18 <= hour < 24:
        return "Boa noite"
    else:
        return "Boa madrugada"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    greeting = _get_greeting()
    await update.message.reply_text(
        f"{greeting}! Sou o *FINOVA*, seu assistente financeiro pessoal.\n\n"
        "Use /ajuda para ver o que posso fazer por você.",
        parse_mode="Markdown",
    )


async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    text = (
        "*Comandos disponíveis:*\n"
        "/saldo — Ver saldo de todas as contas\n"
        "/extrato — Extrato dos últimos 7 dias\n"
        "/carteira — Posição atual da carteira de investimentos\n\n"
        "Você também pode me perguntar livremente, ex: _\"Quanto gastei esse mês?\"_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await handle_intent(update, context, intent="saldo")


async def cmd_extrato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await handle_intent(update, context, intent="extrato")


async def cmd_carteira(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await handle_intent(update, context, intent="carteira")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    text = update.message.text or ""
    intent = classify_intent(text)
    logger.info("Free-text intent classified as '%s' for message: %s", intent, text[:80])
    await handle_intent(update, context, intent=intent, user_text=text)
