"""
scripts/fetch_monthly_data.py

Data Fetcher — monthly report data collection for January 2026.

Fetches:
  1. All transactions 2026-01-01 to 2026-01-31  (current report month)
  2. Investment portfolio (current snapshot + performance)
  3. Income records from January 2026  (filtered from transactions)
  4. Transactions 2025-12-01 to 2025-12-31  (prior month, for MoM comparison)
  5. Current account balances

All data is upserted into the local SQLite DB and also written to
/tmp/finova_monthly_data.json for the report-builder to consume.

Usage (from project root, with venv active):
    python -m scripts.fetch_monthly_data
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when run as a script
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import classify_transaction, settings  # noqa: E402
from src.database.models import AsyncSessionLocal, init_db  # noqa: E402
from src.database.crud import (  # noqa: E402
    get_all_accounts,
    get_all_investments,
    insert_transaction,
    upsert_account,
    upsert_investment,
)
from src.open_finance.client import client  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("data-fetcher.monthly")

# ---------------------------------------------------------------------------
# Date ranges
# ---------------------------------------------------------------------------
REPORT_MONTH_FROM = "2026-01-01"
REPORT_MONTH_TO = "2026-01-31"
PRIOR_MONTH_FROM = "2025-12-01"
PRIOR_MONTH_TO = "2025-12-31"

OUTPUT_PATH = Path("/tmp/finova_monthly_data.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _to_cents(value) -> int:
    return int(round(_safe_float(value) * 100))


def _parse_timestamp(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(tz=timezone.utc)


def _serialize(obj):
    """JSON serialiser that handles datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


# ---------------------------------------------------------------------------
# Fetch accounts
# ---------------------------------------------------------------------------

