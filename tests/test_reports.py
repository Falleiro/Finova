"""
Tests for daily and monthly report builders.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


class TestDailySummary:
    @pytest.mark.asyncio
    async def test_builds_message_with_balances(self):
        mock_account = MagicMock()
        mock_account.balance_cents = 250000
        mock_account.institution = "Nubank"
        mock_account.type = "checking"

        mock_tx = MagicMock()
        mock_tx.amount_cents = -5000
        mock_tx.category = "Food & Delivery"
        mock_tx.timestamp = datetime.now(tz=timezone.utc)

        with patch("src.reports.daily.fetch_accounts", AsyncMock(return_value={"error": True, "data": None})), \
             patch("src.reports.daily.fetch_transactions", AsyncMock(return_value={"error": True, "data": None})), \
             patch("src.reports.daily.get_all_accounts", AsyncMock(return_value=[mock_account])), \
             patch("src.reports.daily.get_transactions_since", AsyncMock(return_value=[mock_tx])), \
             patch("src.reports.daily.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from src.reports.daily import build_daily_summary
            message = await build_daily_summary()

        assert "Resumo" in message
        assert "R$" in message or "2.500" in message


class TestMonthlyReport:
    @pytest.mark.asyncio
    async def test_returns_tuple_message_and_chart(self):
        mock_tx = MagicMock()
        mock_tx.amount_cents = -10000
        mock_tx.category = "Supermarket"

        with patch("src.reports.monthly.fetch_transactions", AsyncMock(return_value={"error": True, "data": None})), \
             patch("src.reports.monthly.get_transactions_since", AsyncMock(return_value=[mock_tx])), \
             patch("src.reports.monthly.build_spending_chart", AsyncMock(return_value="/tmp/finova_charts/test.png")), \
             patch("src.reports.monthly.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from src.reports.monthly import build_monthly_report
            message, chart = await build_monthly_report()

        assert isinstance(message, str)
        assert "Relatório Mensal" in message


class TestFormatter:
    def test_fmt_brl_positive(self):
        from src.telegram.formatter import fmt_brl
        assert fmt_brl(100000) == "R$ 1.000,00"

    def test_fmt_brl_zero(self):
        from src.telegram.formatter import fmt_brl
        assert fmt_brl(0) == "R$ 0,00"

    def test_fmt_pct_positive(self):
        from src.telegram.formatter import fmt_pct
        assert fmt_pct(3.45) == "+3.45%"

    def test_fmt_pct_negative(self):
        from src.telegram.formatter import fmt_pct
        assert fmt_pct(-1.2) == "-1.20%"
