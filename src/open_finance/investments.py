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
        data = await client.get("/investments")
        investments = []
        for item in data.get("data", []):
            current_price_cents = int(round(float(item.get("currentPrice", 0)) * 100))
            open_price_cents = int(round(float(item.get("openPrice", 0)) * 100))
            quantity = float(item.get("quantity", 0))
            total_value_cents = int(round(current_price_cents * quantity))

            daily_change_pct = 0.0
            if open_price_cents > 0:
                daily_change_pct = ((current_price_cents - open_price_cents) / open_price_cents) * 100

            alert_triggered = abs(daily_change_pct) >= settings.investment_alert_threshold

            investments.append({
                "asset_id": item["assetId"],
                "ticker": item.get("ticker", ""),
                "name": item.get("name", ""),
                "quantity": quantity,
                "current_price_cents": current_price_cents,
                "open_price_cents": open_price_cents,
                "total_value_cents": total_value_cents,
                "daily_change_pct": round(daily_change_pct, 4),
                "alert_triggered": alert_triggered,
                "last_updated": datetime.now(tz=timezone.utc),
            })

        logger.info("Fetched %d investment positions.", len(investments))
        return {"error": False, "data": investments}
    except Exception as exc:
        logger.error("fetch_investments failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}
