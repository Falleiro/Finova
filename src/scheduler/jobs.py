"""
APScheduler job definitions for FINOVA.
- Daily summary at configured time (default 08:00)
- Monthly report on the 1st of every month
"""

import logging

from telegram.ext import Application

from src.reports.daily import build_daily_summary
from src.reports.monthly import build_monthly_report
from src.telegram.formatter import fmt_accounts, fmt_transactions

logger = logging.getLogger(__name__)


async def job_daily_summary(app: Application) -> None:
    logger.info("Running daily summary job...")
    try:
        message = await build_daily_summary()
        await app.bot.send_message(
            chat_id=app.bot_data["chat_id"],
            text=message,
            parse_mode="Markdown",
        )
        logger.info("Daily summary sent.")
    except Exception as exc:
        logger.error("Daily summary job failed: %s", exc)
        try:
            await app.bot.send_message(
                chat_id=app.bot_data["chat_id"],
                text=f"⚠️ Falha ao gerar o resumo diário:\n`{exc}`",
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def job_monthly_report(app: Application) -> None:
    logger.info("Running monthly report job...")
    try:
        message, chart_path = await build_monthly_report()
        if chart_path:
            with open(chart_path, "rb") as f:
                await app.bot.send_photo(
                    chat_id=app.bot_data["chat_id"],
                    photo=f,
                    caption=message,
                    parse_mode="Markdown",
                )
        else:
            await app.bot.send_message(
                chat_id=app.bot_data["chat_id"],
                text=message,
                parse_mode="Markdown",
            )
        logger.info("Monthly report sent.")
    except Exception as exc:
        logger.error("Monthly report job failed: %s", exc)
        try:
            await app.bot.send_message(
                chat_id=app.bot_data["chat_id"],
                text=f"⚠️ Falha ao gerar o relatório mensal:\n`{exc}`",
                parse_mode="Markdown",
            )
        except Exception:
            pass
