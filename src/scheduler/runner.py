"""
Configures and starts the APScheduler instance.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application

from src.config import settings
from src.scheduler.jobs import job_daily_summary, job_monthly_report

logger = logging.getLogger(__name__)


def start_scheduler(app: Application) -> AsyncIOScheduler:
    app.bot_data["chat_id"] = settings.telegram_chat_id

    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    # Daily summary
    scheduler.add_job(
        job_daily_summary,
        trigger=CronTrigger(
            hour=settings.daily_report_hour,
            minute=settings.daily_report_minute,
            timezone=settings.timezone,
        ),
        args=[app],
        id="daily_summary",
        name="Daily financial summary",
        replace_existing=True,
    )

    # Monthly report — 1st of every month at the same configured time
    scheduler.add_job(
        job_monthly_report,
        trigger=CronTrigger(
            day=1,
            hour=settings.daily_report_hour,
            minute=settings.daily_report_minute,
            timezone=settings.timezone,
        ),
        args=[app],
        id="monthly_report",
        name="Monthly financial report",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started. Daily at %s, monthly on 1st.",
        settings.daily_report_time,
    )
    return scheduler
