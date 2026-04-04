"""Tests for YNAB service data formatting and filtering logic."""

import os
from unittest.mock import MagicMock, patch

import pytest


def _mock_category(
    name, budgeted, activity, balance, deleted=False, hidden=False, goal_type=None
):
    cat = MagicMock()
    cat.name = name
    cat.budgeted = budgeted
    cat.activity = activity
    cat.balance = balance
    cat.deleted = deleted
    cat.hidden = hidden
    cat.goal_type = goal_type
    return cat


def _mock_transaction(
    var_date, payee_name, category_name, amount, memo="", deleted=False, approved=True
):
    txn = MagicMock()
    txn.var_date = var_date
    txn.payee_name = payee_name
    txn.category_name = category_name
    txn.amount = amount
    txn.memo = memo
    txn.deleted = deleted
    txn.approved = approved
    return txn


@pytest.fixture
def ynab_service():
    """Create a YNABService with mocked API client."""
    with patch.dict(
        os.environ, {"YNAB_ACCESS_TOKEN": "fake-token", "YNAB_BUDGET_ID": "test-budget"}
    ):
        with patch("utils.ynab_service.ynab") as mock_ynab:
            # Mock the configuration and API client chain
            mock_ynab.Configuration.return_value = MagicMock()
            mock_ynab.ApiClient.return_value = MagicMock()
            mock_ynab.PlansApi.return_value = MagicMock()
            mock_ynab.TransactionsApi.return_value = MagicMock()
            mock_ynab.MonthsApi.return_value = MagicMock()
            mock_ynab.CategoriesApi.return_value = MagicMock()

            from utils.ynab_service import YNABService

            service = YNABService()
            yield service


class TestGetBudgetSummary:
    def test_calculates_totals(self, ynab_service):
        categories = [
            _mock_category("Groceries", 500_000, -350_000, 150_000),
            _mock_category("Rent", 1_500_000, -1_500_000, 0),
        ]

        mock_month = MagicMock()
        mock_month.to_be_budgeted = 200_000

        mock_budget = MagicMock()
        mock_budget.name = "My Budget"
        mock_budget.months = [mock_month]
        mock_budget.categories = categories
        mock_budget.currency_format = MagicMock(iso_code="USD")

        mock_response = MagicMock()
        mock_response.data.budget = mock_budget
        ynab_service.plans_api.get_plan_by_id.return_value = mock_response

        result = ynab_service.get_budget_summary()

        assert result["budget_name"] == "My Budget"
        assert result["to_be_budgeted"] == 200.0
        assert result["total_budgeted"] == 2000.0  # (500k + 1500k) / 1000
        assert result["total_activity"] == -1850.0
        assert result["currency_format"] == "USD"

    def test_skips_deleted_and_hidden(self, ynab_service):
        categories = [
            _mock_category("Active", 100_000, -50_000, 50_000),
            _mock_category("Deleted", 999_000, -999_000, 0, deleted=True),
            _mock_category("Hidden", 999_000, -999_000, 0, hidden=True),
        ]

        mock_month = MagicMock()
        mock_month.to_be_budgeted = 0
        mock_budget = MagicMock()
        mock_budget.name = "Budget"
        mock_budget.months = [mock_month]
        mock_budget.categories = categories
        mock_budget.currency_format = None

        mock_response = MagicMock()
        mock_response.data.budget = mock_budget
        ynab_service.plans_api.get_plan_by_id.return_value = mock_response

        result = ynab_service.get_budget_summary()
        assert result["total_budgeted"] == 100.0
        assert result["currency_format"] == "USD"  # Default fallback


class TestGetTransactions:
    def test_filters_by_date_range(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-05", "Store", "Groceries", -25_000),
            _mock_transaction("2026-01-15", "Gas", "Transport", -40_000),
            _mock_transaction(
                "2026-02-01", "Store", "Groceries", -30_000
            ),  # Out of range
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01", end_date="2026-01-31"
        )

        assert result["count"] == 2
        assert result["total_amount"] == -65.0

    def test_filters_by_category(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-05", "Store", "Groceries", -25_000),
            _mock_transaction("2026-01-06", "Gas", "Transport", -40_000),
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01",
            end_date="2026-01-31",
            category_name="groceries",  # Case insensitive
        )

        assert result["count"] == 1
        assert result["transactions"][0]["category"] == "Groceries"

    def test_filters_by_payee(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-05", "Whole Foods", "Groceries", -25_000),
            _mock_transaction("2026-01-06", "Shell Gas", "Transport", -40_000),
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01",
            end_date="2026-01-31",
            payee_name="whole",
        )

        assert result["count"] == 1
        assert result["transactions"][0]["payee"] == "Whole Foods"

    def test_skips_deleted(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-05", "Store", "Groceries", -25_000),
            _mock_transaction("2026-01-06", "Deleted", "Other", -10_000, deleted=True),
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01", end_date="2026-01-31"
        )

        assert result["count"] == 1

    def test_converts_milliunits(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-05", "Store", "Groceries", -12_340),
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01", end_date="2026-01-31"
        )

        assert result["transactions"][0]["amount"] == -12.34

    def test_sorts_by_date_descending(self, ynab_service):
        transactions = [
            _mock_transaction("2026-01-01", "A", "Cat", -10_000),
            _mock_transaction("2026-01-15", "B", "Cat", -20_000),
            _mock_transaction("2026-01-10", "C", "Cat", -30_000),
        ]

        mock_response = MagicMock()
        mock_response.data.transactions = transactions
        ynab_service.transactions_api.get_transactions.return_value = mock_response

        result = ynab_service.get_transactions(
            start_date="2026-01-01", end_date="2026-01-31"
        )

        dates = [t["date"] for t in result["transactions"]]
        assert dates == sorted(dates, reverse=True)


class TestGetCategorySpending:
    def test_month_format_normalization(self, ynab_service):
        """Passing YYYY-MM should be normalized to YYYY-MM-01."""
        categories = [_mock_category("Food", 100_000, -50_000, 50_000)]

        mock_month = MagicMock()
        mock_month.categories = categories
        mock_month.to_be_budgeted = 0

        mock_response = MagicMock()
        mock_response.data.month = mock_month
        ynab_service.months_api.get_plan_month.return_value = mock_response

        result = ynab_service.get_category_spending("2026-03")

        assert result["month"] == "2026-03"

    def test_identifies_overspent(self, ynab_service):
        categories = [
            _mock_category("Dining", 200_000, -300_000, -100_000),  # Overspent
            _mock_category("Groceries", 500_000, -400_000, 100_000),  # Fine
        ]

        mock_month = MagicMock()
        mock_month.categories = categories
        mock_month.to_be_budgeted = 0

        mock_response = MagicMock()
        mock_response.data.month = mock_month
        ynab_service.months_api.get_plan_month.return_value = mock_response

        result = ynab_service.get_category_spending("2026-03")

        assert len(result["overspent_categories"]) == 1
        assert result["overspent_categories"][0]["name"] == "Dining"
        assert result["overspent_categories"][0]["overspent_by"] == 100.0
