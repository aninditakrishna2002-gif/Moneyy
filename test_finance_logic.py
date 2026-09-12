"""
test_finance_logic.py - Unit tests for MONEYY calculations
"""

import unittest
from finance_logic import calculate_finances, check_affordability, calculate_savings_goal


class TestFinanceLogic(unittest.TestCase):
    def test_zero_values(self):
        result = calculate_finances()
        self.assertEqual(result["total_income"], 0.0)
        self.assertEqual(result["total_spending"], 0.0)
        self.assertEqual(result["money_left"], 0.0)
        self.assertEqual(result["savings_rate"], 0.0)
        self.assertEqual(result["status"], "Needs Attention")

    def test_healthy_student_budget(self):
        # Income = 10,000 allowance + 5,000 part time = 15,000
        # Expenses = 4,000 food + 1,000 transport + 1,500 education + 1,000 entertainment = 7,500
        # Left = 7,500. Savings rate = 50.0%
        result = calculate_finances(
            allowance=10000,
            part_time=5000,
            food=4000,
            transport=1000,
            education=1500,
            entertainment=1000,
        )
        self.assertEqual(result["total_income"], 15000.0)
        self.assertEqual(result["total_spending"], 7500.0)
        self.assertEqual(result["money_left"], 7500.0)
        self.assertEqual(result["savings_rate"], 50.0)
        self.assertEqual(result["status"], "Good")
        self.assertEqual(result["biggest_expense"]["category"], "Food")
        self.assertEqual(result["biggest_expense"]["amount"], 4000.0)

    def test_deficit_budget(self):
        # Income = 5,000, Spending = 8,000
        result = calculate_finances(
            allowance=5000,
            food=4000,
            shopping=4000,
        )
        self.assertEqual(result["total_income"], 5000.0)
        self.assertEqual(result["total_spending"], 8000.0)
        self.assertEqual(result["money_left"], -3000.0)
        self.assertTrue(result["savings_rate"] < 0)
        self.assertEqual(result["status"], "Needs Attention")
        self.assertIn("in the red", result["tip"])

    def test_affordability_not_recommended(self):
        # Price > available cash
        afford = check_affordability(
            item_name="PlayStation 5",
            price=50000,
            current_savings=15000,
            monthly_savings=3000,
        )
        self.assertEqual(afford["recommendation"], "Not Recommended")
        self.assertEqual(afford["badge_type"], "danger")
        self.assertIn("short by", afford["reasoning"])
        self.assertEqual(afford["remaining_after_purchase"], -35000.0)

    def test_affordability_think_twice(self):
        # Price is affordable outright, but wipes out 80% of cash
        afford = check_affordability(
            item_name="Concert Ticket",
            price=8000,
            current_savings=10000,
            monthly_savings=1000,
        )
        self.assertEqual(afford["recommendation"], "Think Twice")
        self.assertEqual(afford["badge_type"], "warning")
        self.assertEqual(afford["remaining_after_purchase"], 2000.0)

    def test_affordability_yes(self):
        # Small purchase with plenty cushion
        afford = check_affordability(
            item_name="Textbook",
            price=1200,
            current_savings=20000,
            monthly_savings=3000,
        )
        self.assertEqual(afford["recommendation"], "Yes")
        self.assertEqual(afford["badge_type"], "success")
        self.assertEqual(afford["remaining_after_purchase"], 18800.0)

    def test_savings_goal_progress(self):
        # Target 50,000, saved 20,000 (40%), monthly 5,000 -> 6 months remaining
        goal = calculate_savings_goal(
            goal_name="MacBook Fund",
            target_amount=50000,
            current_saved=20000,
            monthly_contribution=5000,
        )
        self.assertEqual(goal["progress_percentage"], 40.0)
        self.assertEqual(goal["remaining_amount"], 30000.0)
        self.assertEqual(goal["estimated_months"], 6)
        self.assertFalse(goal["is_achieved"])

    def test_savings_goal_achieved(self):
        goal = calculate_savings_goal(
            goal_name="Gym Membership",
            target_amount=6000,
            current_saved=6500,
            monthly_contribution=1000,
        )
        self.assertEqual(goal["progress_percentage"], 100.0)
        self.assertEqual(goal["remaining_amount"], 0.0)
        self.assertEqual(goal["estimated_months"], 0)
        self.assertTrue(goal["is_achieved"])


if __name__ == "__main__":
    unittest.main()
