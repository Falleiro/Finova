"""
SQLAlchemy ORM models for FINOVA's local SQLite cache.
All monetary values are stored as integers in cents.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from src.config import settings


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String, primary_key=True)
    institution: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # checking / savings / credit_card
    balance_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String, default="BRL")
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    merchant: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, default="Other")
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    already_notified: Mapped[bool] = mapped_column(Boolean, default=False)


class Investment(Base):
    __tablename__ = "investments"

    asset_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_value_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_change_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)


# ── Engine & session factory ─────────────────────────────────────────────────

_db_url = settings.database_url
if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite+aiosqlite"):
    _db_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine: AsyncEngine = create_async_engine(_db_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
