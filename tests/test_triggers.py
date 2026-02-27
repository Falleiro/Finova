"""
Tests for transaction and investment watchers, plus intent classifier.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestIntentClassifier:
    def test_saldo_intent(self):
        from src.agents.intent_classifier import classify_intent
        assert classify_intent("qual meu saldo?") == "saldo"

    def test_extrato_intent(self):
        from src.agents.intent_classifier import classify_intent
        assert classify_intent("me mostra o extrato") == "extrato"

    def test_carteira_intent(self):
        from src.agents.intent_classifier import classify_intent
        assert classify_intent("como está minha carteira de investimentos?") == "carteira"

    def test_unknown_falls_back_to_ajuda(self):
        from src.agents.intent_classifier import classify_intent
        assert classify_intent("bom dia!") == "ajuda"


class TestTransactionWatcher:
    @pytest.mark.asyncio
    async def test_alert_sent_for_large_transaction(self):
        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        mock_tx = MagicMock()
        mock_tx.amount_cents = -50000  # R$ 500 — above R$200 threshold
        mock_tx.transaction_id = "tx-large"

        with patch("src.triggers.transaction_watcher.fetch_transactions", AsyncMock(return_value={
            "error": False,
            "data": [{"transaction_id": "tx-large", "account_id": "acc-1",
                       "amount_cents": -50000, "description": "test", "merchant": None,
                       "category": "Other", "timestamp": __import__("datetime").datetime.now(),
                       "already_notified": False}]
        })), \
        patch("src.triggers.transaction_watcher.insert_transaction", AsyncMock(return_value=mock_tx)), \
        patch("src.triggers.transaction_watcher.mark_transaction_notified", AsyncMock()), \
        patch("src.triggers.transaction_watcher.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from src.triggers.transaction_watcher import TransactionWatcher
            watcher = TransactionWatcher(mock_app)
            await watcher._poll()

        mock_app.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_alert_for_small_transaction(self):
        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        mock_tx = MagicMock()
        mock_tx.amount_cents = -500  # R$ 5 — below threshold
        mock_tx.transaction_id = "tx-small"

        with patch("src.triggers.transaction_watcher.fetch_transactions", AsyncMock(return_value={
            "error": False,
            "data": [{"transaction_id": "tx-small", "account_id": "acc-1",
                       "amount_cents": -500, "description": "coffee", "merchant": None,
                       "category": "Other", "timestamp": __import__("datetime").datetime.now(),
                       "already_notified": False}]
        })), \
        patch("src.triggers.transaction_watcher.insert_transaction", AsyncMock(return_value=mock_tx)), \
        patch("src.triggers.transaction_watcher.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from src.triggers.transaction_watcher import TransactionWatcher
            watcher = TransactionWatcher(mock_app)
            await watcher._poll()

        mock_app.bot.send_message.assert_not_called()


class TestInvestmentWatcher:
    @pytest.mark.asyncio
    async def test_alert_sent_on_swing(self):
        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        mock_inv = MagicMock()
        mock_inv.alert_triggered = True
        mock_inv.ticker = "PETR4"
        mock_inv.daily_change_pct = 4.5

        with patch("src.triggers.investment_watcher.fetch_investments", AsyncMock(return_value={
            "error": False,
            "data": [{}]  # raw data doesn't matter; upsert is mocked
        })), \
        patch("src.triggers.investment_watcher.upsert_investment", AsyncMock(return_value=mock_inv)), \
        patch("src.triggers.investment_watcher.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from src.triggers.investment_watcher import InvestmentWatcher
            watcher = InvestmentWatcher(mock_app)
            await watcher._poll()

        mock_app.bot.send_message.assert_called_once()
