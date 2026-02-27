"""
Fetch bank account balances from the Open Finance API.
"""

import logging
from datetime import datetime, timezone

from src.config import settings
from src.open_finance.client import client

logger = logging.getLogger(__name__)


async def fetch_accounts() -> dict:
    try:
        data = await client.get("/accounts", params={"itemId": settings.pluggy_item_id})
        accounts = []
        for item in data.get("results", []):
            institution_obj = item.get("institution") or {}
            accounts.append({
                "account_id": item["id"],
                "institution": institution_obj.get("name") or item.get("name", "Unknown"),
                "type": item.get("subtype", item.get("type", "CHECKING_ACCOUNT")),
                "balance_cents": int(round(float(item.get("balance", 0)) * 100)),
                "currency": item.get("currencyCode", "BRL"),
                "last_updated": datetime.now(tz=timezone.utc),
            })
        logger.info("Fetched %d accounts.", len(accounts))
        return {"error": False, "data": accounts}
    except Exception as exc:
        logger.error("fetch_accounts failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
