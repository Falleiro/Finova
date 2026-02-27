"""
Polls the Open Finance API every POLL_INTERVAL_SECONDS for new transactions.
Fires Telegram alerts for new or large transactions.
"""

import asyncio
import logging

from telegram.ext import Application

from src.config import settings
from src.database.crud import (
    get_unnotified_transactions,
    insert_transaction,
    mark_transaction_notified,
)
from src.database.models import AsyncSessionLocal
from src.open_finance.transactions import fetch_transactions
from src.telegram.formatter import fmt_large_transaction_alert

logger = logging.getLogger(__name__)

LARGE_THRESHOLD_CENTS = settings.large_transaction_threshold * 100


class TransactionWatcher:
    def __init__(self, app: Application) -> None:
        self._app = app
        self._chat_id = settings.telegram_chat_id

    async def run(self) -> None:
        logger.info("TransactionWatcher started (interval=%ds).", settings.poll_interval_seconds)
        while True:
            try:
                await self._poll()
            except asyncio.CancelledError:
                logger.info("TransactionWatcher stopped.")
                break
            except Exception as exc:
                logger.error("TransactionWatcher error: %s", exc)
            await asyncio.sleep(settings.poll_interval_seconds)

    async def _poll(self) -> None:
        result = await fetch_transactions(days=1)
        if result["error"]:
            logger.warning("Transaction fetch error: %s", result["message"])
            return

        async with AsyncSessionLocal() as session:
            for tx_data in result["data"]:
                tx = await insert_transaction(session, tx_data)
                if tx is None:
                    continue  # already in DB

                # Alert on large transactions
                if abs(tx.amount_cents) >= LARGE_THRESHOLD_CENTS:
                    await self._send_alert(tx)
                    await mark_transaction_notified(session, tx.transaction_id)

    async def _send_alert(self, tx) -> None:
        try:
            text = fmt_large_transaction_alert(tx)
            await self._app.bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to send transaction alert: %s", exc)
