"""
verify_app.py - Integration Verification of Flask API Endpoints for MONEYY
Runs through all endpoints using Flask's test client.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import app
import database as db


def run_verification():
    print("Testing MONEYY Flask API endpoints...")
    client = app.test_client()

    # 1. Test Home page
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200 for /, got {res.status_code}"
    print("[PASS] GET / returns 200 OK")

    # 2. Test Meta endpoint
    res = client.get("/api/meta")
    assert res.status_code == 200
    meta = res.get_json()
    assert "Food" in meta["expense_categories"]
    assert "Allowance" in meta["income_categories"]
    assert "UPI" in meta["payment_methods"]
    print("[PASS] GET /api/meta returns valid student categories & payment methods")

    # 3. Seed demo data
    res = client.post("/api/demo/seed")
    assert res.status_code == 200
    print("[PASS] POST /api/demo/seed succeeds")

    # 4. Dashboard
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    dash = res.get_json()["data"]
    assert "current_balance" in dash
    assert "monthly_income" in dash
    assert "monthly_expenses" in dash
    assert "monthly_savings" in dash
    assert "savings_percentage" in dash
    assert len(dash["recent_transactions"]) > 0
    print(f"[PASS] GET /api/dashboard: Balance = {dash['current_balance']}, Savings Rate = {dash['savings_percentage']}%")

    # 5. Transactions Listing & Filter
    res = client.get("/api/transactions?type=Expense")
    assert res.status_code == 200
    txns = res.get_json()["data"]
    assert all(t["type"] == "Expense" for t in txns)
    print(f"[PASS] GET /api/transactions?type=Expense returned {len(txns)} transactions")

    # 6. Add Transaction
    new_txn = {
        "type": "Expense",
        "amount": 299.0,
        "category": "Food",
        "description": "Boba tea after class",
        "date": "2026-09-12",
        "payment_method": "UPI",
        "note": "Weekend treat",
    }
    res = client.post("/api/transactions", json=new_txn)
    assert res.status_code == 201
    created = res.get_json()["data"]
    created_id = created["id"]
    assert created["amount"] == 299.0
    print(f"[PASS] POST /api/transactions created txn id={created_id}")

    # 7. Edit Transaction
    update_data = {
        "type": "Expense",
        "amount": 349.0,
        "category": "Food",
        "description": "Boba tea + waffles",
        "date": "2026-09-12",
        "payment_method": "UPI",
        "note": "Extra waffle",
    }
    res = client.put(f"/api/transactions/{created_id}", json=update_data)
    assert res.status_code == 200
    assert res.get_json()["data"]["amount"] == 349.0
    print(f"[PASS] PUT /api/transactions/{created_id} updated amount to 349.0")

    # 8. Delete Transaction
    res = client.delete(f"/api/transactions/{created_id}")
    assert res.status_code == 200
    print(f"[PASS] DELETE /api/transactions/{created_id} successfully deleted")

    # 9. Budgets
    res = client.get("/api/budgets")
    assert res.status_code == 200
    budgets_data = res.get_json()["data"]
    assert "overall_budget" in budgets_data
    assert len(budgets_data["category_budgets"]) > 0
    print(f"[PASS] GET /api/budgets returned {len(budgets_data['category_budgets'])} category budgets")

    # Set new budget
    res = client.post("/api/budgets", json={"category": "Education", "amount": 3000})
    assert res.status_code == 200
    print("[PASS] POST /api/budgets successfully set budget for Education")

    # 10. Savings Goals
    res = client.get("/api/goals")
    assert res.status_code == 200
    goals = res.get_json()["data"]
    assert len(goals) > 0
    first_goal_id = goals[0]["id"]
    print(f"[PASS] GET /api/goals returned {len(goals)} savings goals")

    # Deposit into goal
    res = client.post(f"/api/goals/{first_goal_id}/deposit", json={"amount": 1000})
    assert res.status_code == 200
    print(f"[PASS] POST /api/goals/{first_goal_id}/deposit added 1000")

    # 11. Insights
    res = client.get("/api/insights")
    assert res.status_code == 200
    insights = res.get_json()["data"]
    assert "biggest_expense" in insights
    assert "avg_daily_spending" in insights
    assert "savings_rate" in insights
    assert "month_comparison" in insights
    assert "highest_spending_day" in insights
    assert "student_tips" in insights
    print(f"[PASS] GET /api/insights: Biggest={insights['biggest_expense']['category']}, Daily Avg={insights['avg_daily_spending']}")

    # 12. Can I Afford It?
    res = client.post("/api/afford", json={"item_name": "New Gaming Mouse", "price": 1200, "current_balance": 15000})
    assert res.status_code == 200
    afford_res = res.get_json()["data"]
    assert afford_res["verdict"] == "Looks Good"
    assert afford_res["remaining_balance"] == 13800.0
    print(f"[PASS] POST /api/afford verdict for 1,200 mouse: {afford_res['verdict']}")

    res_tight = client.post("/api/afford", json={"item_name": "GoPro Camera", "price": 12000, "current_balance": 15000})
    assert res_tight.status_code == 200
    assert res_tight.get_json()["data"]["verdict"] == "Think Twice"
    print(f"[PASS] POST /api/afford verdict for 12,000 GoPro: {res_tight.get_json()['data']['verdict']}")

    res_no = client.post("/api/afford", json={"item_name": "Superbike", "price": 200000, "current_balance": 15000})
    assert res_no.status_code == 200
    assert res_no.get_json()["data"]["verdict"] == "Not Recommended"
    print(f"[PASS] POST /api/afford verdict for 200,000 Superbike: {res_no.get_json()['data']['verdict']}")

    print("\nALL 12 INTEGRATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_verification()
