"""
Tests for Open Finance API integration helpers.
Uses unittest.mock to avoid real HTTP calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def mock_client():
    with patch("src.open_finance.accounts.client") as mock:
        yield mock


class TestFetchAccounts:
    @pytest.mark.asyncio
    async def test_returns_accounts_list(self, mock_client):
        mock_client.get = AsyncMock(return_value={
            "data": [
                {
                    "accountId": "acc-1",
                    "institution": "Nubank",
                    "type": "checking",
                    "balance": "1500.75",
                    "currency": "BRL",
                }
            ]
        })
        from src.open_finance.accounts import fetch_accounts
        result = await fetch_accounts()
        assert result["error"] is False
        assert len(result["data"]) == 1
        assert result["data"][0]["account_id"] == "acc-1"
        assert result["data"][0]["balance_cents"] == 150075

    @pytest.mark.asyncio
    async def test_returns_error_dict_on_exception(self, mock_client):
        mock_client.get = AsyncMock(side_effect=Exception("timeout"))
        from src.open_finance.accounts import fetch_accounts
        result = await fetch_accounts()
        assert result["error"] is True
        assert result["data"] is None
        assert "timeout" in result["message"]


class TestFetchTransactions:
    @pytest.mark.asyncio
    async def test_category_auto_assigned(self):
        with patch("src.open_finance.transactions.client") as mock_client:
            mock_client.get = AsyncMock(return_value={
                "data": [
                    {
                        "transactionId": "tx-1",
                        "accountId": "acc-1",
                        "amount": "-42.90",
                        "description": "iFood pedido",
                        "merchant": None,
                        "timestamp": "2024-01-15T12:00:00",
                    }
                ]
            })
            from src.open_finance.transactions import fetch_transactions
            result = await fetch_transactions(days=1)
            assert result["error"] is False
            tx = result["data"][0]
            assert tx["category"] == "Food & Delivery"
            assert tx["amount_cents"] == -4290

    @pytest.mark.asyncio
    async def test_unknown_merchant_defaults_to_other(self):
        with patch("src.open_finance.transactions.client") as mock_client:
            mock_client.get = AsyncMock(return_value={
                "data": [
                    {
                        "transactionId": "tx-2",
                        "accountId": "acc-1",
                        "amount": "-10.00",
                        "description": "Pagamento desconhecido",
                        "merchant": None,
                        "timestamp": "2024-01-15T12:00:00",
                    }
                ]
            })
            from src.open_finance.transactions import fetch_transactions
            result = await fetch_transactions(days=1)
            assert result["data"][0]["category"] == "Other"


class TestFetchInvestments:
    @pytest.mark.asyncio
    async def test_alert_triggered_on_large_swing(self):
        with patch("src.open_finance.investments.client") as mock_client, \
             patch("src.open_finance.investments.settings") as mock_settings:
            mock_settings.investment_alert_threshold = 3.0
            mock_client.get = AsyncMock(return_value={
                "data": [
                    {
                        "assetId": "inv-1",
                        "ticker": "PETR4",
                        "name": "Petrobras",
                        "quantity": "100",
                        "currentPrice": "38.50",
                        "openPrice": "37.00",
                    }
                ]
            })
            from src.open_finance.investments import fetch_investments
            result = await fetch_investments()
            assert result["error"] is False
            inv = result["data"][0]
            # (38.50 - 37.00) / 37.00 * 100 ≈ 4.05%
            assert inv["alert_triggered"] is True
            assert inv["daily_change_pct"] > 3.0