async def fetch_and_store_accounts(session) -> dict:
    """Fetch current balances for all connected accounts and upsert into DB."""
    logger.info("Fetching account balances ...")
    try:
        data = await client.get("/accounts", params={"itemId": settings.pluggy_item_id})
        accounts = []
        for item in data.get("results", []):
            institution_obj = item.get("institution") or {}
            record = {
                "account_id": item["id"],
                "institution": institution_obj.get("name") or item.get("name", "Unknown"),
                "type": item.get("subtype", item.get("type", "CHECKING_ACCOUNT")),
                "balance_cents": _to_cents(item.get("balance", 0)),
                "currency": item.get("currencyCode", "BRL"),
                "last_updated": datetime.now(tz=timezone.utc),
            }
            await upsert_account(session, record)
            accounts.append(record)

        logger.info("Fetched and stored %d account(s).", len(accounts))
        return {"error": False, "data": accounts}

    except Exception as exc:
        logger.error("fetch_and_store_accounts failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}


# ---------------------------------------------------------------------------
# Fetch transactions for a date range
# ---------------------------------------------------------------------------

async def fetch_and_store_transactions(
    session,
    from_date: str,
    to_date: str,
    label: str = "",
) -> dict:
    """
    Fetch all transactions across every account for the given date range.
    Deduplicates against the DB (insert_transaction skips existing IDs).
    Returns the full list regardless of whether each was new or already known.
    """
    logger.info("Fetching transactions [%s] %s -> %s ...", label, from_date, to_date)
    try:
        accounts_data = await client.get(
            "/accounts", params={"itemId": settings.pluggy_item_id}
        )
        account_ids = [item["id"] for item in accounts_data.get("results", [])]
        if not account_ids:
            logger.warning("No account IDs returned — cannot fetch transactions.")
            return {"error": False, "data": []}

        transactions = []
        for account_id in account_ids:
            resp = await client.get(
                "/transactions",
                params={
                    "accountId": account_id,
                    "from": from_date,
                    "to": to_date,
                    "pageSize": 500,
                },
            )
            for item in resp.get("results", []):
                raw_amount = _safe_float(item.get("amount", 0))
                # Pluggy returns DEBIT amounts as positive values with type=DEBIT.
                # Convert debits to negative cents so the sign carries semantic meaning.
                tx_type = (item.get("type") or "").upper()
                amount_cents = _to_cents(raw_amount)
                if tx_type == "DEBIT":
                    amount_cents = -abs(amount_cents)
                else:
                    amount_cents = abs(amount_cents)

                description = item.get("description", "")
                merchant_raw = item.get("merchant")
                merchant: str | None = None
                if isinstance(merchant_raw, dict):
                    merchant = merchant_raw.get("name") or None
                elif isinstance(merchant_raw, str) and merchant_raw.strip():
                    merchant = merchant_raw.strip()

                category = classify_transaction(description, merchant)
                ts = _parse_timestamp(item.get("date", item.get("timestamp", "")))

                record = {
                    "transaction_id": item["id"],
                    "account_id": item.get("accountId", account_id),
                    "amount_cents": amount_cents,
                    "description": description,
                    "merchant": merchant,
                    "category": category,
                    "timestamp": ts,
                    "already_notified": False,
                }
                # insert_transaction is a no-op if transaction_id already exists
                await insert_transaction(session, record)
                transactions.append(record)

        logger.info(
            "Fetched %d transaction(s) [%s] across %d account(s).",
            len(transactions),
            label,
            len(account_ids),
        )
        return {"error": False, "data": transactions}

    except Exception as exc:
        logger.error("fetch_and_store_transactions [%s] failed: %s", label, exc)
        return {"error": True, "message": str(exc), "data": None}


# ---------------------------------------------------------------------------
# Fetch investments
# ---------------------------------------------------------------------------

async def fetch_and_store_investments(session) -> dict:
    """Fetch current investment portfolio and upsert into DB."""
    logger.info("Fetching investment portfolio ...")
    try:
        data = await client.get("/investments", params={"itemId": settings.pluggy_item_id})
        investments = []
        for item in data.get("results", []):
            quantity = _safe_float(item.get("quantity", 1) or 1, default=1.0)
            total_value_cents = _to_cents(item.get("value", item.get("balance", 0)))
            invested_cents = _to_cents(item.get("amount", 0))

            # Daily change approximation from monthly rate (Pluggy does not expose
            # per-unit open/current prices separately for fixed-income products)
            last_month_rate = _safe_float(item.get("lastMonthRate") or 0)
            annual_rate = _safe_float(item.get("annualRate") or 0)
            if last_month_rate:
                daily_change_pct = round(last_month_rate / 30, 4)
            elif annual_rate:
                daily_change_pct = round(annual_rate / 365, 4)
            else:
                daily_change_pct = 0.0

            current_price_cents = int(total_value_cents / quantity) if quantity else 0
            open_price_cents = (
                int(invested_cents / quantity)
                if (quantity and invested_cents)
                else current_price_cents
            )

            alert_triggered = abs(daily_change_pct) >= settings.investment_alert_threshold

            # Total gain in cents (current value minus invested amount)
            gain_cents = total_value_cents - invested_cents

            record = {
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
                # Extra fields for the report-builder (not persisted in DB model)
                "invested_cents": invested_cents,
                "gain_cents": gain_cents,
                "annual_rate": annual_rate,
                "last_month_rate": last_month_rate,
                "subtype": item.get("subtype", ""),
            }
            # upsert_investment only persists fields that match Investment columns;
            # the extra keys are harmless (SQLAlchemy ignores unknown kwargs at the
            # model constructor level — but to be safe we pass only model fields)
            db_record = {k: v for k, v in record.items() if k in {
                "asset_id", "ticker", "name", "quantity",
                "current_price_cents", "open_price_cents", "total_value_cents",
                "daily_change_pct", "alert_triggered", "last_updated",
            }}
            await upsert_investment(session, db_record)
            investments.append(record)

        logger.info("Fetched and stored %d investment position(s).", len(investments))
        return {"error": False, "data": investments}

    except Exception as exc:
        logger.error("fetch_and_store_investments failed: %s", exc)
        return {"error": True, "message": str(exc), "data": None}


# ---------------------------------------------------------------------------
# Filter income records
# ---------------------------------------------------------------------------

def extract_income_records(transactions: list[dict]) -> list[dict]:
    """
    Return only the transactions that were classified as Income.
    These are already stored in the DB as regular transactions; this just
    produces a convenience filtered list for the report-builder.
    """
    return [tx for tx in transactions if tx.get("category") == "Income"]


# ---------------------------------------------------------------------------
# Summary stats helpers
# ---------------------------------------------------------------------------

def _summarise_transactions(transactions: list[dict]) -> dict:
    total_debits = sum(t["amount_cents"] for t in transactions if t["amount_cents"] < 0)
    total_credits = sum(t["amount_cents"] for t in transactions if t["amount_cents"] > 0)
    by_category: dict[str, int] = {}
    for tx in transactions:
        cat = tx.get("category", "Other")
        by_category[cat] = by_category.get(cat, 0) + tx["amount_cents"]
    return {
        "count": len(transactions),
        "total_debits_cents": total_debits,
        "total_credits_cents": total_credits,
        "net_cents": total_credits + total_debits,  # debits are negative
        "by_category_cents": by_category,
    }


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def run() -> dict:
    logger.info("=== FINOVA Data Fetcher — Monthly Report (January 2026) ===")

    # Initialise DB schema if it does not yet exist
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Current account balances
        accounts_result = await fetch_and_store_accounts(session)

        # 2. January 2026 transactions (report month)
        jan_result = await fetch_and_store_transactions(
            session,
            from_date=REPORT_MONTH_FROM,
            to_date=REPORT_MONTH_TO,
            label="Jan-2026",
        )

        # 3. Investment portfolio
        investments_result = await fetch_and_store_investments(session)

        # 4. December 2025 transactions (prior month for MoM comparison)
        dec_result = await fetch_and_store_transactions(
            session,
            from_date=PRIOR_MONTH_FROM,
            to_date=PRIOR_MONTH_TO,
            label="Dec-2025",
        )

    # 5. Income records — derived from January transactions
    jan_transactions = jan_result["data"] if not jan_result.get("error") else []
    income_records = extract_income_records(jan_transactions)

    # -------------------------------------------------------------------
    # Build structured payload for report-builder
    # -------------------------------------------------------------------
    jan_summary = _summarise_transactions(jan_transactions)
    dec_transactions = dec_result["data"] if not dec_result.get("error") else []
    dec_summary = _summarise_transactions(dec_transactions)

    # Month-over-month deltas
    mom_spend_delta_cents = (
        jan_summary["total_debits_cents"] - dec_summary["total_debits_cents"]
    )
    mom_income_delta_cents = (
        jan_summary["total_credits_cents"] - dec_summary["total_credits_cents"]
    )

    # Investment totals
    investments = investments_result["data"] if not investments_result.get("error") else []
    portfolio_total_value_cents = sum(i["total_value_cents"] for i in investments)
    portfolio_total_invested_cents = sum(i.get("invested_cents", 0) for i in investments)
    portfolio_total_gain_cents = sum(i.get("gain_cents", 0) for i in investments)
    alerted_investments = [i for i in investments if i.get("alert_triggered")]

    # Account balances total
    accounts = accounts_result["data"] if not accounts_result.get("error") else []
    total_balance_cents = sum(a["balance_cents"] for a in accounts)

    payload = {
        "meta": {
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "report_month": "2026-01",
            "prior_month": "2025-12",
            "report_month_range": {"from": REPORT_MONTH_FROM, "to": REPORT_MONTH_TO},
            "prior_month_range": {"from": PRIOR_MONTH_FROM, "to": PRIOR_MONTH_TO},
            "fetch_errors": {
                "accounts": accounts_result.get("error", False),
                "jan_transactions": jan_result.get("error", False),
                "dec_transactions": dec_result.get("error", False),
                "investments": investments_result.get("error", False),
            },
        },
        # --- Section 1: Account balances ---
        "accounts": {
            "records": accounts,
            "total_balance_cents": total_balance_cents,
        },
        # --- Section 2: Report-month transactions (January 2026) ---
        "report_month_transactions": {
            "period": {"from": REPORT_MONTH_FROM, "to": REPORT_MONTH_TO},
            "records": jan_transactions,
            "summary": jan_summary,
        },
        # --- Section 3: Investment portfolio ---
        "investments": {
            "records": investments,
            "portfolio_total_value_cents": portfolio_total_value_cents,
            "portfolio_total_invested_cents": portfolio_total_invested_cents,
            "portfolio_total_gain_cents": portfolio_total_gain_cents,
            "alerted_positions": alerted_investments,
        },
        # --- Section 4: Income records (January 2026, filtered) ---
        "income": {
            "period": {"from": REPORT_MONTH_FROM, "to": REPORT_MONTH_TO},
            "records": income_records,
            "total_income_cents": sum(r["amount_cents"] for r in income_records),
        },
        # --- Section 5: Prior-month transactions (December 2025) ---
        "prior_month_transactions": {
            "period": {"from": PRIOR_MONTH_FROM, "to": PRIOR_MONTH_TO},
            "records": dec_transactions,
            "summary": dec_summary,
        },
        # --- Month-over-month comparison ---
        "month_over_month": {
            "spend_delta_cents": mom_spend_delta_cents,
            "income_delta_cents": mom_income_delta_cents,
            "net_delta_cents": jan_summary["net_cents"] - dec_summary["net_cents"],
        },
    }

    # -------------------------------------------------------------------
    # Persist JSON to /tmp for report-builder
    # -------------------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=_serialize, ensure_ascii=False)

    logger.info("Monthly data written to %s", OUTPUT_PATH)

    # Log a human-readable summary (no raw credentials in output)
    logger.info(
        "SUMMARY — Accounts: %d | Jan txns: %d | Dec txns: %d | Investments: %d | Income entries: %d",
        len(accounts),
        len(jan_transactions),
        len(dec_transactions),
        len(investments),
        len(income_records),
    )
    logger.info(
        "TOTALS — Balance: R$%.2f | Jan spend: R$%.2f | Jan income: R$%.2f | Portfolio: R$%.2f | P&L: R$%.2f",
        total_balance_cents / 100,
        abs(jan_summary["total_debits_cents"]) / 100,
        jan_summary["total_credits_cents"] / 100,
        portfolio_total_value_cents / 100,
        portfolio_total_gain_cents / 100,
    )

    return payload


if __name__ == "__main__":
    asyncio.run(run())
