"""
Tests for Open Finance API integration helpers.
Uses unittest.mock to avoid real HTTP calls.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestFetchAccounts:
    @pytest.mark.asyncio
    async def test_returns_accounts_list(self):
        # Pluggy returns {"results": [...]} with "id", "institution" as object
        with patch("src.open_finance.accounts.client") as mock_client:
            mock_client.get = AsyncMock(return_value={
                "results": [
                    {
                        "id": "acc-1",
                        "institution": {"name": "Nubank"},
                        "subtype": "CHECKING_ACCOUNT",
                        "balance": 1500.75,
                        "currencyCode": "BRL",
                    }
                ]
            })
            from src.open_finance.accounts import fetch_accounts
            result = await fetch_accounts()

        assert result["error"] is False
        assert len(result["data"]) == 1
        assert result["data"][0]["account_id"] == "acc-1"
        assert result["data"][0]["balance_cents"] == 150075
        assert result["data"][0]["institution"] == "Nubank"

    @pytest.mark.asyncio
    async def test_returns_error_dict_on_exception(self):
        with patch("src.open_finance.accounts.client") as mock_client:
            mock_client.get = AsyncMock(side_effect=Exception("timeout"))
            from src.open_finance.accounts import fetch_accounts
            result = await fetch_accounts()

        assert result["error"] is True
        assert result["data"] is None
        assert "timeout" in result["message"]


class TestFetchTransactions:
    @pytest.mark.asyncio
    async def test_category_auto_assigned(self):
        # fetch_transactions makes two calls: /accounts then /transactions per account
        with patch("src.open_finance.transactions.client") as mock_client:
            mock_client.get = AsyncMock(side_effect=[
                # First call: /accounts
                {"results": [{"id": "acc-1"}]},
                # Second call: /transactions for acc-1
                {"results": [{
                    "id": "tx-1",
                    "accountId": "acc-1",
                    "amount": -42.90,
                    "description": "iFood pedido",
                    "merchant": None,
                    "date": "2024-01-15T12:00:00Z",
                }]},
            ])
            from src.open_finance.transactions import fetch_transactions
            result = await fetch_transactions(days=1)

        assert result["error"] is False
        tx = result["data"][0]
        assert tx["category"] == "Food & Delivery"
        assert tx["amount_cents"] == -4290

    @pytest.mark.asyncio
    async def test_unknown_merchant_defaults_to_other(self):
        with patch("src.open_finance.transactions.client") as mock_client:
            mock_client.get = AsyncMock(side_effect=[
                {"results": [{"id": "acc-1"}]},
                {"results": [{
                    "id": "tx-2",
                    "accountId": "acc-1",
                    "amount": -10.00,
                    "description": "Compra aleatória sem categoria",
                    "merchant": None,
                    "date": "2024-01-15T12:00:00Z",
                }]},
            ])
            from src.open_finance.transactions import fetch_transactions
            result = await fetch_transactions(days=1)

        assert result["data"][0]["category"] == "Other"

    @pytest.mark.asyncio
    async def test_returns_error_dict_on_exception(self):
        with patch("src.open_finance.transactions.client") as mock_client:
            mock_client.get = AsyncMock(side_effect=Exception("network error"))
            from src.open_finance.transactions import fetch_transactions
            result = await fetch_transactions(days=1)

        assert result["error"] is True
        assert result["data"] is None


class TestFetchInvestments:
    @pytest.mark.asyncio
    async def test_alert_triggered_on_large_swing(self):
        # lastMonthRate=150 → daily_change_pct = 150/30 = 5.0% > 3.0% threshold
        with patch("src.open_finance.investments.client") as mock_client, \
             patch("src.open_finance.investments.settings") as mock_settings:
            mock_settings.pluggy_item_id = "test-item"
            mock_settings.investment_alert_threshold = 3.0
            mock_client.get = AsyncMock(return_value={
                "results": [{
                    "id": "inv-1",
                    "code": "PETR4",
                    "name": "Petrobras",
                    "quantity": 100,
                    "value": 3850.0,
                    "amount": 3700.0,
                    "lastMonthRate": 150,
                }]
            })
            from src.open_finance.investments import fetch_investments
            result = await fetch_investments()

        assert result["error"] is False
        inv = result["data"][0]
        assert inv["alert_triggered"] is True
        assert inv["daily_change_pct"] > 3.0

    @pytest.mark.asyncio
    async def test_no_alert_below_threshold(self):
        # lastMonthRate=3 → daily_change_pct = 3/30 = 0.1% < 3.0% threshold
        with patch("src.open_finance.investments.client") as mock_client, \
             patch("src.open_finance.investments.settings") as mock_settings:
            mock_settings.pluggy_item_id = "test-item"
            mock_settings.investment_alert_threshold = 3.0
            mock_client.get = AsyncMock(return_value={
                "results": [{
                    "id": "inv-2",
                    "code": "VALE3",
                    "name": "Vale",
                    "quantity": 50,
                    "value": 5000.0,
                    "amount": 4900.0,
                    "lastMonthRate": 3,
                }]
            })
            from src.open_finance.investments import fetch_investments
            result = await fetch_investments()

        assert result["error"] is False
        inv = result["data"][0]
        assert inv["alert_triggered"] is False

    @pytest.mark.asyncio
    async def test_returns_error_dict_on_exception(self):
        with patch("src.open_finance.investments.client") as mock_client, \
             patch("src.open_finance.investments.settings") as mock_settings:
            mock_settings.pluggy_item_id = "test-item"
            mock_settings.investment_alert_threshold = 3.0
            mock_client.get = AsyncMock(side_effect=Exception("api error"))
            from src.open_finance.investments import fetch_investments
            result = await fetch_investments()

        assert result["error"] is True
        assert result["data"] is None
