"""
Builds the monthly financial report message and optional chart.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

from src.database.crud import get_transactions_since
from src.database.models import AsyncSessionLocal
from src.open_finance.transactions import fetch_transactions
from src.database.crud import insert_transaction
from src.reports.charts import build_spending_chart
from src.telegram.formatter import fmt_brl

logger = logging.getLogger(__name__)


async def build_monthly_report() -> tuple[str, str | None]:
    # Fetch last 30 days
    tx_result = await fetch_transactions(days=30)

    async with AsyncSessionLocal() as session:
        if not tx_result["error"]:
            for t in tx_result["data"]:
                await insert_transaction(session, t)

        now = datetime.now(tz=timezone.utc)
        # First day of current month
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        transactions = await get_transactions_since(session, since)

    debits = [t for t in transactions if t.amount_cents < 0]
    credits = [t for t in transactions if t.amount_cents > 0]
    total_spent = abs(sum(t.amount_cents for t in debits))
    total_received = sum(t.amount_cents for t in credits)

    by_category: dict[str, int] = defaultdict(int)
    for tx in debits:
        by_category[tx.category] += abs(tx.amount_cents)

    month_name = now.strftime("%B %Y")
    lines = [
        f"*Relatório Mensal — {month_name}*\n",
        f"*Total recebido:* {fmt_brl(total_received)}",
        f"*Total gasto:* {fmt_brl(total_spent)}",
        f"*Saldo do mês:* {fmt_brl(total_received - total_spent)}",
        f"*Transações:* {len(transactions)}",
    ]

    if by_category:
        lines.append("\n*Gastos por categoria:*")
        for cat, amount in sorted(by_category.items(), key=lambda x: -x[1]):
            pct = (amount / total_spent * 100) if total_spent else 0
            lines.append(f"  • {cat}: {fmt_brl(amount)} ({pct:.1f}%)")

    chart_path: str | None = None
    if by_category:
        try:
            chart_path = await build_spending_chart(by_category, month_name)
        except Exception as exc:
            logger.warning("Chart generation failed: %s", exc)

    return "\n".join(lines), chart_path
