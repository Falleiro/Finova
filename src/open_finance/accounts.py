"""
Fetch bank account balances from the Open Finance API.
"""

import logging
from datetime import datetime, timezone

from src.open_finance.client import client

logger = logging.getLogger(__name__)


async def fetch_accounts() -> dict:
    try:
        data = await client.get("/accounts")
        accounts = []
        for item in data.get("data", []):
            accounts.append({
                "account_id": item["accountId"],
                "institution": item.get("institution", "Unknown"),
                "type": item.get("type", "checking"),
                "balance_cents": int(round(float(item.get("balance", 0)) * 100)),
                "currency": item.get("currency", "BRL"),
                "last_updated": datetime.now(tz=timezone.utc),
            })
        logger.info("Fetched %d accounts.", len(accounts))
        return {"error": False, "data": accounts}
    except Exception as exc:
        logger.error("fetch_accounts failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
