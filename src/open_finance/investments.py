"""
Fetch investment portfolio data from the Open Finance API.
"""

import logging
from datetime import datetime, timezone

from src.config import settings
from src.open_finance.client import client

logger = logging.getLogger(__name__)


async def fetch_investments() -> dict:
    try:
        data = await client.get("/investments", params={"itemId": settings.pluggy_item_id})
        investments = []
        for item in data.get("results", []):
            quantity = float(item.get("quantity", 1) or 1)
            # Pluggy returns `value` (current total) and `amount` (invested total)
            total_value_cents = int(round(float(item.get("value", item.get("balance", 0))) * 100))
            invested_cents = int(round(float(item.get("amount", 0)) * 100))

            # Pluggy does not expose open/current per-unit prices directly.
            # Approximate daily change from monthly rate when available.
            last_month_rate = float(item.get("lastMonthRate") or 0)
            daily_change_pct = round(last_month_rate / 30, 4) if last_month_rate else 0.0

            # Derive implied per-unit prices for consistency with the rest of the codebase
            current_price_cents = int(total_value_cents / quantity) if quantity else 0
            open_price_cents = int(invested_cents / quantity) if quantity and invested_cents else current_price_cents

            alert_triggered = abs(daily_change_pct) >= settings.investment_alert_threshold

            investments.append({
                "asset_id": item["id"],
                "ticker": item.get("code") or item.get("name", ""),
                "name": item.get("name", ""),
                "quantity": quantity,
                "current_price_cents": current_price_cents,
                "open_price_cents": open_price_cents,
                "total_value_cents": total_value_cents,
                "daily_change_pct": daily_change_pct,
                "alert_triggered": alert_triggered,
                "last_updated": datetime.now(tz=timezone.utc),
            })

        logger.info("Fetched %d investment positions.", len(investments))
        return {"error": False, "data": investments}
    except Exception as exc:
        logger.error("fetch_investments failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
