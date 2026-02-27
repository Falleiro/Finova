"""
Polls the Open Finance API every POLL_INTERVAL_SECONDS for investment swings.
Fires Telegram alerts when any position moves ±INVESTMENT_ALERT_THRESHOLD%.
"""

import asyncio
import logging

from telegram.ext import Application

from src.config import settings
from src.database.crud import clear_investment_alerts, upsert_investment
from src.database.models import AsyncSessionLocal
from src.open_finance.investments import fetch_investments
from src.telegram.formatter import fmt_investment_alert

logger = logging.getLogger(__name__)


class InvestmentWatcher:
    def __init__(self, app: Application) -> None:
        self._app = app
        self._chat_id = settings.telegram_chat_id

    async def run(self) -> None:
        logger.info("InvestmentWatcher started (interval=%ds).", settings.poll_interval_seconds)
        while True:
            try:
                await self._poll()
            except asyncio.CancelledError:
                logger.info("InvestmentWatcher stopped.")
                break
            except Exception as exc:
                logger.error("InvestmentWatcher error: %s", exc)
            await asyncio.sleep(settings.poll_interval_seconds)

    async def _poll(self) -> None:
        result = await fetch_investments()
        if result["error"]:
            logger.warning("Investment fetch error: %s", result["message"])
            return

        async with AsyncSessionLocal() as session:
            for inv_data in result["data"]:
                inv = await upsert_investment(session, inv_data)
                if inv.alert_triggered:
                    await self._send_alert(inv)
                    inv.alert_triggered = False
            await session.commit()

    async def _send_alert(self, inv) -> None:
        try:
            text = fmt_investment_alert(inv)
            await self._app.bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to send investment alert for %s: %s", inv.ticker, exc)
