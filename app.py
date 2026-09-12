"""
app.py - Flask Server for MONEYY Personal Finance Tracker
Tagline: "Your money. Your choices."
Built for students from Class 12 to postgraduate level.
"""

import os
import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, jsonify

import database as db
import finance_engine as fe

app = Flask(__name__)


# ==========================================
# PAGE ROUTE
# ==========================================

@app.route("/")
def index():
    """Renders the single-page application."""
    return render_template("index.html")


# ==========================================
# DASHBOARD API
# ==========================================

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Returns dashboard financial metrics, breakdown, and quick insight."""
    try:
        month = request.args.get("month")
        summary = fe.calculate_dashboard_summary(month=month)
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# TRANSACTIONS API
# ==========================================

@app.route("/api/transactions", methods=["GET"])
def api_get_transactions():
    """Retrieves filtered list of transactions."""
    try:
        trans_type = request.args.get("type")
        category = request.args.get("category")
        month = request.args.get("month")
        search = request.args.get("search")
        limit = request.args.get("limit", type=int)

        txns = db.get_transactions(
            trans_type=trans_type,
            category=category,
            month=month,
            search=search,
            limit=limit,
        )
        # Attach emoji to each transaction
        for t in txns:
            t["emoji"] = fe.CATEGORY_EMOJIS.get(t["category"], "🏷️")

        return jsonify({"success": True, "data": txns, "count": len(txns)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions", methods=["POST"])
def api_add_transaction():
    """Adds a new income or expense transaction."""
    try:
        payload = request.get_json(force=True) or {}
        trans_type = payload.get("type", "Expense")
        amount = float(payload.get("amount", 0))
        category = payload.get("category", "Other")
        description = payload.get("description", "").strip()
        trans_date = payload.get("date") or fe.get_current_month_str() + "-01"
        payment_method = payload.get("payment_method", "UPI")
        note = payload.get("note", "").strip()

        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400

        t_id = db.add_transaction(
            trans_type=trans_type,
            amount=amount,
            category=category,
            description=description,
            trans_date=trans_date,
            payment_method=payment_method,
            note=note,
        )
        created = db.get_transaction(t_id)
        if created:
            created["emoji"] = fe.CATEGORY_EMOJIS.get(created["category"], "🏷️")

        return jsonify({"success": True, "data": created, "message": "Transaction added successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions/<int:trans_id>", methods=["GET"])
def api_get_single_transaction(trans_id: int):
    """Fetches a single transaction by ID."""
    t = db.get_transaction(trans_id)
    if not t:
        return jsonify({"success": False, "error": "Transaction not found"}), 404
    t["emoji"] = fe.CATEGORY_EMOJIS.get(t["category"], "🏷️")
    return jsonify({"success": True, "data": t})


@app.route("/api/transactions/<int:trans_id>", methods=["PUT"])
def api_update_transaction(trans_id: int):
    """Updates an existing transaction."""
    try:
        payload = request.get_json(force=True) or {}
        trans_type = payload.get("type", "Expense")
        amount = float(payload.get("amount", 0))
        category = payload.get("category", "Other")
        description = payload.get("description", "").strip()
        trans_date = payload.get("date")
        payment_method = payload.get("payment_method", "UPI")
        note = payload.get("note", "").strip()

        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400

        updated = db.update_transaction(
            trans_id=trans_id,
            trans_type=trans_type,
            amount=amount,
            category=category,
            description=description,
            trans_date=trans_date,
            payment_method=payment_method,
            note=note,
        )
        if not updated:
            return jsonify({"success": False, "error": "Transaction not found or not modified"}), 404

        t = db.get_transaction(trans_id)
        if t:
            t["emoji"] = fe.CATEGORY_EMOJIS.get(t["category"], "🏷️")
        return jsonify({"success": True, "data": t, "message": "Transaction updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions/<int:trans_id>", methods=["DELETE"])
def api_delete_transaction(trans_id: int):
    """Deletes a transaction."""
    try:
        deleted = db.delete_transaction(trans_id)
        if not deleted:
            return jsonify({"success": False, "error": "Transaction not found"}), 404
        return jsonify({"success": True, "message": "Transaction deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# BUDGETS API
# ==========================================

@app.route("/api/budgets", methods=["GET"])
def api_get_budgets():
    """Returns overall and category budget statuses."""
    try:
        month = request.args.get("month")
        status = fe.calculate_budgets_status(month=month)
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/budgets", methods=["POST"])
def api_set_budget():
    """Sets or updates a monthly budget."""
    try:
        payload = request.get_json(force=True) or {}
        category = payload.get("category", "Overall").strip()
        amount = float(payload.get("amount", 0))

        if amount <= 0:
            return jsonify({"success": False, "error": "Budget amount must be greater than 0"}), 400

        b_id = db.set_budget(category=category, monthly_amount=amount)
        return jsonify({"success": True, "message": f"Budget for {category} set to {amount}!", "id": b_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
def api_delete_budget(budget_id: int):
    """Deletes a budget."""
    try:
        deleted = db.delete_budget(budget_id)
        if not deleted:
            return jsonify({"success": False, "error": "Budget not found"}), 404
        return jsonify({"success": True, "message": "Budget removed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# SAVINGS GOALS API
# ==========================================

@app.route("/api/goals", methods=["GET"])
def api_get_goals():
    """Returns all savings goals with progress and ETA."""
    try:
        month = request.args.get("month")
        goals = fe.calculate_savings_goals_summary(month=month)
        return jsonify({"success": True, "data": goals})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals", methods=["POST"])
def api_add_goal():
    """Creates a new savings goal."""
    try:
        payload = request.get_json(force=True) or {}
        name = payload.get("name", "").strip()
        target_amount = float(payload.get("target_amount", 0))
        saved_amount = float(payload.get("saved_amount", 0))
        category_type = payload.get("category_type", "Custom").strip()

        if not name:
            return jsonify({"success": False, "error": "Goal name is required"}), 400
        if target_amount <= 0:
            return jsonify({"success": False, "error": "Target amount must be greater than 0"}), 400

        g_id = db.add_savings_goal(
            name=name,
            target_amount=target_amount,
            saved_amount=saved_amount,
            category_type=category_type,
        )
        return jsonify({"success": True, "message": "Savings goal created!", "id": g_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<int:goal_id>", methods=["PUT"])
def api_update_goal(goal_id: int):
    """Updates a savings goal."""
    try:
        payload = request.get_json(force=True) or {}
        name = payload.get("name", "").strip()
        target_amount = float(payload.get("target_amount", 0))
        saved_amount = float(payload.get("saved_amount", 0))
        category_type = payload.get("category_type", "Custom").strip()

        if not name:
            return jsonify({"success": False, "error": "Goal name is required"}), 400
        if target_amount <= 0:
            return jsonify({"success": False, "error": "Target amount must be greater than 0"}), 400

        updated = db.update_savings_goal(
            goal_id=goal_id,
            name=name,
            target_amount=target_amount,
            saved_amount=saved_amount,
            category_type=category_type,
        )
        if not updated:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": "Goal updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<int:goal_id>/deposit", methods=["POST"])
def api_deposit_goal(goal_id: int):
    """Deposits money into an existing savings goal."""
    try:
        payload = request.get_json(force=True) or {}
        amount = float(payload.get("amount", 0))
        if amount <= 0:
            return jsonify({"success": False, "error": "Deposit amount must be greater than 0"}), 400

        updated = db.deposit_to_savings_goal(goal_id, amount)
        if not updated:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": f"Added funds to your savings goal!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
def api_delete_goal(goal_id: int):
    """Deletes a savings goal."""
    try:
        deleted = db.delete_savings_goal(goal_id)
        if not deleted:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": "Goal deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# INSIGHTS API
# ==========================================

@app.route("/api/insights", methods=["GET"])
def api_get_insights():
    """Computes dynamic financial insights."""
    try:
        month = request.args.get("month")
        insights = fe.calculate_deep_insights(month=month)
        return jsonify({"success": True, "data": insights})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# CAN I AFFORD IT? API
# ==========================================

@app.route("/api/afford", methods=["POST"])
def api_afford():
    """Evaluates whether the user can afford a purchase."""
    try:
        payload = request.get_json(force=True) or {}
        item_name = str(payload.get("item_name", "Item")).strip()
        price = float(payload.get("price", 0))
        custom_balance = payload.get("current_balance")

        balance_arg = float(custom_balance) if custom_balance is not None and str(custom_balance).strip() != "" else None

        if price <= 0:
            return jsonify({"success": False, "error": "Price must be greater than 0"}), 400

        result = fe.evaluate_affordability(
            item_name=item_name,
            price=price,
            current_balance=balance_arg,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==========================================
# METADATA & DEMO CONTROLS
# ==========================================

@app.route("/api/meta", methods=["GET"])
def api_meta():
    """Returns categories, payment methods, and emojis for UI selects."""
    return jsonify({
        "success": True,
        "income_categories": fe.INCOME_CATEGORIES,
        "expense_categories": fe.EXPENSE_CATEGORIES,
        "payment_methods": fe.PAYMENT_METHODS,
        "category_emojis": fe.CATEGORY_EMOJIS,
        "current_month": fe.get_current_month_str(),
    })


@app.route("/api/demo/seed", methods=["POST"])
def api_demo_seed():
    """Re-seeds demo student transactions and budgets."""
    try:
        db.seed_demo_data(force=True)
        return jsonify({"success": True, "message": "Demo data reloaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/demo/clear", methods=["POST"])
def api_demo_clear():
    """Clears all transactions, budgets, and goals."""
    try:
        db.clear_all_data()
        return jsonify({"success": True, "message": "All data cleared. Clean slate ready!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


def open_browser():
    """Helper to automatically launch default browser on startup."""
    webbrowser.open_new("http://127.0.0.1:5000/")


# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Initialize DB & Seed demo data on first start if empty
    db.init_db()
    db.seed_demo_data(force=False)

    print("=" * 60)
    print(f"🚀 MONEYY is live at: http://127.0.0.1:{port}/")
    print("   Tagline: 'Your money. Your choices.'")
    print("   Built for students, not accountants :)")
    print("=" * 60)

    if os.environ.get("OPEN_BROWSER", "false").lower() == "true":
        Timer(1.2, open_browser).start()

    app.run(host="127.0.0.1", port=port, debug=True)
