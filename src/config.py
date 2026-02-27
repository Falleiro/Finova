"""
Central configuration — loads all environment variables from .env.
All other modules import `settings` from here.
"""

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value


@dataclass(frozen=True)
class Settings:
    # Telegram
    telegram_bot_token: str = field(default_factory=lambda: _require("TELEGRAM_BOT_TOKEN"))
    telegram_chat_id: str = field(default_factory=lambda: _require("TELEGRAM_CHAT_ID"))

    # Open Finance API
    open_finance_client_id: str = field(default_factory=lambda: _require("OPEN_FINANCE_CLIENT_ID"))
    open_finance_client_secret: str = field(default_factory=lambda: _require("OPEN_FINANCE_CLIENT_SECRET"))
    open_finance_base_url: str = field(default_factory=lambda: _require("OPEN_FINANCE_BASE_URL"))
    open_finance_consent_token: str = field(default_factory=lambda: _require("OPEN_FINANCE_CONSENT_TOKEN"))

    # App behaviour
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "America/Sao_Paulo"))
    daily_report_time: str = field(default_factory=lambda: os.getenv("DAILY_REPORT_TIME", "08:00"))
    large_transaction_threshold: int = field(
        default_factory=lambda: int(os.getenv("LARGE_TRANSACTION_THRESHOLD", "200"))
    )
    investment_alert_threshold: float = field(
        default_factory=lambda: float(os.getenv("INVESTMENT_ALERT_THRESHOLD", "3.0"))
    )
    poll_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    )

    # Database
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/finova.db")
    )

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def daily_report_hour(self) -> int:
        return int(self.daily_report_time.split(":")[0])

    @property
    def daily_report_minute(self) -> int:
        return int(self.daily_report_time.split(":")[1])


settings = Settings()

# ── Category keyword mapping ─────────────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food & Delivery": [
        "ifood", "rappi", "uber eats", "mcdonalds", "subway",
        "restaurante", "padaria", "lanchonete", "burger", "pizza",
    ],
    "Transport": [
        "uber", "99", "taxi", "metro", "combustivel", "posto",
        "shell", "ipiranga", "gasolina", "estacionamento",
    ],
    "Subscriptions": [
        "netflix", "spotify", "amazon prime", "youtube", "steam",
        "adobe", "globoplay", "disney", "hbo",
    ],
    "Health": [
        "farmacia", "drogasil", "ultrafarma", "medico", "hospital",
        "clinica", "plano de saude", "dentista",
    ],
    "Supermarket": [
        "mercado", "supermercado", "atacado", "carrefour", "extra",
        "pao de acucar", "assai", "hortifruti",
    ],
    "Shopping": [
        "amazon", "shopee", "mercado livre", "magazine", "americanas",
        "renner", "zara", "riachuelo", "c&a",
    ],
    "Housing & Bills": [
        "aluguel", "condominio", "energia", "agua", "gas", "internet",
        "tim", "vivo", "claro", "oi", "luz",
    ],
    "Income": [
        "salario", "pagamento", "deposito", "transferencia recebida",
        "pix recebido", "credito em conta",
    ],
    "Investments": [
        "investimento", "corretora", "xp", "clear", "rico",
        "btg", "nuinvest", "tesouro",
    ],
}


def classify_transaction(description: str, merchant: str | None = None) -> str:
    text = f"{description} {merchant or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"
