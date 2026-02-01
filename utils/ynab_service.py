"""YNAB API service for querying budget data."""

import os
from datetime import datetime, timedelta
from typing import Any, Optional

from dotenv import load_dotenv
import ynab

# Load environment variables
load_dotenv()


class YNABService:
    """Service for interacting with YNAB API."""

    def __init__(self):
        """Initialize YNAB API client."""
        self.access_token = os.getenv("YNAB_ACCESS_TOKEN", "")
        self.budget_id = os.getenv("YNAB_BUDGET_ID", "")

        if not self.access_token:
            raise ValueError("YNAB_ACCESS_TOKEN environment variable is required")

        # Configure API client
        configuration = ynab.Configuration(access_token=self.access_token)
        self.api_client = ynab.ApiClient(configuration)

        # Initialize API endpoints
        self.budgets_api = ynab.BudgetsApi(self.api_client)
        self.transactions_api = ynab.TransactionsApi(self.api_client)
        self.months_api = ynab.MonthsApi(self.api_client)
        self.categories_api = ynab.CategoriesApi(self.api_client)

        # Get budget ID if not provided
        if not self.budget_id:
            budgets_response = self.budgets_api.get_budgets()
            if budgets_response.data and budgets_response.data.budgets:
                self.budget_id = budgets_response.data.budgets[0].id
            else:
                raise ValueError("No YNAB budgets found")

    def get_budget_summary(self) -> dict[str, Any]:
        """Get overall budget summary and health status.

        Returns:
            Dictionary containing budget summary with to-be-budgeted amount,
            total budgeted, total activity, and overall budget health.
        """
        budget_response = self.budgets_api.get_budget_by_id(self.budget_id)
        budget_data = budget_response.data.budget

        # Calculate totals from categories
        to_be_budgeted = (
            budget_data.months[0].to_be_budgeted / 1000 if budget_data.months else 0
        )

        total_budgeted = 0
        total_activity = 0
        total_available = 0

        for category_group in budget_data.category_groups or []:
            if category_group.deleted or category_group.hidden:
                continue
            for category in category_group.categories or []:
                if category.deleted or category.hidden:
                    continue
                total_budgeted += category.budgeted / 1000
                total_activity += category.activity / 1000
                total_available += category.balance / 1000

        return {
            "budget_name": budget_data.name,
            "to_be_budgeted": round(to_be_budgeted, 2),
            "total_budgeted": round(total_budgeted, 2),
            "total_activity": round(total_activity, 2),
            "total_available": round(total_available, 2),
            "currency_format": budget_data.currency_format.iso_code
            if budget_data.currency_format
            else "USD",
            "summary": f"Budget '{budget_data.name}' has ${abs(to_be_budgeted):.2f} {'to be budgeted' if to_be_budgeted > 0 else 'overbudgeted'}. "
            f"Total budgeted: ${total_budgeted:.2f}, Total spent: ${abs(total_activity):.2f}, "
            f"Total available: ${total_available:.2f}.",
        }

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_name: Optional[str] = None,
        payee_name: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get transactions filtered by date range, category, or payee.

        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            category_name: Filter by category name (case-insensitive partial match)
            payee_name: Filter by payee name (case-insensitive partial match)
            limit: Maximum number of transactions to return (default 50)

        Returns:
            Dictionary containing matching transactions and summary statistics.
        """
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Get transactions
        transactions_response = self.transactions_api.get_transactions(
            self.budget_id, since_date=start_date
        )

        transactions = transactions_response.data.transactions or []

        # Filter by date range, category, and payee
        filtered_transactions = []
        total_amount = 0

        for txn in transactions:
            # Skip if deleted or before start date or after end date
            if txn.deleted:
                continue
            txn_date = str(txn.date)
            if txn_date < start_date or txn_date > end_date:
                continue

            # Filter by category if specified
            if category_name and txn.category_name:
                if category_name.lower() not in txn.category_name.lower():
                    continue

            # Filter by payee if specified
            if payee_name and txn.payee_name:
                if payee_name.lower() not in txn.payee_name.lower():
                    continue

            amount = txn.amount / 1000  # Convert milliunits to dollars
            filtered_transactions.append(
                {
                    "date": txn_date,
                    "payee": txn.payee_name,
                    "category": txn.category_name,
                    "memo": txn.memo,
                    "amount": round(amount, 2),
                    "approved": txn.approved,
                }
            )
            total_amount += amount

        # Sort by date (most recent first) and limit
        filtered_transactions.sort(key=lambda x: x["date"], reverse=True)
        filtered_transactions = filtered_transactions[:limit]

        return {
            "transactions": filtered_transactions,
            "count": len(filtered_transactions),
            "total_amount": round(total_amount, 2),
            "start_date": start_date,
            "end_date": end_date,
            "filters": {"category": category_name, "payee": payee_name},
        }

    def get_category_spending(self, month: Optional[str] = None) -> dict[str, Any]:
        """Get spending breakdown by category for a specific month.

        Args:
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            Dictionary containing spending by category and summary.
        """
        if not month:
            month = datetime.now().strftime("%Y-%m-01")
        else:
            # Ensure format is YYYY-MM-01
            if len(month) == 7:  # YYYY-MM
                month = f"{month}-01"

        # Get budget month
        month_response = self.months_api.get_budget_month(self.budget_id, month)

        month_data = month_response.data.month

        categories_spending = []
        total_budgeted = 0
        total_activity = 0
        total_available = 0
        overspent_categories = []

        for category in month_data.categories or []:
            if category.deleted or category.hidden:
                continue

            budgeted = category.budgeted / 1000
            activity = category.activity / 1000
            available = category.balance / 1000

            total_budgeted += budgeted
            total_activity += activity
            total_available += available

            # Track overspent categories
            if available < 0:
                overspent_categories.append(
                    {
                        "name": category.name,
                        "budgeted": round(budgeted, 2),
                        "spent": round(abs(activity), 2),
                        "overspent_by": round(abs(available), 2),
                    }
                )

            # Only include categories with activity
            if activity != 0:
                categories_spending.append(
                    {
                        "category": category.name,
                        "budgeted": round(budgeted, 2),
                        "activity": round(activity, 2),
                        "available": round(available, 2),
                        "goal_type": category.goal_type
                        if hasattr(category, "goal_type")
                        else None,
                    }
                )

        # Sort by absolute activity (highest spending first)
        categories_spending.sort(key=lambda x: abs(x["activity"]), reverse=True)

        return {
            "month": month[:7],  # Return YYYY-MM format
            "categories": categories_spending,
            "total_budgeted": round(total_budgeted, 2),
            "total_spent": round(abs(total_activity), 2),
            "total_available": round(total_available, 2),
            "overspent_categories": overspent_categories,
            "to_be_budgeted": round(month_data.to_be_budgeted / 1000, 2)
            if month_data.to_be_budgeted
            else 0,
        }

    def get_spending_insights(self, months_back: int = 3) -> dict[str, Any]:
        """Generate insights about spending patterns and budget health.

        Args:
            months_back: Number of months to analyze (default 3)

        Returns:
            Dictionary containing spending insights, trends, and recommendations.
        """
        current_month = datetime.now()
        monthly_data = []

        # Collect data for the last N months
        for i in range(months_back):
            month_date = current_month - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m-01")

            try:
                month_spending = self.get_category_spending(month_str)
                monthly_data.append(
                    {
                        "month": month_str[:7],
                        "total_spent": month_spending["total_spent"],
                        "total_budgeted": month_spending["total_budgeted"],
                        "overspent_categories": month_spending["overspent_categories"],
                    }
                )
            except Exception:
                # Skip months that don't have data yet
                continue

        if not monthly_data:
            return {"error": "No spending data available for analysis"}

        # Calculate average spending
        avg_spending = sum(m["total_spent"] for m in monthly_data) / len(monthly_data)
        current_spending = monthly_data[0]["total_spent"] if monthly_data else 0

        # Identify spending trend
        if len(monthly_data) >= 2:
            recent_avg = sum(m["total_spent"] for m in monthly_data[:2]) / 2
            older_avg = sum(m["total_spent"] for m in monthly_data[1:]) / (
                len(monthly_data) - 1
            )
            trend = (
                "increasing"
                if recent_avg > older_avg * 1.1
                else "decreasing"
                if recent_avg < older_avg * 0.9
                else "stable"
            )
        else:
            trend = "insufficient data"

        # Find frequently overspent categories
        overspent_frequency = {}
        for month in monthly_data:
            for cat in month["overspent_categories"]:
                cat_name = cat["name"]
                if cat_name not in overspent_frequency:
                    overspent_frequency[cat_name] = 0
                overspent_frequency[cat_name] += 1

        frequently_overspent = [
            {"category": cat, "months_overspent": count}
            for cat, count in overspent_frequency.items()
            if count > 1
        ]
        frequently_overspent.sort(key=lambda x: x["months_overspent"], reverse=True)

        # Generate recommendations
        recommendations = []
        if current_spending > avg_spending * 1.2:
            recommendations.append(
                f"Current month spending (${current_spending:.2f}) is significantly higher than your {months_back}-month average (${avg_spending:.2f})"
            )

        if frequently_overspent:
            top_overspent = frequently_overspent[0]
            recommendations.append(
                f"'{top_overspent['category']}' has been overspent in {top_overspent['months_overspent']} of the last {months_back} months"
            )

        if trend == "increasing":
            recommendations.append(
                "Your spending trend is increasing. Consider reviewing your budget allocations."
            )

        return {
            "analysis_period": f"Last {months_back} months",
            "average_monthly_spending": round(avg_spending, 2),
            "current_month_spending": round(current_spending, 2),
            "spending_trend": trend,
            "frequently_overspent_categories": frequently_overspent,
            "recommendations": recommendations,
            "monthly_breakdown": monthly_data,
        }
