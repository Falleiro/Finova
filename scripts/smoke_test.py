"""
Smoke test: verifica se a API do Open Finance está respondendo e envia
um resumo para o Telegram. Rode diretamente:

    python scripts/smoke_test.py

Não inicia o bot completo — apenas faz chamadas pontuais para validar
credenciais e integração.
"""

import asyncio
import json
import sys
import logging
from pathlib import Path

# Garante que `src/` seja encontrado quando rodado da raiz do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smoke_test")

SEPARATOR = "─" * 40


def _fmt_brl(cents: int) -> str:
    value = cents / 100
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


async def test_accounts() -> list[dict]:
    logger.info("Testando fetch_accounts()...")
    from src.open_finance.accounts import fetch_accounts
    result = await fetch_accounts()
    if result["error"]:
        logger.error("FALHOU: %s", result["message"])
        return []
    accounts = result["data"]
    logger.info("OK — %d conta(s) retornada(s):", len(accounts))
    for acc in accounts:
        print(f"  • {acc['institution']} ({acc['type']}): {_fmt_brl(acc['balance_cents'])}")
    return accounts


async def test_transactions() -> list[dict]:
    logger.info("Testando fetch_transactions(days=7)...")
    from src.open_finance.transactions import fetch_transactions
    result = await fetch_transactions(days=7)
    if result["error"]:
        logger.error("FALHOU: %s", result["message"])
        return []
    txs = result["data"]
    logger.info("OK — %d transação(ões) nos últimos 7 dias:", len(txs))
    for tx in txs[:5]:
        sign = "+" if tx["amount_cents"] > 0 else ""
        print(f"  • [{tx['category']}] {tx['description'][:40]}: {sign}{_fmt_brl(tx['amount_cents'])}")
    if len(txs) > 5:
        print(f"  ... e mais {len(txs) - 5} transação(ões).")
    return txs


async def test_investments() -> list[dict]:
    logger.info("Testando fetch_investments()...")
    from src.open_finance.investments import fetch_investments
    result = await fetch_investments()
    if result["error"]:
        logger.error("FALHOU: %s", result["message"])
        return []
    investments = result["data"]
    logger.info("OK — %d ativo(s) na carteira:", len(investments))
    for inv in investments:
        alert_flag = " ⚠️ ALERTA" if inv["alert_triggered"] else ""
        print(f"  • {inv['ticker']} ({inv['name']}): {_fmt_brl(inv['total_value_cents'])} | {_fmt_pct(inv['daily_change_pct'])}{alert_flag}")
    return investments


async def send_telegram_summary(accounts: list, transactions: list, investments: list) -> None:
    logger.info("Enviando mensagem de teste para o Telegram...")
    from src.config import settings
    import httpx

    n_accounts = len(accounts)
    n_txs = len(transactions)
    n_investments = len(investments)

    total_balance = sum(a["balance_cents"] for a in accounts)
    total_portfolio = sum(i["total_value_cents"] for i in investments)
    alerts = [i for i in investments if i["alert_triggered"]]

    lines = [
        "🧪 *FINOVA — Smoke Test OK*\n",
        f"✅ API Open Finance respondendo normalmente\n",
        f"🏦 *Contas:* {n_accounts} conta(s) | Saldo total: {_fmt_brl(total_balance)}",
        f"💳 *Transações (7d):* {n_txs} registro(s)",
        f"📊 *Carteira:* {n_investments} ativo(s) | Total: {_fmt_brl(total_portfolio)}",
    ]

    if alerts:
        tickers = ", ".join(f"{i['ticker']} ({_fmt_pct(i['daily_change_pct'])})" for i in alerts)
        lines.append(f"⚠️ *Alertas ativos:* {tickers}")

    message = "\n".join(lines)

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    async with httpx.AsyncClient(timeout=15) as http:
        try:
            response = await http.post(url, json=payload)
            response.raise_for_status()
            logger.info("Mensagem enviada para o Telegram com sucesso.")
        except httpx.HTTPError as exc:
            logger.error("Falha ao enviar para o Telegram: %s", exc)
            if hasattr(exc, "response"):
                logger.error("Resposta: %s", exc.response.text)


async def main() -> None:
    print(f"\n{SEPARATOR}")
    print("  FINOVA — Smoke Test")
    print(f"{SEPARATOR}\n")

    accounts = await test_accounts()
    print()
    transactions = await test_transactions()
    print()
    investments = await test_investments()
    print()

    if accounts or transactions or investments:
        await send_telegram_summary(accounts, transactions, investments)
    else:
        logger.warning("Nenhum dado retornado — mensagem de Telegram não enviada.")

    print(f"\n{SEPARATOR}")
    print("  Smoke test concluído.")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    asyncio.run(main())
