"""
CRUD helpers for the local SQLite database.
All functions are async and accept an AsyncSession.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Account, Investment, Transaction

logger = logging.getLogger(__name__)


# ── Accounts ─────────────────────────────────────────────────────────────────

async def upsert_account(session: AsyncSession, data: dict) -> Account:
    result = await session.get(Account, data["account_id"])
    if result is None:
        result = Account(**data)
        session.add(result)
    else:
        for key, value in data.items():
            setattr(result, key, value)
    await session.commit()
    await session.refresh(result)
    return result


async def get_all_accounts(session: AsyncSession) -> list[Account]:
    result = await session.execute(select(Account))
    return list(result.scalars().all())


# ── Transactions ─────────────────────────────────────────────────────────────

async def transaction_exists(session: AsyncSession, transaction_id: str) -> bool:
    result = await session.get(Transaction, transaction_id)
    return result is not None


async def insert_transaction(session: AsyncSession, data: dict) -> Transaction | None:
    if await transaction_exists(session, data["transaction_id"]):
        logger.debug("Transaction %s already exists, skipping.", data["transaction_id"])
        return None
    tx = Transaction(**data)
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


async def mark_transaction_notified(session: AsyncSession, transaction_id: str) -> None:
    tx = await session.get(Transaction, transaction_id)
    if tx:
        tx.already_notified = True
        await session.commit()


async def get_unnotified_transactions(session: AsyncSession) -> list[Transaction]:
    result = await session.execute(
        select(Transaction).where(Transaction.already_notified.is_(False))
    )
    return list(result.scalars().all())


async def get_transactions_since(session: AsyncSession, since: datetime) -> list[Transaction]:
    result = await session.execute(
        select(Transaction).where(Transaction.timestamp >= since).order_by(Transaction.timestamp.desc())
    )
    return list(result.scalars().all())


# ── Investments ───────────────────────────────────────────────────────────────

async def upsert_investment(session: AsyncSession, data: dict) -> Investment:
    result = await session.get(Investment, data["asset_id"])
    if result is None:
        result = Investment(**data)
        session.add(result)
    else:
        for key, value in data.items():
            setattr(result, key, value)
    await session.commit()
    await session.refresh(result)
    return result


async def get_all_investments(session: AsyncSession) -> list[Investment]:
    result = await session.execute(select(Investment))
    return list(result.scalars().all())


async def get_investments_with_alert(session: AsyncSession) -> list[Investment]:
    result = await session.execute(
        select(Investment).where(Investment.alert_triggered.is_(True))
    )
    return list(result.scalars().all())


async def clear_investment_alerts(session: AsyncSession) -> None:
    investments = await get_investments_with_alert(session)
    for inv in investments:
        inv.alert_triggered = False
    await session.commit()
