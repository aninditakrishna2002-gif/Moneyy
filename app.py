"""
app.py - Flask Server for MONEYY Personal Finance Tracker
Tagline: "Your money. Your choices."
Powered by Supabase Auth and Supabase PostgreSQL with Row Level Security.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from functools import wraps
from flask import Flask, render_template, request, jsonify, session

import supabase_client as sc
import supabase_db as sdb
import finance_engine as fe

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "moneyy-student-fintech-2026-secure-session")


# ==============================================================================
# AUTHENTICATION DECORATOR & HELPERS
# ==============================================================================

def get_current_token_and_user():
    """Extracts access token from Authorization header or Flask session, and retrieves user."""
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif session.get("access_token"):
        token = session.get("access_token")

    if not token:
        return None, None

    # Check session user cache first
    cached_user = session.get("user")
    if cached_user and session.get("access_token") == token:
        return token, cached_user

    # Verify with Supabase
    user = sc.get_user_from_token(token)
    if user:
        session["user"] = user
        session["access_token"] = token
        return token, user

    return None, None


def auth_required(f):
    """Decorator to protect routes requiring Supabase authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token, user = get_current_token_and_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401
        request.user = user
        request.access_token = token
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# PAGE ROUTE
# ==============================================================================

@app.route("/")
def index():
    """Renders the single-page application."""
    return render_template("index.html")


# ==============================================================================
# AUTH API ENDPOINTS
# ==============================================================================

