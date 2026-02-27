"""
FINOVA — Personal Finance Agent
Entry point: starts the Telegram bot, scheduler, and polling triggers.
"""

import asyncio
import logging
import signal
import sys

from src.config import settings
from src.database.models import init_db
from src.telegram.bot import build_application
from src.scheduler.runner import start_scheduler
from src.triggers.transaction_watcher import TransactionWatcher
from src.triggers.investment_watcher import InvestmentWatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finova.main")


async def main() -> None:
    logger.info("Starting FINOVA agent...")

    # Initialise database
    await init_db()
    logger.info("Database initialised.")

    # Build Telegram application
    app = build_application()

    # Start APScheduler
    scheduler = start_scheduler(app)
    logger.info("Scheduler started.")

    # Start polling triggers
    tx_watcher = TransactionWatcher(app)
    inv_watcher = InvestmentWatcher(app)

    async with app:
        await app.start()
        logger.info("Telegram bot started (polling).")

        watcher_tasks = [
            asyncio.create_task(tx_watcher.run(), name="tx_watcher"),
            asyncio.create_task(inv_watcher.run(), name="inv_watcher"),
        ]

        # Graceful shutdown on SIGINT / SIGTERM
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _shutdown(sig: signal.Signals) -> None:
            logger.info("Received %s — shutting down...", sig.name)
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _shutdown, sig)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler for all signals
                pass

        await stop_event.wait()

        # Cancel background tasks
        for task in watcher_tasks:
            task.cancel()
        await asyncio.gather(*watcher_tasks, return_exceptions=True)

        scheduler.shutdown(wait=False)
        await app.stop()

    logger.info("FINOVA stopped cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
