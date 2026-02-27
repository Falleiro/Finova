"""
Builds the daily financial summary message.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.database.crud import get_all_accounts, get_transactions_since
from src.database.models import AsyncSessionLocal
from src.open_finance.accounts import fetch_accounts
from src.open_finance.transactions import fetch_transactions
from src.database.crud import upsert_account, insert_transaction
from src.telegram.formatter import fmt_brl

logger = logging.getLogger(__name__)


async def build_daily_summary() -> str:
    # Refresh data
    acc_result = await fetch_accounts()
    tx_result = await fetch_transactions(days=1)

    async with AsyncSessionLocal() as session:
        if not acc_result["error"]:
            for a in acc_result["data"]:
                await upsert_account(session, a)
        if not tx_result["error"]:
            for t in tx_result["data"]:
                await insert_transaction(session, t)

        accounts = await get_all_accounts(session)
        since = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        transactions = await get_transactions_since(session, since)

    total_balance = sum(a.balance_cents for a in accounts)
    debits = [t for t in transactions if t.amount_cents < 0]
    credits = [t for t in transactions if t.amount_cents > 0]
    total_spent = abs(sum(t.amount_cents for t in debits))
    total_received = sum(t.amount_cents for t in credits)

    # Spending by category
    by_category: dict[str, int] = defaultdict(int)
    for tx in debits:
        by_category[tx.category] += abs(tx.amount_cents)

    today = datetime.now(tz=timezone.utc).strftime("%d/%m/%Y")
    lines = [
        f"*Bom dia! Resumo de {today}*\n",
        f"*Saldo total:* {fmt_brl(total_balance)}",
        f"*Entrada (24h):* {fmt_brl(total_received)}",
        f"*Saída (24h):* {fmt_brl(total_spent)}",
    ]

    if by_category:
        lines.append("\n*Gastos por categoria:*")
        for cat, amount in sorted(by_category.items(), key=lambda x: -x[1]):
            lines.append(f"  • {cat}: {fmt_brl(amount)}")

    if not transactions:
        lines.append("\n_Nenhuma transação nas últimas 24 horas._")

    return "\n".join(lines)
