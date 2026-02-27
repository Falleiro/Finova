"""
Fetch transactions from the Open Finance API.
"""

import logging
from datetime import datetime, timedelta, timezone

from src.config import classify_transaction, settings
from src.open_finance.client import client

logger = logging.getLogger(__name__)


async def fetch_transactions(days: int = 1) -> dict:
    try:
        # Pluggy requires accountId (not itemId) — fetch accounts first
        accounts_data = await client.get("/accounts", params={"itemId": settings.pluggy_item_id})
        account_ids = [item["id"] for item in accounts_data.get("results", [])]

        to_date = datetime.now(tz=timezone.utc)
        from_date = to_date - timedelta(days=days)
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")

        transactions = []
        for account_id in account_ids:
            data = await client.get("/transactions", params={
                "accountId": account_id,
                "from": from_str,
                "to": to_str,
                "pageSize": 500,
            })
            for item in data.get("results", []):
                amount_cents = int(round(float(item.get("amount", 0)) * 100))
                description = item.get("description", "")
                merchant = item.get("merchant") or None
                category = classify_transaction(description, merchant)
                raw_date = item.get("date", item.get("timestamp", ""))
                try:
                    ts = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    ts = datetime.now(tz=timezone.utc)
                transactions.append({
                    "transaction_id": item["id"],
                    "account_id": item.get("accountId", account_id),
                    "amount_cents": amount_cents,
                    "description": description,
                    "merchant": merchant,
                    "category": category,
                    "timestamp": ts,
                    "already_notified": False,
                })

        logger.info("Fetched %d transactions (last %dd).", len(transactions), days)
        return {"error": False, "data": transactions}
    except Exception as exc:
        logger.error("fetch_transactions failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
