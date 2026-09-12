"""
finance_logic.py - Core Financial Calculations for MONEYY
Built for students: Class 12, Undergraduates, and Postgraduates.
Lightweight, pure Python, zero external dependencies.
"""

from typing import Dict, Any, Tuple
import math


def calculate_finances(
    allowance: float = 0.0,
    part_time: float = 0.0,
    scholarship: float = 0.0,
    other_income: float = 0.0,
    food: float = 0.0,
    transport: float = 0.0,
    education: float = 0.0,
    entertainment: float = 0.0,
    shopping: float = 0.0,
    other_expenses: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates student cash flow, savings rate, biggest expense category,
    financial health status, and a personalized money tip.
    """
    # 1. Total money coming in
    income_breakdown = {
        "Allowance": max(0.0, float(allowance)),
        "Part-time Income": max(0.0, float(part_time)),
        "Scholarship": max(0.0, float(scholarship)),
        "Other Income": max(0.0, float(other_income)),
    }
    total_income = sum(income_breakdown.values())

    # 2. Monthly expenses
    expense_breakdown = {
        "Food": max(0.0, float(food)),
        "Transport": max(0.0, float(transport)),
        "Education": max(0.0, float(education)),
        "Entertainment": max(0.0, float(entertainment)),
        "Shopping": max(0.0, float(shopping)),
        "Other Expenses": max(0.0, float(other_expenses)),
    }
    total_spending = sum(expense_breakdown.values())

    # 3. Calculations
    money_left = total_income - total_spending

    if total_income > 0:
        savings_rate = round((money_left / total_income) * 100, 1)
    else:
        # If income is 0, savings rate cannot be positive
        savings_rate = 0.0 if total_spending == 0 else -100.0

    # 4. Find the biggest expense category
    if total_spending > 0:
        biggest_category = max(expense_breakdown, key=expense_breakdown.get)
        biggest_amount = expense_breakdown[biggest_category]
        biggest_percentage = round((biggest_amount / total_spending) * 100, 1)
    else:
        biggest_category = "None"
        biggest_amount = 0.0
        biggest_percentage = 0.0

    # 5. Financial Status Assessment
    if total_income == 0 and total_spending == 0:
        status = "Needs Attention"
        status_color = "neutral"
        status_summary = "Enter your income and expenses to see your financial health check."
    elif money_left < 0:
        status = "Needs Attention"
        status_color = "danger"
        status_summary = "You're spending more than you bring in. Time to trim some non-essentials!"
    elif savings_rate < 10.0:
        status = "Needs Attention"
        status_color = "warning"
        status_summary = "You're living paycheck-to-paycheck or allowance-to-allowance. Try building a small safety cushion."
    elif savings_rate < 25.0:
        status = "Moderate"
        status_color = "info"
        status_summary = "Solid balance! You're covering expenses with a modest cushion left over."
    else:
        status = "Good"
        status_color = "success"
        status_summary = "Crushing it! You're saving a healthy slice of your student funds."

    # 6. Personalized Money Tip based on student spending profile
    tip = generate_personalized_tip(
        total_income=total_income,
        total_spending=total_spending,
        money_left=money_left,
        savings_rate=savings_rate,
        biggest_category=biggest_category,
        biggest_amount=biggest_amount,
        biggest_percentage=biggest_percentage,
        expense_breakdown=expense_breakdown,
    )

    return {
        "total_income": round(total_income, 2),
        "total_spending": round(total_spending, 2),
        "money_left": round(money_left, 2),
        "savings_rate": savings_rate,
        "biggest_expense": {
            "category": biggest_category,
            "amount": round(biggest_amount, 2),
            "percentage": biggest_percentage,
        },
        "status": status,
        "status_color": status_color,
        "status_summary": status_summary,
        "tip": tip,
        "breakdown": {
            "income": {k: round(v, 2) for k, v in income_breakdown.items()},
            "expenses": {k: round(v, 2) for k, v in expense_breakdown.items()},
        },
    }


def generate_personalized_tip(
    total_income: float,
    total_spending: float,
    money_left: float,
    savings_rate: float,
    biggest_category: str,
    biggest_amount: float,
    biggest_percentage: float,
    expense_breakdown: Dict[str, float],
) -> str:
    """Generates a friendly, practical, student-centric financial tip."""
    if total_income == 0 and total_spending == 0:
        return "Add your monthly allowance, scholarship, or side gigs to get started!"

    if money_left < 0:
        deficit = abs(money_left)
        return (
            f"You're in the red by {deficit:,.2f}. Check if you can reduce {biggest_category.lower()} "
            "this month so you don't have to borrow from friends or family."
        )

    # Specific category insights
    if biggest_category == "Food" and biggest_percentage >= 35.0:
        return (
            f"Food takes up {biggest_percentage}% of your budget! Cooking with roommates or taking "
            "advantage of the campus dining hall/tiffin can easily free up 15-20% more cash."
        )

    if biggest_category == "Shopping" and biggest_percentage >= 25.0:
        return (
            "Shopping is your largest expense. Try the 48-hour rule: leave non-essential items in your cart "
            "for 2 days before clicking checkout. Half the time, the urge fades!"
        )

    if biggest_category == "Entertainment" and biggest_percentage >= 25.0:
        return (
            "Entertainment is taking the biggest bite! Check for student discounts on streaming services, "
            "gyms, and local venues—always carry your student ID card."
        )

    if biggest_category == "Transport" and biggest_percentage >= 25.0:
        return (
            "Commuting is adding up. Check if your university or city offers subsidized student transit passes, "
            "metro cards, or carpooling groups."
        )

    if biggest_category == "Education" and biggest_percentage >= 30.0:
        return (
            "Investing in your education is great! Make sure to look for library copies, shared course packs, "
            "or free digital versions before buying full-price textbooks."
        )

    if savings_rate >= 30.0:
        return (
            f"Superb job saving {savings_rate}% of your money! Consider moving some of this into a separate "
            "emergency fund or a high-yield student account so you don't accidentally spend it."
        )

    if savings_rate > 0:
        return (
            "Good rhythm! Try setting aside your savings first on the day your allowance or paycheck arrives, "
            "rather than only saving what happens to be left at month-end."
        )

    return "Aim to save even just 5% to 10% of your incoming money every month to build financial confidence!"


def check_affordability(
    item_name: str,
    price: float,
    current_savings: float,
    monthly_savings: float,
) -> Dict[str, Any]:
    """
    Evaluates whether a student can afford a specific purchase.
    Returns remaining balance, a clear recommendation (Yes, Think Twice, Not Recommended),
    and student-tailored reasoning.
    """
    cleaned_name = item_name.strip() if item_name.strip() else "This item"
    price = max(0.0, float(price))
    current_savings = max(0.0, float(current_savings))
    monthly_savings = max(0.0, float(monthly_savings))

    remaining = current_savings - price

    # 1. Not Recommended: Can't afford it outright (would go into debt) or leaves zero safety
    if price > current_savings:
        shortfall = price - current_savings
        months_to_afford = (
            math.ceil(shortfall / monthly_savings) if monthly_savings > 0 else None
        )
        recommendation = "Not Recommended"
        badge_type = "danger"
        emoji = "🚫"

        if monthly_savings > 0 and months_to_afford:
            reasoning = (
                f"You are short by {shortfall:,.2f}. Buying '{cleaned_name}' right now would drain your account or require debt. "
                f"If you save {monthly_savings:,.2f}/mo, you can comfortably buy it in about {months_to_afford} month(s)!"
            )
        else:
            reasoning = (
                f"You are short by {shortfall:,.2f}. It's best to wait until your funds build up before purchasing '{cleaned_name}'."
            )

    # 2. Think Twice: You have the cash, but it wipes out over 60% of your buffer or leaves very little safety
    elif remaining < (current_savings * 0.3) or (monthly_savings > 0 and price > (monthly_savings * 3)):
        recommendation = "Think Twice"
        badge_type = "warning"
        emoji = "⚠️"
        percent_of_stash = round((price / current_savings) * 100, 1) if current_savings > 0 else 100

        months_to_replenish = (
            math.ceil(price / monthly_savings) if monthly_savings > 0 else None
        )

        replenish_text = (
            f" It will take approximately {months_to_replenish} month(s) of regular savings to rebuild this cash."
            if months_to_replenish
            else ""
        )

        reasoning = (
            f"'{cleaned_name}' takes {percent_of_stash}% of your total available cash, leaving you with only {remaining:,.2f}. "
            f"If an unexpected college fee or emergency happens, you might feel squeezed.{replenish_text}"
        )

    # 3. Yes: Comfortably within budget
    else:
        recommendation = "Yes"
        badge_type = "success"
        emoji = "🎉"
        percent_of_stash = round((price / current_savings) * 100, 1) if current_savings > 0 else 0

        reasoning = (
            f"Go for it! '{cleaned_name}' costs {percent_of_stash}% of your available money, "
            f"leaving you with a healthy cushion of {remaining:,.2f}."
        )

    return {
        "item_name": cleaned_name,
        "price": round(price, 2),
        "current_savings": round(current_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "remaining_after_purchase": round(remaining, 2),
        "recommendation": recommendation,
        "badge_type": badge_type,
        "emoji": emoji,
        "reasoning": reasoning,
    }


def calculate_savings_goal(
    goal_name: str,
    target_amount: float,
    current_saved: float,
    monthly_contribution: float,
) -> Dict[str, Any]:
    """
    Calculates progress percentage, remaining balance, and estimated months
    to reach a student savings milestone.
    """
    cleaned_name = goal_name.strip() if goal_name.strip() else "Savings Goal"
    target = max(0.0, float(target_amount))
    saved = max(0.0, float(current_saved))
    monthly = max(0.0, float(monthly_contribution))

    remaining = max(0.0, target - saved)

    if target > 0:
        progress_pct = min(100.0, round((saved / target) * 100.0, 1))
    else:
        progress_pct = 100.0 if saved >= 0 else 0.0

    is_achieved = saved >= target and target > 0

    if is_achieved:
        months_left = 0
        message = f"Congratulations! You've successfully reached your goal for '{cleaned_name}'! 🥳"
    elif remaining > 0 and monthly > 0:
        months_left = math.ceil(remaining / monthly)
        message = (
            f"At {monthly:,.2f}/month, you will reach '{cleaned_name}' in about {months_left} month"
            f"{'s' if months_left != 1 else ''}! Keep the streak going! 🚀"
        )
    elif monthly == 0:
        months_left = None
        message = "Set a monthly contribution to see your projected completion date."
    else:
        months_left = 0
        message = "You're all set!"

    return {
        "goal_name": cleaned_name,
        "target_amount": round(target, 2),
        "current_saved": round(saved, 2),
        "monthly_contribution": round(monthly, 2),
        "remaining_amount": round(remaining, 2),
        "progress_percentage": progress_pct,
        "estimated_months": months_left,
        "is_achieved": is_achieved,
        "message": message,
    }


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("MONEYY - Student Personal Finance Engine (CLI Mode)")
    print("Your money. Your choices.")
    print("=" * 60)
    sample = calculate_finances(
        allowance=10000,
        part_time=4000,
        scholarship=1000,
        food=4500,
        transport=1200,
        education=800,
        entertainment=1000,
        shopping=1200,
        other_expenses=500,
    )
    curr = "₹"
    try:
        print(f"Total Inflows:    {curr}{sample['total_income']:,.2f}")
        print(f"Total Spending:   {curr}{sample['total_spending']:,.2f}")
        print(f"Money Left:       {curr}{sample['money_left']:,.2f}")
        print(f"Savings Rate:     {sample['savings_rate']}%")
        print(f"Biggest Expense:  {sample['biggest_expense']['category']} ({curr}{sample['biggest_expense']['amount']:,.2f} - {sample['biggest_expense']['percentage']}%)")
        print(f"Financial Status: {sample['status']}")
        print(f"Money Tip:        {sample['tip']}")
        print("-" * 60)
        afford_test = check_affordability("Wireless Headphones", 3500, sample["money_left"], sample["money_left"])
        print(f"Afford Check:     {afford_test['item_name']} -> {afford_test['recommendation']}")
        print(f"Afford Reason:    {afford_test['reasoning']}")
    except UnicodeEncodeError:
        curr = "INR "
        print(f"Total Inflows:    {curr}{sample['total_income']:,.2f}")
        print(f"Total Spending:   {curr}{sample['total_spending']:,.2f}")
        print(f"Money Left:       {curr}{sample['money_left']:,.2f}")
        print(f"Savings Rate:     {sample['savings_rate']}%")
        print(f"Biggest Expense:  {sample['biggest_expense']['category']} ({curr}{sample['biggest_expense']['amount']:,.2f} - {sample['biggest_expense']['percentage']}%)")
        print(f"Financial Status: {sample['status']}")
        print(f"Money Tip:        {sample['tip']}")
        print("-" * 60)
        afford_test = check_affordability("Wireless Headphones", 3500, sample["money_left"], sample["money_left"])
        print(f"Afford Check:     {afford_test['item_name']} -> {afford_test['recommendation']}")
        print(f"Afford Reason:    {afford_test['reasoning']}")
    print("=" * 60)


