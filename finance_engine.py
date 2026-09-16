"""
finance_engine.py - Core Financial Logic & Calculation Engine for MONEYY
Tagline: "Your money. Your choices."
Pure Python financial formulas, budget alerts, savings projections, and insights.
Operates on Supabase PostgreSQL user data with strict user isolation.
"""

from datetime import datetime, date
import calendar
import math
from typing import Dict, Any, List, Optional
import supabase_db as sdb

# Standard App Categories & Payment Methods
INCOME_CATEGORIES = [
    "Allowance",
    "Salary/Stipend",
    "Scholarship",
    "Freelance",
    "Gifts",
    "Other",
]

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Housing",
    "Education",
    "Shopping",
    "Entertainment",
    "Health",
    "Bills/Subscriptions",
    "Travel",
    "Family",
    "Other",
]

PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Bank Transfer",
    "Other",
]

CATEGORY_EMOJIS = {
    # Income
    "Allowance": "👛",
    "Salary/Stipend": "💼",
    "Scholarship": "🎓",
    "Freelance": "💻",
    "Gifts": "🎁",
    # Expense
    "Food": "🍔",
    "Transport": "🚇",
    "Housing": "🏠",
    "Education": "📚",
    "Shopping": "🛍️",
    "Entertainment": "🎬",
    "Health": "💊",
    "Bills/Subscriptions": "📱",
    "Travel": "✈️",
    "Family": "👨‍👩‍👦",
    # Default
    "Other": "🏷️",
    "Overall": "🎯",
}


def get_current_month_str() -> str:
    """Returns current month in YYYY-MM format."""
    return date.today().strftime("%Y-%m")


