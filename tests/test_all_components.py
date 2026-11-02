"""
tests/test_all_components.py
============================
Comprehensive test suite verifying that all UI components, formatters,
tables, charts, and database helpers render without errors under valid,
empty, None, and edge-case inputs.
"""

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st

from utils.formatting import (
    format_currency,
    format_date,
    format_datetime,
    badge_html,
    percentage_color,
    safe_error_message,
)
from components.cards import (
    render_metric_card,
    render_metric_cards_grid,
    render_info_card,
    render_empty_state,
)
from components.charts import (
    render_category_pie_chart,
    render_budget_utilization_chart,
    render_monthly_bar_chart,
    render_monthly_history_chart,
    render_month_end_summary_chart,
)
from components.grocery_table import render_grocery_table
from components.payment_table import render_payment_table
from components.expense_table import render_expense_table
from components.budget_progress import render_budget_progress
from components.notifications import render_notification_banner
from components.auto_sync import setup_auto_sync
from database.database import (
    get_user_all_rooms_grocery_items,
    get_user_all_payments_live,
    get_user_joined_rooms,
    invalidate_rooms_cache,
)


class TestFormatting:
    def test_format_currency_valid(self):
        assert format_currency(1234.56) == "₹1,234.56"
        assert format_currency(0) == "₹0.00"

    def test_format_currency_edge_cases(self):
        assert format_currency(None) == "₹0.00"
        assert format_currency("not_a_number") == "₹0.00"
        assert format_currency("150.50") == "₹150.50"

    def test_format_datetime_valid(self):
        assert "2026" in format_datetime("2026-10-15T14:30:00")

    def test_format_datetime_edge_cases(self):
        assert format_datetime(None) == "—"
        assert format_datetime("") == "—"
        assert format_datetime("invalid_date") == "invalid_date"

    def test_badge_html_all_statuses(self):
        statuses = ["pending", "paid", "awaiting_confirmation", "settled", "purchased", "unavailable", "unknown"]
        for s in statuses:
            badge = badge_html(s)
            assert isinstance(badge, str)
            assert len(badge) > 0

    def test_percentage_color(self):
        assert percentage_color(50.0) == "#6B8F71"
        assert percentage_color(85.0) == "#E3A02E"
        assert percentage_color(110.0) == "#8C1C13"

    def test_safe_error_message(self):
        assert safe_error_message(ValueError("Custom error")) == "Custom error"
        assert "went wrong" in safe_error_message(Exception("psycopg2 internal host leak"))


class TestCards:
    def test_metric_card(self):
        render_metric_card("TEST CARD", "100", sub="subtitle", accent="danger")

    def test_metric_cards_grid(self):
        cards = [
            {"label": "ONE", "value": "1", "sub": "sub1", "accent": "gold"},
            {"label": "TWO", "value": "2", "sub": "sub2", "accent": "danger"},
        ]
        render_metric_cards_grid(cards)

    def test_info_card(self):
        render_info_card(icon="💡", title="Test Title", body="Content string here")

    def test_empty_state(self):
        render_empty_state("🛒", "No items", "Please add some items.")


class TestCharts:
    def test_category_pie_chart_with_data(self):
        expenses = [
            {"category": "Food", "amount": 250.0},
            {"category": "Transport", "amount": 100.0},
        ]
        render_category_pie_chart(expenses)

    def test_category_pie_chart_empty(self):
        render_category_pie_chart([])

    def test_budget_utilization_chart_with_data(self):
        budgets = [{"category": "Food", "monthlyLimit": 500.0}]
        spending = {"Food": 350.0}
        render_budget_utilization_chart(budgets, spending)

    def test_budget_utilization_chart_empty(self):
        render_budget_utilization_chart([], {})

    def test_monthly_bar_chart_empty(self):
        render_monthly_bar_chart([])

    def test_monthly_history_chart_empty(self):
        render_monthly_history_chart([])

    def test_month_end_summary_chart_empty(self):
        render_month_end_summary_chart([])


class TestGroceryTable:
    def test_render_grocery_table_empty(self):
        render_grocery_table([], current_user_id=1)

    def test_render_grocery_table_with_items(self):
        items = [
            {"id": 101, "item_name": "Apples", "quantity": 4, "user_id": 1, "added_by_name": "Alice", "status": "pending"},
            {"id": 102, "item_name": "Milk", "quantity": 2, "user_id": 2, "added_by_name": "Bob", "status": "purchased"},
            {"id": 103, "item_name": "Bread", "quantity": 1, "user_id": None, "added_by_name": None, "status": "unavailable"},
        ]
        render_grocery_table(items, current_user_id=1, on_edit=lambda x: None, on_delete=lambda x: None)


class TestPaymentTable:
    def test_render_payment_table_empty(self):
        render_payment_table([], current_user_id=1)

    def test_render_payment_table_with_all_cases(self):
        payments = [
            {
                "id": 1,
                "payer_user_id": 1,
                "payee_user_id": 2,
                "payer_name": "Alice",
                "payee_name": "Bob",
                "amount": 150.0,
                "payment_status": "pending",
                "created_at": "2026-11-01T10:00:00",
            },
            {
                "id": 2,
                "payer_user_id": 2,
                "payee_user_id": 1,
                "payer_name": "Bob",
                "payee_name": "Alice",
                "amount": None,
                "payment_status": "paid",
                "created_at": None,
            },
            {
                "id": 3,
                "payer_user_id": 3,
                "payee_user_id": 4,
                "amount": "200.50",
                "payment_status": "settled",
            },
        ]
        # Should gracefully accept extra kwargs without throwing TypeError
        render_payment_table(
            payments,
            current_user_id=1,
            on_settle=lambda x: None,
            on_confirm=lambda x: None,
            on_dispute=lambda x: None,
            on_remind=lambda x: None,
            unexpected_arg="should_not_crash",
            key_prefix="test",
        )


class TestExpenseTable:
    def test_render_expense_table_empty(self):
        render_expense_table([], current_user_id=1)

    def test_render_expense_table_with_data(self):
        expenses = [
            {"id": 1, "amount": 50.0, "category": "Food", "expenseDate": "2026-10-15", "description": "Snacks"},
        ]
        render_expense_table(expenses, current_user_id=1, on_delete=lambda x: None)


class TestNotifications:
    def test_render_notification_banner_empty(self):
        render_notification_banner(user_id=1, key_prefix="test")


class TestAutoSync:
    def test_setup_auto_sync_pause(self):
        setup_auto_sync(interval_ms=10000, pause=True)

    def test_setup_auto_sync_active(self):
        setup_auto_sync(interval_ms=10000, pause=False)


class TestDatabaseBatchQueries:
    def test_rooms_cache_invalidation(self):
        invalidate_rooms_cache(user_id=1)
        invalidate_rooms_cache()

    def test_batch_query_fallbacks(self):
        # Empty user IDs should safely return empty lists without hitting DB
        assert get_user_all_rooms_grocery_items(None) == []
        assert get_user_all_payments_live(None) == []
        assert get_user_joined_rooms(None) == []
