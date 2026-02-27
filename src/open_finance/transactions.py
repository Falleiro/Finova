"""
Fetch transactions from the Open Finance API.
"""

import logging
from datetime import datetime, timezone

from src.config import classify_transaction
from src.open_finance.client import client

logger = logging.getLogger(__name__)


async def fetch_transactions(days: int = 1) -> dict:
    try:
        data = await client.get("/transactions", params={"days": days})
        transactions = []
        for item in data.get("data", []):
            amount_cents = int(round(float(item.get("amount", 0)) * 100))
            description = item.get("description", "")
            merchant = item.get("merchant") or None
            category = classify_transaction(description, merchant)
            transactions.append({
                "transaction_id": item["transactionId"],
                "account_id": item["accountId"],
                "amount_cents": amount_cents,
                "description": description,
                "merchant": merchant,
                "category": category,
                "timestamp": datetime.fromisoformat(item["timestamp"]).replace(tzinfo=timezone.utc),
                "already_notified": False,
            })
        logger.info("Fetched %d transactions (last %dd).", len(transactions), days)
        return {"error": False, "data": transactions}
    except Exception as exc:
        logger.error("fetch_transactions failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