@app.route("/api/auth/signup", methods=["POST"])
def api_auth_signup():
    """Registers a new user with Supabase Auth."""
    try:
        data = request.get_json(force=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")
        name = data.get("name", "").strip()

        if not email or not password or not name:
            return jsonify({"success": False, "error": "Name, email, and password are required."}), 400

        success, result = sc.sign_up_user(email, password, name)
        if not success:
            return jsonify({"success": False, "error": result.get("error", "Signup failed.")}), 400

        # Save session if available
        user_info = result.get("user", {})
        session_info = result.get("session", {})
        if session_info.get("access_token"):
            session["access_token"] = session_info["access_token"]
            session["user"] = user_info

        return jsonify({
            "success": True,
            "data": result,
            "message": "Account created successfully! Welcome to MONEYY.",
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """Authenticates an existing user via Supabase Auth."""
    try:
        data = request.get_json(force=True) or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password are required."}), 400

        success, result = sc.sign_in_user(email, password)
        if not success:
            return jsonify({"success": False, "error": result.get("error", "Login failed.")}), 401

        user_info = result.get("user", {})
        session_info = result.get("session", {})
        session["access_token"] = session_info["access_token"]
        session["user"] = user_info

        return jsonify({
            "success": True,
            "data": result,
            "message": f"Welcome back, {user_info.get('name', 'Student')}!",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    """Logs out user and clears session."""
    token = session.get("access_token")
    if token:
        sc.sign_out_user(token)
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    """Returns currently authenticated user profile."""
    token, user = get_current_token_and_user()
    if not user:
        return jsonify({"success": False, "data": None})
    return jsonify({"success": True, "data": {"user": user, "access_token": token}})


# ==============================================================================
# DASHBOARD API (PROTECTED)
# ==============================================================================

@app.route("/api/dashboard", methods=["GET"])
@auth_required
def api_dashboard():
    """Returns dashboard financial metrics for the authenticated user."""
    try:
        month = request.args.get("month")
        summary = fe.calculate_dashboard_summary(
            user_id=request.user["id"],
            month=month,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# TRANSACTIONS API (PROTECTED)
# ==============================================================================

@app.route("/api/transactions", methods=["GET"])
@auth_required
def api_get_transactions():
    """Retrieves user's transactions with filtering."""
    try:
        trans_type = request.args.get("type")
        category = request.args.get("category")
        month = request.args.get("month")
        search = request.args.get("search")
        limit = request.args.get("limit", type=int)

        txns = sdb.get_transactions(
            user_id=request.user["id"],
            trans_type=trans_type,
            category=category,
            month=month,
            search=search,
            limit=limit,
            access_token=request.access_token,
        )
        for t in txns:
            t["emoji"] = fe.CATEGORY_EMOJIS.get(t.get("category"), "🏷️")

        return jsonify({"success": True, "data": txns, "count": len(txns)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions", methods=["POST"])
@auth_required
def api_add_transaction():
    """Adds a new transaction linked to the user's UUID."""
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

        created = sdb.add_transaction(
            user_id=request.user["id"],
            trans_type=trans_type,
            amount=amount,
            category=category,
            description=description,
            trans_date=trans_date,
            payment_method=payment_method,
            note=note,
            access_token=request.access_token,
        )
        if created:
            created["emoji"] = fe.CATEGORY_EMOJIS.get(created.get("category"), "🏷️")

        return jsonify({"success": True, "data": created, "message": "Transaction added successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions/<string:trans_id>", methods=["GET"])
@auth_required
def api_get_single_transaction(trans_id: str):
    """Fetches a single transaction by ID."""
    t = sdb.get_transaction(trans_id=trans_id, user_id=request.user["id"], access_token=request.access_token)
    if not t:
        return jsonify({"success": False, "error": "Transaction not found"}), 404
    t["emoji"] = fe.CATEGORY_EMOJIS.get(t.get("category"), "🏷️")
    return jsonify({"success": True, "data": t})


@app.route("/api/transactions/<string:trans_id>", methods=["PUT"])
@auth_required
def api_update_transaction(trans_id: str):
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

        updated = sdb.update_transaction(
            trans_id=trans_id,
            user_id=request.user["id"],
            trans_type=trans_type,
            amount=amount,
            category=category,
            description=description,
            trans_date=trans_date,
            payment_method=payment_method,
            note=note,
            access_token=request.access_token,
        )
        if not updated:
            return jsonify({"success": False, "error": "Transaction not found or not modified"}), 404

        t = sdb.get_transaction(trans_id=trans_id, user_id=request.user["id"], access_token=request.access_token)
        if t:
            t["emoji"] = fe.CATEGORY_EMOJIS.get(t.get("category"), "🏷️")
        return jsonify({"success": True, "data": t, "message": "Transaction updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/transactions/<string:trans_id>", methods=["DELETE"])
@auth_required
def api_delete_transaction(trans_id: str):
    """Deletes a transaction."""
    try:
        deleted = sdb.delete_transaction(trans_id=trans_id, user_id=request.user["id"], access_token=request.access_token)
        if not deleted:
            return jsonify({"success": False, "error": "Transaction not found"}), 404
        return jsonify({"success": True, "message": "Transaction deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# BUDGETS API (PROTECTED)
# ==============================================================================

@app.route("/api/budgets", methods=["GET"])
@auth_required
def api_get_budgets():
    """Returns budget statuses for the user."""
    try:
        month = request.args.get("month")
        status = fe.calculate_budgets_status(
            user_id=request.user["id"],
            month=month,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/budgets", methods=["POST"])
@auth_required
def api_set_budget():
    """Sets or updates a monthly budget for the user."""
    try:
        payload = request.get_json(force=True) or {}
        category = payload.get("category", "Overall").strip()
        amount = float(payload.get("amount", 0))

        if amount <= 0:
            return jsonify({"success": False, "error": "Budget amount must be greater than 0"}), 400

        result = sdb.set_budget(
            user_id=request.user["id"],
            category=category,
            monthly_amount=amount,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "message": f"Budget for {category} set to {amount}!", "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/budgets/<string:budget_id>", methods=["DELETE"])
@auth_required
def api_delete_budget(budget_id: str):
    """Deletes a budget."""
    try:
        deleted = sdb.delete_budget(budget_id=budget_id, user_id=request.user["id"], access_token=request.access_token)
        if not deleted:
            return jsonify({"success": False, "error": "Budget not found"}), 404
        return jsonify({"success": True, "message": "Budget removed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# SAVINGS GOALS API (PROTECTED)
# ==============================================================================

@app.route("/api/goals", methods=["GET"])
@auth_required
def api_get_goals():
    """Returns all savings goals for the user."""
    try:
        month = request.args.get("month")
        goals = fe.calculate_savings_goals_summary(
            user_id=request.user["id"],
            month=month,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "data": goals})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals", methods=["POST"])
@auth_required
def api_add_goal():
    """Creates a new savings goal for the user."""
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

        result = sdb.add_savings_goal(
            user_id=request.user["id"],
            name=name,
            target_amount=target_amount,
            saved_amount=saved_amount,
            category_type=category_type,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "message": "Savings goal created!", "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<string:goal_id>", methods=["PUT"])
@auth_required
def api_update_goal(goal_id: str):
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

        updated = sdb.update_savings_goal(
            goal_id=goal_id,
            user_id=request.user["id"],
            name=name,
            target_amount=target_amount,
            saved_amount=saved_amount,
            category_type=category_type,
            access_token=request.access_token,
        )
        if not updated:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": "Goal updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<string:goal_id>/deposit", methods=["POST"])
@auth_required
def api_deposit_goal(goal_id: str):
    """Deposits funds into an existing savings goal."""
    try:
        payload = request.get_json(force=True) or {}
        amount = float(payload.get("amount", 0))
        if amount <= 0:
            return jsonify({"success": False, "error": "Deposit amount must be greater than 0"}), 400

        updated = sdb.deposit_to_savings_goal(
            goal_id=goal_id,
            user_id=request.user["id"],
            amount=amount,
            access_token=request.access_token,
        )
        if not updated:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": "Added funds to your savings goal!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/goals/<string:goal_id>", methods=["DELETE"])
@auth_required
def api_delete_goal(goal_id: str):
    """Deletes a savings goal."""
    try:
        deleted = sdb.delete_savings_goal(goal_id=goal_id, user_id=request.user["id"], access_token=request.access_token)
        if not deleted:
            return jsonify({"success": False, "error": "Goal not found"}), 404
        return jsonify({"success": True, "message": "Goal deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# INSIGHTS API (PROTECTED)
# ==============================================================================

@app.route("/api/insights", methods=["GET"])
@auth_required
def api_get_insights():
    """Computes dynamic financial insights for the user."""
    try:
        month = request.args.get("month")
        insights = fe.calculate_deep_insights(
            user_id=request.user["id"],
            month=month,
            access_token=request.access_token,
        )
        return jsonify({"success": True, "data": insights})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# CAN I AFFORD IT? API (PROTECTED)
# ==============================================================================

@app.route("/api/afford", methods=["POST"])
@auth_required
def api_afford():
    """Evaluates whether the user can afford a purchase based on live balance."""
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
            user_id=request.user["id"],
            access_token=request.access_token,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# METADATA & DEMO CONTROLS (PROTECTED)
# ==============================================================================

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
        "supabase_configured": sc.is_supabase_configured(),
    })


@app.route("/api/demo/seed", methods=["POST"])
@auth_required
def api_demo_seed():
    """Re-seeds demo student transactions and budgets for this user."""
    try:
        sdb.seed_user_demo_data(user_id=request.user["id"], access_token=request.access_token, force=True)
        return jsonify({"success": True, "message": "Demo data reloaded for your account!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/demo/clear", methods=["POST"])
@auth_required
def api_demo_clear():
    """Clears all transactions, budgets, and goals for this user."""
    try:
        sdb.clear_user_data(user_id=request.user["id"], access_token=request.access_token)
        return jsonify({"success": True, "message": "Your data has been cleared. Clean slate ready!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f"🚀 MONEYY with Supabase is live at: http://127.0.0.1:{port}/")
    print("   Tagline: 'Your money. Your choices.'")
    print(f"   Supabase Configured: {sc.is_supabase_configured()}")
    print("=" * 60)

    app.run(host="127.0.0.1", port=port, debug=True)
