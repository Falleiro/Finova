"""
Message formatting helpers for Telegram output.
Converts raw data dicts into human-readable Markdown strings.
"""

from datetime import datetime

from src.database.models import Account, Investment, Transaction


def fmt_brl(cents: int) -> str:
    value = cents / 100
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def fmt_accounts(accounts: list[Account]) -> str:
    if not accounts:
        return "Nenhuma conta encontrada."
    lines = ["*Saldo das Contas*\n"]
    total = 0
    for acc in accounts:
        emoji = {"checking": "🏦", "savings": "💰", "credit_card": "💳"}.get(acc.type, "🏦")
        lines.append(f"{emoji} *{acc.institution}* ({acc.type})\n   {fmt_brl(acc.balance_cents)}")
        total += acc.balance_cents
    lines.append(f"\n*Total: {fmt_brl(total)}*")
    return "\n".join(lines)


def fmt_transactions(transactions: list[Transaction], title: str = "Extrato") -> str:
    if not transactions:
        return f"*{title}*\n\nNenhuma transação encontrada."
    lines = [f"*{title}*\n"]
    for tx in transactions[:20]:  # cap to avoid Telegram message size limit
        sign = "+" if tx.amount_cents > 0 else ""
        date_str = tx.timestamp.strftime("%d/%m %H:%M")
        lines.append(
            f"`{date_str}` {tx.category}\n"
            f"   {tx.description[:40]}\n"
            f"   *{sign}{fmt_brl(tx.amount_cents)}*"
        )
    if len(transactions) > 20:
        lines.append(f"\n_... e mais {len(transactions) - 20} transações._")
    return "\n".join(lines)


def fmt_investments(investments: list[Investment]) -> str:
    if not investments:
        return "Nenhum ativo na carteira."
    lines = ["*Carteira de Investimentos*\n"]
    total = 0
    for inv in investments:
        arrow = "📈" if inv.daily_change_pct >= 0 else "📉"
        lines.append(
            f"{arrow} *{inv.ticker}* — {inv.name}\n"
            f"   {inv.quantity:.4f} × {fmt_brl(inv.current_price_cents)}"
            f" = *{fmt_brl(inv.total_value_cents)}*\n"
            f"   Hoje: {fmt_pct(inv.daily_change_pct)}"
        )
        total += inv.total_value_cents
    lines.append(f"\n*Total investido: {fmt_brl(total)}*")
    return "\n".join(lines)


def fmt_investment_alert(inv: Investment) -> str:
    direction = "SUBIU" if inv.daily_change_pct > 0 else "CAIU"
    arrow = "🚀" if inv.daily_change_pct > 0 else "🔻"
    return (
        f"{arrow} *Alerta de Investimento*\n\n"
        f"*{inv.ticker}* {direction} *{fmt_pct(inv.daily_change_pct)}* hoje!\n"
        f"Preço atual: {fmt_brl(inv.current_price_cents)}\n"
        f"Valor total: {fmt_brl(inv.total_value_cents)}"
    )


def fmt_large_transaction_alert(tx: Transaction) -> str:
    direction = "crédito" if tx.amount_cents > 0 else "débito"
    emoji = "💸" if tx.amount_cents < 0 else "💰"
    date_str = tx.timestamp.strftime("%d/%m/%Y %H:%M")
    return (
        f"{emoji} *Transação Detectada*\n\n"
        f"*{fmt_brl(abs(tx.amount_cents))}* ({direction})\n"
        f"{tx.description}\n"
        f"Categoria: {tx.category}\n"
        f"Data: {date_str}"
    )
