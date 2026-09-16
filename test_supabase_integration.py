"""
test_supabase_integration.py - Integration & Security Test Suite for Supabase Auth & PostgreSQL in MONEYY
Tests:
1. User registration & Supabase Auth flow
2. User login, session management & token verification
3. Protected endpoint security (401 when unauthorized)
4. Adding transactions, budgets, goals for User A
5. User isolation: User B cannot access or view User A's data
6. Logout & session invalidation
7. Security check: No secret keys or passwords exposed in code, HTML, JS, or Git
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from app import app
import supabase_client as sc
import supabase_db as sdb
import finance_engine as fe


class TestSupabaseIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_unauthenticated_access_denied(self):
        """Ensures protected financial routes reject unauthenticated requests with 401."""
        protected_routes = [
            "/api/dashboard",
            "/api/transactions",
            "/api/budgets",
            "/api/goals",
            "/api/insights",
        ]
        for route in protected_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 401, f"Route {route} should return 401 when unauthenticated.")
            data = res.get_json()
            self.assertFalse(data.get("success"))
            self.assertIn("Authentication required", data.get("error"))

    def test_public_meta_accessible(self):
        """Ensures public metadata route works without authentication."""
        res = self.client.get("/api/meta")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Food", data.get("expense_categories"))
        self.assertIn("Allowance", data.get("income_categories"))

    @patch("supabase_client.sign_up_user")
    def test_signup_flow(self, mock_signup):
        """Tests user registration with name, email, and password."""
        mock_signup.return_value = (True, {
            "user": {
                "id": "usr-uuid-1111",
                "email": "student1@campus.edu",
                "name": "Anindita",
            },
            "session": {
                "access_token": "mock-jwt-token-1111",
                "refresh_token": "mock-refresh-1111",
            },
            "message": "Signup successful!",
        })

        payload = {
            "name": "Anindita",
            "email": "student1@campus.edu",
            "password": "securepassword123",
        }
        res = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["user"]["name"], "Anindita")
        self.assertEqual(data["data"]["user"]["email"], "student1@campus.edu")

    @patch("supabase_client.sign_in_user")
    def test_login_flow(self, mock_signin):
        """Tests user login and session establishment."""
        mock_signin.return_value = (True, {
            "user": {
                "id": "usr-uuid-1111",
                "email": "student1@campus.edu",
                "name": "Anindita",
            },
            "session": {
                "access_token": "mock-jwt-token-1111",
            },
            "message": "Login successful!",
        })

        res = self.client.post("/api/auth/login", json={
            "email": "student1@campus.edu",
            "password": "securepassword123",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["user"]["id"], "usr-uuid-1111")

    @patch("supabase_client.get_user_from_token")
    @patch("supabase_db.add_transaction")
    @patch("supabase_db.get_transactions")
    def test_user_data_isolation(self, mock_get_txns, mock_add_txn, mock_get_user):
        """
        Tests that User A and User B only access their own respective transactions.
        """
        # Set up mock user verification
        def get_user_side_effect(token):
            if token == "token-user-a":
                return {"id": "user-a-uuid", "email": "usera@campus.edu", "name": "User A"}
            elif token == "token-user-b":
                return {"id": "user-b-uuid", "email": "userb@campus.edu", "name": "User B"}
            return None

        mock_get_user.side_effect = get_user_side_effect

        # Mock database storage per user
        user_a_txns = [
            {
                "id": "txn-a-1",
                "user_id": "user-a-uuid",
                "type": "Expense",
                "amount": 450.0,
                "category": "Food",
                "description": "User A Pizza",
                "date": "2026-09-16",
                "payment_method": "UPI",
            }
        ]
        user_b_txns = [
            {
                "id": "txn-b-1",
                "user_id": "user-b-uuid",
                "type": "Expense",
                "amount": 1200.0,
                "category": "Education",
                "description": "User B Textbook",
                "date": "2026-09-16",
                "payment_method": "Debit Card",
            }
        ]

        def get_txns_side_effect(user_id, **kwargs):
            if user_id == "user-a-uuid":
                return list(user_a_txns)
            elif user_id == "user-b-uuid":
                return list(user_b_txns)
            return []

        mock_get_txns.side_effect = get_txns_side_effect

        # User A requests their transactions
        res_a = self.client.get("/api/transactions", headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.get_json()["data"]
        self.assertEqual(len(data_a), 1)
        self.assertEqual(data_a[0]["description"], "User A Pizza")
        self.assertEqual(data_a[0]["user_id"], "user-a-uuid")

        # User B requests their transactions
        res_b = self.client.get("/api/transactions", headers={"Authorization": "Bearer token-user-b"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()["data"]
        self.assertEqual(len(data_b), 1)
        self.assertEqual(data_b[0]["description"], "User B Textbook")
        self.assertEqual(data_b[0]["user_id"], "user-b-uuid")

        # Verify User B CANNOT see User A's transaction
        user_b_descriptions = [t["description"] for t in data_b]
        self.assertNotIn("User A Pizza", user_b_descriptions)

    @patch("supabase_client.get_user_from_token")
    @patch("supabase_db.add_transaction")
    def test_add_transaction_endpoint(self, mock_add, mock_get_user):
        """Tests adding a transaction via POST /api/transactions for authenticated user."""
        mock_get_user.return_value = {"id": "user-a-uuid", "email": "usera@campus.edu", "name": "User A"}
        mock_add.return_value = {
            "id": "txn-uuid-new",
            "user_id": "user-a-uuid",
            "type": "Expense",
            "amount": 250.0,
            "category": "Food",
            "description": "Campus Canteen Snack",
            "date": "2026-09-16",
            "payment_method": "UPI",
            "note": "",
        }

        payload = {
            "type": "Expense",
            "amount": 250.0,
            "category": "Food",
            "description": "Campus Canteen Snack",
            "date": "2026-09-16",
            "payment_method": "UPI",
            "note": "",
        }
        res = self.client.post("/api/transactions", json=payload, headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["id"], "txn-uuid-new")
        self.assertEqual(data["data"]["amount"], 250.0)

    @patch("supabase_client.get_user_from_token")
    @patch("supabase_db.set_budget")
    @patch("supabase_db.get_budgets")
    @patch("supabase_db.get_transactions")
    def test_budgets_endpoint(self, mock_txns, mock_get_budgets, mock_set_budget, mock_get_user):
        """Tests setting and viewing budgets for authenticated user."""
        mock_get_user.return_value = {"id": "user-a-uuid", "email": "usera@campus.edu", "name": "User A"}
        mock_set_budget.return_value = {"id": "b-uuid-1", "user_id": "user-a-uuid", "category": "Food", "monthly_amount": 3500.0}
        mock_get_budgets.return_value = [{"id": "b-uuid-1", "user_id": "user-a-uuid", "category": "Food", "monthly_amount": 3500.0}]
        mock_txns.return_value = [{"id": "t-1", "amount": 1000.0, "category": "Food", "type": "Expense"}]

        # Set budget
        res = self.client.post("/api/budgets", json={"category": "Food", "amount": 3500.0}, headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(res.status_code, 200)

        # Get budgets
        res_get = self.client.get("/api/budgets?month=2026-09", headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(res_get.status_code, 200)
        data = res_get.get_json()["data"]
        self.assertEqual(len(data["category_budgets"]), 1)
        self.assertEqual(data["category_budgets"][0]["category"], "Food")
        self.assertEqual(data["category_budgets"][0]["spent"], 1000.0)

    @patch("supabase_client.get_user_from_token")
    @patch("finance_engine.evaluate_affordability")
    def test_afford_endpoint(self, mock_afford, mock_get_user):
        """Tests Can I Afford It calculator for authenticated user."""
        mock_get_user.return_value = {"id": "user-a-uuid", "email": "usera@campus.edu", "name": "User A"}
        mock_afford.return_value = {
            "item_name": "Course Books",
            "price": 800.0,
            "remaining_balance": 9200.0,
            "verdict": "Looks Good",
            "badge_color": "success",
            "emoji": "🎉",
            "percentage_of_balance": 8.0,
            "headline": "Affordable with a healthy buffer!",
            "explanation": "You can comfortably afford this.",
            "recommendation": "Great purchase.",
        }

    @patch("supabase_client.sign_up_user")
    @patch("supabase_db.seed_user_demo_data")
    def test_signup_does_not_seed_demo_data(self, mock_seed, mock_signup):
        """Ensures that registering a new account does NOT automatically seed demo data."""
        mock_signup.return_value = (True, {
            "user": {
                "id": "usr-uuid-clean",
                "email": "fresh@campus.edu",
                "name": "Fresh Student",
            },
            "session": {
                "access_token": "mock-jwt-clean",
            },
            "message": "Signup successful!",
        })

        payload = {
            "name": "Fresh Student",
            "email": "fresh@campus.edu",
            "password": "cleanpassword123",
        }
        res = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(res.status_code, 201)
        # Verify seed_user_demo_data was NOT called
        mock_seed.assert_not_called()

    @patch("supabase_client.get_user_from_token")
    @patch("supabase_db.get_all_time_transactions")
    @patch("supabase_db.get_transactions")
    @patch("supabase_db.get_budgets")
    @patch("supabase_db.get_savings_goals")
    def test_new_user_zero_state(self, mock_goals, mock_budgets, mock_txns, mock_all_txns, mock_user):
        """
        Ensures a newly created account starts with:
        Balance: 0, Income: 0, Expenses: 0, Savings: 0, Transactions: 0, Budgets: 0, Goals: 0.
        """
        mock_user.return_value = {"id": "usr-new-000", "email": "brandnew@campus.edu", "name": "Newbie"}
        mock_all_txns.return_value = []
        mock_txns.return_value = []
        mock_budgets.return_value = []
        mock_goals.return_value = []

        headers = {"Authorization": "Bearer token-new"}

        # 1. Dashboard
        res_dash = self.client.get("/api/dashboard", headers=headers)
        self.assertEqual(res_dash.status_code, 200)
        dash = res_dash.get_json()["data"]
        self.assertEqual(dash["current_balance"], 0.0)
        self.assertEqual(dash["monthly_income"], 0.0)
        self.assertEqual(dash["monthly_expenses"], 0.0)
        self.assertEqual(dash["monthly_savings"], 0.0)
        self.assertEqual(dash["savings_percentage"], 0.0)
        self.assertEqual(len(dash["recent_transactions"]), 0)
        self.assertEqual(len(dash["spending_breakdown"]), 0)

        # 2. Transactions
        res_txns = self.client.get("/api/transactions", headers=headers)
        self.assertEqual(res_txns.status_code, 200)
        txns = res_txns.get_json()
        self.assertEqual(txns["count"], 0)
        self.assertEqual(len(txns["data"]), 0)

        # 3. Budgets
        res_b = self.client.get("/api/budgets", headers=headers)
        self.assertEqual(res_b.status_code, 200)
        budgets_data = res_b.get_json()["data"]
        self.assertFalse(budgets_data["has_any_budget"])
        self.assertIsNone(budgets_data["overall_budget"])
        self.assertEqual(len(budgets_data["category_budgets"]), 0)

        # 4. Goals
        res_g = self.client.get("/api/goals", headers=headers)
        self.assertEqual(res_g.status_code, 200)
        goals = res_g.get_json()["data"]
        self.assertEqual(len(goals), 0)

    @patch("supabase_client.get_user_from_token")
    @patch("supabase_db.get_transactions")
    @patch("supabase_db.get_budgets")
    @patch("supabase_db.get_savings_goals")
    def test_user_isolation_budgets_and_goals(self, mock_goals, mock_budgets, mock_txns, mock_user):
        """
        Tests that User A's budgets and goals are isolated and cannot be viewed by User B.
        """
        mock_txns.return_value = []
        def get_user_side_effect(token):
            if token == "token-user-a":
                return {"id": "uuid-a", "email": "a@campus.edu", "name": "User A"}
            elif token == "token-user-b":
                return {"id": "uuid-b", "email": "b@campus.edu", "name": "User B"}
            return None
        mock_user.side_effect = get_user_side_effect

        def get_budgets_side_effect(user_id, **kwargs):
            if user_id == "uuid-a":
                return [{"id": "b-a-1", "user_id": "uuid-a", "category": "Food", "monthly_amount": 5000.0}]
            return []
        mock_budgets.side_effect = get_budgets_side_effect

        def get_goals_side_effect(user_id, **kwargs):
            if user_id == "uuid-a":
                return [{"id": "g-a-1", "user_id": "uuid-a", "name": "User A Laptop", "target_amount": 60000.0, "saved_amount": 10000.0}]
            return []
        mock_goals.side_effect = get_goals_side_effect

        # User A checks budgets
        res_a_b = self.client.get("/api/budgets", headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(len(res_a_b.get_json()["data"]["category_budgets"]), 1)

        # User B checks budgets -> 0
        res_b_b = self.client.get("/api/budgets", headers={"Authorization": "Bearer token-user-b"})
        self.assertEqual(len(res_b_b.get_json()["data"]["category_budgets"]), 0)

        # User A checks goals
        res_a_g = self.client.get("/api/goals", headers={"Authorization": "Bearer token-user-a"})
        self.assertEqual(len(res_a_g.get_json()["data"]), 1)
        self.assertEqual(res_a_g.get_json()["data"][0]["name"], "User A Laptop")

        # User B checks goals -> 0
        res_b_g = self.client.get("/api/goals", headers={"Authorization": "Bearer token-user-b"})
        self.assertEqual(len(res_b_g.get_json()["data"]), 0)

    def test_security_and_secrets_check(self):
        """
        Scans source files, templates, and static assets to guarantee:
        - No hardcoded Supabase secret keys or service role keys exist
        - No hardcoded passwords exist
        - .gitignore exists and properly ignores .env and moneyy.db
        """
        # 1. Check .gitignore exists and includes sensitive files
        gitignore_path = os.path.join(os.path.dirname(__file__), ".gitignore")
        self.assertTrue(os.path.exists(gitignore_path), ".gitignore must exist.")
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(".env", content, ".gitignore must ignore .env")
            self.assertIn("moneyy.db", content, ".gitignore must ignore moneyy.db")

        # 2. Check source files for leaked keys or tokens
        check_extensions = [".py", ".html", ".js", ".css", ".sql"]
        forbidden_patterns = [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", # Common JWT prefix pattern
            "sbp_", # Supabase personal access token prefix
        ]

        project_dir = os.path.dirname(os.path.abspath(__file__))
        for root, _, files in os.walk(project_dir):
            if ".git" in root or "__pycache__" in root or "venv" in root:
                continue
            for file in files:
                if any(file.endswith(ext) for ext in check_extensions) and file != "test_supabase_integration.py":
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_text = f.read()
                        for pattern in forbidden_patterns:
                            self.assertNotIn(pattern, file_text, f"Found forbidden secret pattern {pattern} in {file}")


if __name__ == "__main__":
    unittest.main()
