"""
test_moneyy.py - Comprehensive Unit Tests for MONEYY
Tests database persistence, transaction calculations, budgets, goals, insights, and afford engine.
"""

import unittest
import os
import tempfile
from datetime import date
import database as db
import finance_engine as fe


class TestMoneyy(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for isolation
        self.temp_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        db.init_db(self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_database_init(self):
        """Verifies tables are created properly."""
        txns = db.get_transactions(db_path=self.temp_db_path)
        budgets = db.get_budgets(db_path=self.temp_db_path)
        goals = db.get_savings_goals(db_path=self.temp_db_path)
        self.assertEqual(len(txns), 0)
        self.assertEqual(len(budgets), 0)
        self.assertEqual(len(goals), 0)

    def test_add_and_get_transactions(self):
        """Tests inserting transactions and fetching them."""
        t1_id = db.add_transaction(
            trans_type="Income",
            amount=10000.0,
            category="Allowance",
            description="Monthly pocket money",
            trans_date="2026-09-01",
            payment_method="Bank Transfer",
            note="Parent transfer",
            db_path=self.temp_db_path,
        )
        self.assertGreater(t1_id, 0)

        t2_id = db.add_transaction(
            trans_type="Expense",
            amount=2500.0,
            category="Food",
            description="Mess and snacks",
            trans_date="2026-09-03",
            payment_method="UPI",
            note="",
            db_path=self.temp_db_path,
        )
        self.assertGreater(t2_id, 0)

        txns = db.get_transactions(db_path=self.temp_db_path)
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0]["description"], "Mess and snacks")  # Ordered DESC by date

    def test_update_and_delete_transaction(self):
        """Tests modifying and deleting a transaction."""
        t_id = db.add_transaction(
            trans_type="Expense",
            amount=500.0,
            category="Transport",
            description="Cab fare",
            trans_date="2026-09-05",
            payment_method="Cash",
            db_path=self.temp_db_path,
        )

        # Update
        updated = db.update_transaction(
            trans_id=t_id,
            trans_type="Expense",
            amount=650.0,
            category="Transport",
            description="Cab fare + toll",
            trans_date="2026-09-05",
            payment_method="UPI",
            note="Night fare",
            db_path=self.temp_db_path,
        )
        self.assertTrue(updated)
        t = db.get_transaction(t_id, db_path=self.temp_db_path)
        self.assertEqual(t["amount"], 650.0)
        self.assertEqual(t["payment_method"], "UPI")

        # Delete
        deleted = db.delete_transaction(t_id, db_path=self.temp_db_path)
        self.assertTrue(deleted)
        self.assertIsNone(db.get_transaction(t_id, db_path=self.temp_db_path))

    def test_filter_and_search_transactions(self):
        """Tests filtering by type, category, month, and search query."""
        db.add_transaction("Income", 15000, "Allowance", "Allowance", "2026-09-01", "Bank Transfer", db_path=self.temp_db_path)
        db.add_transaction("Expense", 800, "Food", "Campus burger", "2026-09-02", "UPI", db_path=self.temp_db_path)
        db.add_transaction("Expense", 1200, "Shopping", "Winter jacket", "2026-09-03", "Credit Card", db_path=self.temp_db_path)
        db.add_transaction("Expense", 400, "Food", "College canteen lunch", "2026-08-25", "UPI", db_path=self.temp_db_path)

        # Filter by type
        income_txns = db.get_transactions(trans_type="Income", db_path=self.temp_db_path)
        self.assertEqual(len(income_txns), 1)

        # Filter by category
        food_txns = db.get_transactions(category="Food", db_path=self.temp_db_path)
        self.assertEqual(len(food_txns), 2)

        # Filter by month
        sep_txns = db.get_transactions(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(len(sep_txns), 3)

        # Search
        burger_search = db.get_transactions(search="burger", db_path=self.temp_db_path)
        self.assertEqual(len(burger_search), 1)
        self.assertEqual(burger_search[0]["category"], "Food")

    def test_dashboard_summary_calculations(self):
        """Verifies balance, income, expense, savings, and savings % calculations."""
        db.add_transaction("Income", 20000, "Salary/Stipend", "Internship stipend", "2026-09-01", "Bank Transfer", db_path=self.temp_db_path)
        db.add_transaction("Expense", 4000, "Food", "Mess bill", "2026-09-02", "UPI", db_path=self.temp_db_path)
        db.add_transaction("Expense", 2000, "Transport", "Metro smart card", "2026-09-04", "UPI", db_path=self.temp_db_path)

        summary = fe.calculate_dashboard_summary(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(summary["current_balance"], 14000.0)
        self.assertEqual(summary["monthly_income"], 20000.0)
        self.assertEqual(summary["monthly_expenses"], 6000.0)
        self.assertEqual(summary["monthly_savings"], 14000.0)
        self.assertEqual(summary["savings_percentage"], 70.0)
        self.assertEqual(len(summary["spending_breakdown"]), 2)
        self.assertEqual(summary["spending_breakdown"][0]["category"], "Food")
        self.assertEqual(summary["spending_breakdown"][0]["percentage"], 66.7)

    def test_empty_dashboard_handling(self):
        """Verifies zero values are safely handled without ZeroDivisionError."""
        summary = fe.calculate_dashboard_summary(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(summary["current_balance"], 0.0)
        self.assertEqual(summary["monthly_income"], 0.0)
        self.assertEqual(summary["monthly_expenses"], 0.0)
        self.assertEqual(summary["monthly_savings"], 0.0)
        self.assertEqual(summary["savings_percentage"], 0.0)
        self.assertEqual(len(summary["spending_breakdown"]), 0)
        self.assertEqual(summary["quick_insight"]["type"], "neutral")

    def test_budget_calculations_and_warnings(self):
        """Tests budget remaining, percentage, and warning thresholds."""
        db.set_budget("Overall", 5000.0, db_path=self.temp_db_path)
        db.set_budget("Food", 2000.0, db_path=self.temp_db_path)

        # 1. Healthy spending (Food 1000 of 2000 -> 50%)
        db.add_transaction("Expense", 1000.0, "Food", "Groceries", "2026-09-02", "UPI", db_path=self.temp_db_path)
        b_status = fe.calculate_budgets_status(month="2026-09", db_path=self.temp_db_path)
        food_b = next(b for b in b_status["category_budgets"] if b["category"] == "Food")
        self.assertEqual(food_b["percentage"], 50.0)
        self.assertEqual(food_b["status"], "healthy")

        # 2. Warning spending (Add 700 -> Food = 1700 / 2000 = 85%)
        db.add_transaction("Expense", 700.0, "Food", "Dinner", "2026-09-05", "UPI", db_path=self.temp_db_path)
        b_status = fe.calculate_budgets_status(month="2026-09", db_path=self.temp_db_path)
        food_b = next(b for b in b_status["category_budgets"] if b["category"] == "Food")
        self.assertEqual(food_b["percentage"], 85.0)
        self.assertEqual(food_b["status"], "warning")

        # 3. Exceeded spending (Add 500 -> Food = 2200 / 2000 = 110%)
        db.add_transaction("Expense", 500.0, "Food", "Snacks", "2026-09-07", "UPI", db_path=self.temp_db_path)
        b_status = fe.calculate_budgets_status(month="2026-09", db_path=self.temp_db_path)
        food_b = next(b for b in b_status["category_budgets"] if b["category"] == "Food")
        self.assertEqual(food_b["percentage"], 110.0)
        self.assertEqual(food_b["status"], "exceeded")
        self.assertLess(food_b["remaining"], 0)

    def test_savings_goals_and_eta(self):
        """Tests savings goal tracking, progress %, remaining, and time estimation."""
        g_id = db.add_savings_goal(
            name="New Laptop",
            target_amount=60000.0,
            saved_amount=15000.0,
            category_type="Laptop",
            db_path=self.temp_db_path,
        )

        # Add monthly savings to database: Income 15000, Expense 5000 => Savings 10000/mo
        db.add_transaction("Income", 15000, "Allowance", "Pocket money", "2026-09-01", "Bank Transfer", db_path=self.temp_db_path)
        db.add_transaction("Expense", 5000, "Food", "Expenses", "2026-09-02", "UPI", db_path=self.temp_db_path)

        goals = fe.calculate_savings_goals_summary(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(len(goals), 1)
        g = goals[0]
        self.assertEqual(g["target_amount"], 60000.0)
        self.assertEqual(g["saved_amount"], 15000.0)
        self.assertEqual(g["remaining"], 45000.0)
        self.assertEqual(g["progress_pct"], 25.0)
        # Remaining 45,000 / 10,000 monthly savings = 5 months
        self.assertIn("5 months", g["estimated_time"])

        # Test deposit to goal
        db.deposit_to_savings_goal(g_id, 5000.0, db_path=self.temp_db_path)
        goals_after = fe.calculate_savings_goals_summary(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(goals_after[0]["saved_amount"], 20000.0)
        self.assertEqual(goals_after[0]["remaining"], 40000.0)

    def test_deep_insights(self):
        """Verifies insights: biggest expense, daily avg, comparison with prev month, highest day."""
        # Previous month: 2026-08
        db.add_transaction("Expense", 4000, "Food", "Mess", "2026-08-10", "UPI", db_path=self.temp_db_path)

        # Current month: 2026-09
        db.add_transaction("Income", 10000, "Allowance", "Allowance", "2026-09-01", "Bank Transfer", db_path=self.temp_db_path)
        db.add_transaction("Expense", 1500, "Food", "Groceries", "2026-09-03", "UPI", db_path=self.temp_db_path)
        db.add_transaction("Expense", 2500, "Shopping", "Course books", "2026-09-05", "Debit Card", db_path=self.temp_db_path)

        insights = fe.calculate_deep_insights(month="2026-09", db_path=self.temp_db_path)
        self.assertEqual(insights["biggest_expense"]["category"], "Shopping")
        self.assertEqual(insights["biggest_expense"]["amount"], 2500.0)
        self.assertEqual(insights["savings_rate"], 60.0)  # (10000 - 4000) / 10000 = 60%
        self.assertEqual(insights["highest_spending_day"]["date"], "2026-09-05")
        self.assertEqual(insights["highest_spending_day"]["amount"], 2500.0)
        # Prev expenses was 4000, curr is 4000 -> difference is 0
        self.assertEqual(insights["month_comparison"]["difference"], 0.0)

    def test_affordability_verdicts(self):
        """Tests 'Looks Good', 'Think Twice', and 'Not Recommended' logic."""
        # Current balance = 10,000
        # 1. Looks Good (<= 50% and leaves > 1000) -> 2,000 purchase
        res1 = fe.evaluate_affordability("Headphones", 2000.0, current_balance=10000.0)
        self.assertEqual(res1["verdict"], "Looks Good")
        self.assertEqual(res1["remaining_balance"], 8000.0)

        # 2. Think Twice (> 50% or leaves < 1000) -> 6,000 purchase
        res2 = fe.evaluate_affordability("Smartwatch", 6000.0, current_balance=10000.0)
        self.assertEqual(res2["verdict"], "Think Twice")
        self.assertEqual(res2["remaining_balance"], 4000.0)

        # 3. Not Recommended (exceeds balance) -> 15,000 purchase
        res3 = fe.evaluate_affordability("Gaming Console", 15000.0, current_balance=10000.0)
        self.assertEqual(res3["verdict"], "Not Recommended")
        self.assertEqual(res3["remaining_balance"], -5000.0)

    def test_demo_seed_data(self):
        """Tests that demo data seeds properly and clear_all_data functions."""
        db.seed_demo_data(db_path=self.temp_db_path, force=True)
        txns = db.get_transactions(db_path=self.temp_db_path)
        budgets = db.get_budgets(db_path=self.temp_db_path)
        goals = db.get_savings_goals(db_path=self.temp_db_path)

        self.assertGreater(len(txns), 0)
        self.assertGreater(len(budgets), 0)
        self.assertGreater(len(goals), 0)

        db.clear_all_data(db_path=self.temp_db_path)
        self.assertEqual(len(db.get_transactions(db_path=self.temp_db_path)), 0)


if __name__ == "__main__":
    unittest.main()
