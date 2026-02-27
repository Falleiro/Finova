"""
Main agent coordinator — routes intents to the correct handler and replies.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.database.crud import get_all_accounts, get_all_investments, get_transactions_since
from src.database.models import AsyncSessionLocal
from src.open_finance.accounts import fetch_accounts
from src.open_finance.investments import fetch_investments
from src.open_finance.transactions import fetch_transactions
from src.database.crud import upsert_account, upsert_investment, insert_transaction
from src.telegram.formatter import fmt_accounts, fmt_investments, fmt_transactions
from src.reports.daily import build_daily_summary
from src.reports.monthly import build_monthly_report

from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def handle_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    intent: str,
    user_text: str = "",
) -> None:
    chat_id = update.effective_chat.id
    try:
        message, photo_path = await _resolve(intent, user_text)
        if photo_path:
            with open(photo_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=message,
                    parse_mode="Markdown",
                )
        else:
            await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as exc:
        logger.error("handle_intent error [%s]: %s", intent, exc)
        await update.message.reply_text(
            f"⚠️ Erro ao processar sua solicitação:\n`{exc}`",
            parse_mode="Markdown",
        )


async def _resolve(intent: str, user_text: str) -> tuple[str, str | None]:
    if intent == "saldo":
        result = await fetch_accounts()
        async with AsyncSessionLocal() as session:
            if not result["error"]:
                for a in result["data"]:
                    await upsert_account(session, a)
            accounts = await get_all_accounts(session)
        return fmt_accounts(accounts), None

    if intent == "extrato":
        result = await fetch_transactions(days=7)
        async with AsyncSessionLocal() as session:
            if not result["error"]:
                for t in result["data"]:
                    await insert_transaction(session, t)
            since = datetime.now(tz=timezone.utc) - timedelta(days=7)
            transactions = await get_transactions_since(session, since)
        return fmt_transactions(transactions, title="Extrato — últimos 7 dias"), None

    if intent == "carteira":
        result = await fetch_investments()
        async with AsyncSessionLocal() as session:
            if not result["error"]:
                for i in result["data"]:
                    await upsert_investment(session, i)
            investments = await get_all_investments(session)
        return fmt_investments(investments), None

    if intent == "resumo_diario":
        message = await build_daily_summary()
        return message, None

    if intent == "relatorio_mensal":
        message, chart = await build_monthly_report()
        return message, chart

    # Default: help
    return (
        "*FINOVA — Comandos disponíveis*\n\n"
        "/saldo — Ver saldo de todas as contas\n"
        "/extrato — Extrato dos últimos 7 dias\n"
        "/carteira — Posição da carteira de investimentos\n\n"
        "_Você também pode me perguntar livremente!_"
    ), None