def get_previous_month_str(month_str: str) -> str:
    """Returns previous month string YYYY-MM from given month."""
    dt = datetime.strptime(month_str, "%Y-%m")
    year = dt.year
    month = dt.month - 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def calculate_dashboard_summary(
    user_id: str,
    month: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes all high-level figures for the specified user:
    - Current balance (all-time income - all-time expenses)
    - Monthly income (for selected month)
    - Monthly expenses (for selected month)
    - Monthly savings (monthly income - monthly expenses)
    - Savings percentage
    - Spending breakdown by category
    - Recent transactions
    - Micro insights banner
    """
    if not month or month == "All":
        month = get_current_month_str()

    all_transactions = sdb.get_all_time_transactions(user_id=user_id, access_token=access_token)

    # 1. Total All-time Balance
    total_all_income = sum(float(t["amount"]) for t in all_transactions if t["type"] == "Income")
    total_all_expense = sum(float(t["amount"]) for t in all_transactions if t["type"] == "Expense")
    current_balance = round(total_all_income - total_all_expense, 2)

    # 2. Monthly Stats
    month_transactions = [t for t in all_transactions if str(t["date"])[:7] == month]
    monthly_income = round(sum(float(t["amount"]) for t in month_transactions if t["type"] == "Income"), 2)
    monthly_expenses = round(sum(float(t["amount"]) for t in month_transactions if t["type"] == "Expense"), 2)
    monthly_savings = round(monthly_income - monthly_expenses, 2)

    if monthly_income > 0:
        savings_percentage = round((monthly_savings / monthly_income) * 100, 1)
    else:
        savings_percentage = 0.0 if monthly_expenses == 0 else -100.0

    # 3. Category Breakdown for selected month
    breakdown_map: Dict[str, float] = {}
    for t in month_transactions:
        if t["type"] == "Expense":
            cat = t["category"]
            breakdown_map[cat] = breakdown_map.get(cat, 0.0) + float(t["amount"])

    spending_breakdown = []
    for cat, amt in sorted(breakdown_map.items(), key=lambda item: item[1], reverse=True):
        pct = round((amt / monthly_expenses) * 100, 1) if monthly_expenses > 0 else 0.0
        spending_breakdown.append({
            "category": cat,
            "amount": round(amt, 2),
            "percentage": pct,
            "emoji": CATEGORY_EMOJIS.get(cat, "🏷️"),
        })

    # 4. Recent Transactions (last 7)
    recent_transactions = []
    for t in all_transactions[:7]:
        recent_transactions.append({
            **t,
            "emoji": CATEGORY_EMOJIS.get(t["category"], "🏷️"),
        })

    # 5. Friendly quick insight
    quick_insight = generate_quick_insight(monthly_income, monthly_expenses, monthly_savings, savings_percentage, spending_breakdown)

    return {
        "month": month,
        "current_balance": current_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_savings": monthly_savings,
        "savings_percentage": savings_percentage,
        "spending_breakdown": spending_breakdown,
        "recent_transactions": recent_transactions,
        "quick_insight": quick_insight,
    }


def generate_quick_insight(
    monthly_income: float,
    monthly_expenses: float,
    monthly_savings: float,
    savings_pct: float,
    breakdown: List[Dict[str, Any]],
) -> Dict[str, str]:
    """Generates a student-friendly Gen-Z micro-insight."""
    if monthly_income == 0 and monthly_expenses == 0:
        return {
            "title": "Clean Slate ✨",
            "message": "Money in. Money out. No drama. Add your first transaction to start tracking!",
            "type": "neutral",
        }

    if monthly_savings < 0:
        return {
            "title": "Red Alert 🚨",
            "message": f"Spending is outstripping income by ₹{abs(monthly_savings):,.0f}. Time to slow down on non-essentials!",
            "type": "danger",
        }

    if savings_pct >= 40:
        return {
            "title": "Your wallet is looking healthy 👀",
            "message": f"You're saving {savings_pct}% of your money this month! Way ahead of the student curve.",
            "type": "success",
        }

    if breakdown and breakdown[0]["percentage"] >= 35:
        top_cat = breakdown[0]["category"]
        top_pct = breakdown[0]["percentage"]
        return {
            "title": f"Watch that {top_cat} 🎯",
            "message": f"{top_cat} takes up {top_pct}% of your expenses. Keep an eye on campus outings this week!",
            "type": "warning",
        }

    return {
        "title": "On Track 🚀",
        "message": f"Saved ₹{monthly_savings:,.0f} so far this month. Your money, decoded.",
        "type": "info",
    }


def calculate_budgets_status(
    user_id: str,
    month: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes overall budget and per-category budget statuses for the user,
    used/remaining amounts, and alert thresholds (healthy, warning >= 80%, exceeded >= 100%).
    """
    if not month or month == "All":
        month = get_current_month_str()

    month_transactions = sdb.get_transactions(user_id=user_id, trans_type="Expense", month=month, access_token=access_token)
    total_spent = sum(float(t["amount"]) for t in month_transactions)

    cat_spending: Dict[str, float] = {}
    for t in month_transactions:
        c = t["category"]
        cat_spending[c] = cat_spending.get(c, 0.0) + float(t["amount"])

    budgets_list = sdb.get_budgets(user_id=user_id, access_token=access_token)

    overall_budget_entry = next((b for b in budgets_list if b["category"] == "Overall"), None)
    overall_budget = None
    if overall_budget_entry:
        b_amt = float(overall_budget_entry["monthly_amount"])
        spent = total_spent
        remaining = round(b_amt - spent, 2)
        pct = round((spent / b_amt) * 100, 1) if b_amt > 0 else 0.0

        if pct >= 100.0:
            status = "exceeded"
            warning_msg = f"Over budget by ₹{abs(remaining):,.2f}! Pump the brakes."
        elif pct >= 80.0:
            status = "warning"
            warning_msg = f"Close to limit! Used {pct}% with ₹{remaining:,.2f} left."
        else:
            status = "healthy"
            warning_msg = f"Looking good! ₹{remaining:,.2f} remaining."

        overall_budget = {
            "id": str(overall_budget_entry["id"]),
            "budget_amount": b_amt,
            "spent": round(spent, 2),
            "remaining": remaining,
            "percentage": pct,
            "status": status,
            "warning_msg": warning_msg,
        }

    category_budgets = []
    for b in budgets_list:
        if b["category"] == "Overall":
            continue
        c = b["category"]
        b_amt = float(b["monthly_amount"])
        spent = cat_spending.get(c, 0.0)
        remaining = round(b_amt - spent, 2)
        pct = round((spent / b_amt) * 100, 1) if b_amt > 0 else 0.0

        if pct >= 100.0:
            status = "exceeded"
            warning_msg = f"Exceeded by ₹{abs(remaining):,.2f}!"
        elif pct >= 80.0:
            status = "warning"
            warning_msg = f"Warning: {pct}% used."
        else:
            status = "healthy"
            warning_msg = f"Safe: ₹{remaining:,.2f} remaining."

        category_budgets.append({
            "id": str(b["id"]),
            "category": c,
            "emoji": CATEGORY_EMOJIS.get(c, "🏷️"),
            "budget_amount": b_amt,
            "spent": round(spent, 2),
            "remaining": remaining,
            "percentage": pct,
            "status": status,
            "warning_msg": warning_msg,
        })

    return {
        "month": month,
        "overall_budget": overall_budget,
        "category_budgets": category_budgets,
        "has_any_budget": bool(overall_budget or category_budgets),
    }


def calculate_savings_goals_summary(
    user_id: str,
    month: Optional[str] = None,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Calculates progress, remaining balance, and estimated completion time for all user savings goals.
    """
    if not month or month == "All":
        month = get_current_month_str()

    dash = calculate_dashboard_summary(user_id=user_id, month=month, access_token=access_token)
    est_monthly_savings = max(0.0, dash["monthly_savings"])

    goals = sdb.get_savings_goals(user_id=user_id, access_token=access_token)
    results = []

    for g in goals:
        target = float(g["target_amount"])
        saved = float(g["saved_amount"])
        remaining = round(max(0.0, target - saved), 2)
        progress_pct = round((saved / target) * 100, 1) if target > 0 else 0.0

        if remaining == 0:
            estimated_time = "Goal Reached! 🎉"
            status = "completed"
        elif est_monthly_savings > 0:
            months = math.ceil(remaining / est_monthly_savings)
            if months <= 1:
                estimated_time = "~1 month at current savings rate"
            elif months < 12:
                estimated_time = f"~{months} months at current savings rate"
            else:
                years = round(months / 12, 1)
                estimated_time = f"~{years} years at current savings rate"
            status = "in_progress"
        else:
            estimated_time = "Save money this month to get an ETA!"
            status = "waiting_savings"

        icon = {
            "Laptop": "💻",
            "Trip": "🏖️",
            "Emergency Fund": "🛡️",
            "Phone": "📱",
        }.get(g.get("category_type"), "🎯")

        results.append({
            "id": str(g["id"]),
            "name": g["name"],
            "category_type": g.get("category_type", "Custom"),
            "icon": icon,
            "target_amount": target,
            "saved_amount": saved,
            "remaining": remaining,
            "progress_pct": min(100.0, progress_pct),
            "estimated_time": estimated_time,
            "status": status,
        })

    return results


def calculate_deep_insights(
    user_id: str,
    month: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes detailed financial insights based on the user's transactions:
    - Biggest expense category (name, amount, %)
    - Average daily spending
    - Savings rate (%)
    - Spending compared with previous month
    - Highest spending day
    - Spending trends (daily series)
    - Dynamic student financial tips
    """
    if not month or month == "All":
        month = get_current_month_str()

    prev_month = get_previous_month_str(month)

    all_transactions = sdb.get_all_time_transactions(user_id=user_id, access_token=access_token)
    curr_txns = [t for t in all_transactions if str(t["date"])[:7] == month]
    prev_txns = [t for t in all_transactions if str(t["date"])[:7] == prev_month]

    curr_income = sum(float(t["amount"]) for t in curr_txns if t["type"] == "Income")
    curr_expenses = sum(float(t["amount"]) for t in curr_txns if t["type"] == "Expense")
    curr_savings = curr_income - curr_expenses

    prev_expenses = sum(float(t["amount"]) for t in prev_txns if t["type"] == "Expense")

    # 1. Biggest Expense Category
    expense_breakdown: Dict[str, float] = {}
    for t in curr_txns:
        if t["type"] == "Expense":
            c = t["category"]
            expense_breakdown[c] = expense_breakdown.get(c, 0.0) + float(t["amount"])

    if expense_breakdown and curr_expenses > 0:
        biggest_cat = max(expense_breakdown, key=expense_breakdown.get)
        biggest_amt = expense_breakdown[biggest_cat]
        biggest_pct = round((biggest_amt / curr_expenses) * 100, 1)
        biggest_expense = {
            "category": biggest_cat,
            "amount": round(biggest_amt, 2),
            "percentage": biggest_pct,
            "emoji": CATEGORY_EMOJIS.get(biggest_cat, "🏷️"),
        }
    else:
        biggest_expense = {
            "category": "None yet",
            "amount": 0.0,
            "percentage": 0.0,
            "emoji": "✨",
        }

    # 2. Average Daily Spending
    today = date.today()
    curr_year, curr_m = map(int, month.split("-"))
    num_days_in_month = calendar.monthrange(curr_year, curr_m)[1]

    if curr_year == today.year and curr_m == today.month:
        days_elapsed = max(1, today.day)
    else:
        days_elapsed = num_days_in_month

    avg_daily_spending = round(curr_expenses / days_elapsed, 2) if days_elapsed > 0 else 0.0

    # 3. Savings Rate
    if curr_income > 0:
        savings_rate = round((curr_savings / curr_income) * 100, 1)
    else:
        savings_rate = 0.0 if curr_expenses == 0 else -100.0

    # 4. Spending Compared with Previous Month
    diff_amount = round(curr_expenses - prev_expenses, 2)
    pct_change = round(((curr_expenses - prev_expenses) / prev_expenses) * 100, 1) if prev_expenses > 0 else 0.0

    if prev_expenses == 0 and curr_expenses == 0:
        month_comparison_text = "No previous month data to compare."
        comparison_badge = "neutral"
    elif curr_expenses < prev_expenses:
        month_comparison_text = f"You spent ₹{abs(diff_amount):,.0f} ({abs(pct_change)}%) less than last month! 👏 Great restraint."
        comparison_badge = "success"
    elif curr_expenses > prev_expenses:
        month_comparison_text = f"Spending is up ₹{diff_amount:,.0f} (+{pct_change}%) compared to last month."
        comparison_badge = "warning"
    else:
        month_comparison_text = "Spending is exactly identical to last month!"
        comparison_badge = "info"

    # 5. Highest Spending Day
    daily_spend_map: Dict[str, float] = {}
    day_top_item: Dict[str, Dict[str, Any]] = {}
    for t in curr_txns:
        if t["type"] == "Expense":
            d_str = str(t["date"])
            amt = float(t["amount"])
            daily_spend_map[d_str] = daily_spend_map.get(d_str, 0.0) + amt
            if d_str not in day_top_item or amt > float(day_top_item[d_str]["amount"]):
                day_top_item[d_str] = t

    if daily_spend_map:
        peak_day = max(daily_spend_map, key=daily_spend_map.get)
        peak_amount = round(daily_spend_map[peak_day], 2)
        peak_item = day_top_item.get(peak_day, {}).get("description", "Various expenses")
        highest_spending_day = {
            "date": peak_day,
            "amount": peak_amount,
            "top_item": peak_item,
        }
    else:
        highest_spending_day = {
            "date": "N/A",
            "amount": 0.0,
            "top_item": "No expenses recorded",
        }

    # 6. Spending Trends
    spending_trends = []
    for d_str in sorted(daily_spend_map.keys()):
        spending_trends.append({
            "date": d_str,
            "day": d_str.split("-")[-1],
            "amount": round(daily_spend_map[d_str], 2),
        })

    # 7. Student Actionable Tips
    student_tips = generate_student_tips(biggest_expense, savings_rate, avg_daily_spending, curr_expenses)

    return {
        "month": month,
        "previous_month": prev_month,
        "biggest_expense": biggest_expense,
        "avg_daily_spending": avg_daily_spending,
        "days_elapsed": days_elapsed,
        "savings_rate": savings_rate,
        "month_comparison": {
            "current_month_expenses": round(curr_expenses, 2),
            "previous_month_expenses": round(prev_expenses, 2),
            "difference": diff_amount,
            "percentage_change": pct_change,
            "message": month_comparison_text,
            "badge": comparison_badge,
        },
        "highest_spending_day": highest_spending_day,
        "spending_trends": spending_trends,
        "student_tips": student_tips,
    }


def generate_student_tips(
    biggest_expense: Dict[str, Any],
    savings_rate: float,
    daily_avg: float,
    total_expenses: float,
) -> List[Dict[str, str]]:
    """Curates personalized money advice for students."""
    tips = []
    cat = biggest_expense.get("category", "")
    pct = biggest_expense.get("percentage", 0)

    if cat == "Food" and pct >= 30:
        tips.append({
            "icon": "🍔",
            "title": "Campus Canteen vs Swiggy",
            "desc": f"Food took {pct}% of your expenses. Packing snacks or grabbing canteen meals on alternate days can save ₹1,000–2,000 monthly!",
        })
    elif cat == "Shopping" and pct >= 25:
        tips.append({
            "icon": "🛍️",
            "title": "The 48-Hour Cart Rule",
            "desc": "Before buying non-essential items online, wait 48 hours. If you still want it, check if a student coupon or second-hand option exists.",
        })
    elif cat == "Bills/Subscriptions" and pct >= 15:
        tips.append({
            "icon": "📱",
            "title": "Student Discounts on Subscriptions",
            "desc": "Make sure you're using Spotify Student, Apple Music Student, and GitHub Student Developer Pack to save up to 50% on recurring digital services.",
        })

    if savings_rate >= 30:
        tips.append({
            "icon": "🚀",
            "title": "High Savings Momentum",
            "desc": f"A {savings_rate}% savings rate is stellar for students! Consider parking some in a high-yield emergency savings goal or term deposit.",
        })
    elif savings_rate < 10:
        tips.append({
            "icon": "💡",
            "title": "Small Daily Cuts",
            "desc": f"Your daily spend is ₹{daily_avg:,.0f}. Shaving off just ₹50–100/day adds ₹1,500–3,000 back into your savings by month end.",
        })

    tips.append({
        "icon": "💳",
        "title": "UPI Micro-Spends Add Up",
        "desc": "Tap-and-pay UPI makes ₹40 chai and ₹80 treats feel invisible. Tracking them here gives you true control over your cash.",
    })

    return tips


def evaluate_affordability(
    item_name: str,
    price: float,
    current_balance: Optional[float] = None,
    user_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates whether a student can afford a purchase:
    Input: item_name, price, current_balance (auto-calculated from user's transactions if None)
    Output:
    - remaining_balance
    - result: "Looks Good", "Think Twice", or "Not Recommended"
    - percentage_of_balance
    - advice and breakdown
    """
    if price <= 0:
        raise ValueError("Price must be greater than 0")

    if current_balance is None:
        if user_id:
            summary = calculate_dashboard_summary(user_id=user_id, access_token=access_token)
            current_balance = summary["current_balance"]
        else:
            current_balance = 0.0

    remaining_balance = round(current_balance - price, 2)
    name = item_name.strip() if item_name and item_name.strip() else "This item"

    if current_balance <= 0:
        return {
            "item_name": name,
            "price": round(price, 2),
            "current_balance": round(current_balance, 2),
            "remaining_balance": remaining_balance,
            "verdict": "Not Recommended",
            "badge_color": "danger",
            "emoji": "🚫",
            "percentage_of_balance": 100.0,
            "headline": "Wallet is at zero or negative!",
            "explanation": f"You currently have ₹{current_balance:,.2f} in your account. Buying {name} for ₹{price:,.2f} would put you in debt.",
            "recommendation": "Hold off on this purchase until you've received your next allowance or stipend.",
        }

    spend_pct = round((price / current_balance) * 100, 1)

    if price > current_balance:
        return {
            "item_name": name,
            "price": round(price, 2),
            "current_balance": round(current_balance, 2),
            "remaining_balance": remaining_balance,
            "verdict": "Not Recommended",
            "badge_color": "danger",
            "emoji": "🚫",
            "percentage_of_balance": spend_pct,
            "headline": "Out of your current budget range",
            "explanation": f"{name} costs ₹{price:,.2f}, which is ₹{abs(remaining_balance):,.2f} more than your total available balance of ₹{current_balance:,.2f}.",
            "recommendation": "Create a Savings Goal for it instead and set aside a little each month!",
        }

    # Leaves tight cushion: takes > 50% of money or leaves under ₹1,000
    if spend_pct > 50.0 or remaining_balance < 1000.0:
        return {
            "item_name": name,
            "price": round(price, 2),
            "current_balance": round(current_balance, 2),
            "remaining_balance": remaining_balance,
            "verdict": "Think Twice",
            "badge_color": "warning",
            "emoji": "⚠️",
            "percentage_of_balance": spend_pct,
            "headline": "Leaves you with very low cushion",
            "explanation": f"This purchase absorbs {spend_pct}% of your available funds. You'll only have ₹{remaining_balance:,.2f} left for the rest of the month.",
            "recommendation": "Ask yourself: Is this an urgent necessity, or can it wait until after exams / next month's allowance?",
        }

    # Plenty of cushion:
    return {
        "item_name": name,
        "price": round(price, 2),
        "current_balance": round(current_balance, 2),
        "remaining_balance": remaining_balance,
        "verdict": "Looks Good",
        "badge_color": "success",
        "emoji": "🎉",
        "percentage_of_balance": spend_pct,
        "headline": "Affordable with a healthy buffer!",
        "explanation": f"{name} only takes {spend_pct}% of your balance. You'll still have a solid cushion of ₹{remaining_balance:,.2f} remaining.",
        "recommendation": "You can comfortably afford this without putting your finances at risk. Enjoy your choice!",
    }
