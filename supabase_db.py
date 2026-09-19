"""
supabase_db.py - Supabase PostgreSQL Storage Layer for MONEYY
Replaces SQLite database operations with Supabase PostgreSQL calls.
Enforces user isolation via user_id and Row Level Security (RLS).
"""

from typing import List, Dict, Any, Optional
from datetime import date
import supabase_client as sc


def _get_client(access_token: Optional[str] = None):
    """Returns the authenticated user client if access_token is provided, else admin client."""
    if access_token:
        return sc.get_user_client(access_token)
    return sc.get_admin_client()


# ==============================================================================
# TRANSACTIONS CRUD
# ==============================================================================

def add_transaction(
    user_id: str,
    trans_type: str,
    amount: float,
    category: str,
    description: str,
    trans_date: str,
    payment_method: str,
    note: str = "",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Inserts a new transaction for the user."""
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if trans_type not in ("Income", "Expense"):
        raise ValueError("Type must be Income or Expense")

    client = _get_client(access_token)
    payload = {
        "user_id": user_id,
        "type": trans_type,
        "amount": float(amount),
        "category": category.strip(),
        "description": description.strip() if description.strip() else category.strip(),
        "date": trans_date,
        "payment_method": payment_method.strip(),
        "note": note.strip() if note else "",
    }
    res = client.table("transactions").insert(payload).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    raise RuntimeError("Failed to insert transaction into Supabase.")


def get_transaction(
    trans_id: str,
    user_id: str,
    access_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fetches a single transaction for the user."""
    client = _get_client(access_token)
    res = (
        client.table("transactions")
        .select("*")
        .eq("id", str(trans_id))
        .eq("user_id", user_id)
        .execute()
    )
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None


def update_transaction(
    trans_id: str,
    user_id: str,
    trans_type: str,
    amount: float,
    category: str,
    description: str,
    trans_date: str,
    payment_method: str,
    note: str = "",
    access_token: Optional[str] = None,
) -> bool:
    """Updates an existing transaction belonging to the user."""
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if trans_type not in ("Income", "Expense"):
        raise ValueError("Type must be Income or Expense")

    client = _get_client(access_token)
    payload = {
        "type": trans_type,
        "amount": float(amount),
        "category": category.strip(),
        "description": description.strip() if description.strip() else category.strip(),
        "date": trans_date,
        "payment_method": payment_method.strip(),
        "note": note.strip() if note else "",
    }
    res = (
        client.table("transactions")
        .update(payload)
        .eq("id", str(trans_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data and len(res.data) > 0)


def delete_transaction(
    trans_id: str,
    user_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """Deletes a transaction belonging to the user."""
    client = _get_client(access_token)
    res = (
        client.table("transactions")
        .delete()
        .eq("id", str(trans_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data and len(res.data) > 0)


def get_transactions(
    user_id: str,
    trans_type: Optional[str] = None,
    category: Optional[str] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves filtered transactions belonging to the user.
    """
    client = _get_client(access_token)
    query = (
        client.table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .order("created_at", desc=True)
    )

    if trans_type and trans_type != "All":
        query = query.eq("type", trans_type)

    if category and category != "All":
        query = query.eq("category", category)

    if month and month != "All":
        # Format month YYYY-MM
        start_date = f"{month}-01"
        # Supabase allows gte / lte or like
        next_m_parts = month.split("-")
        y = int(next_m_parts[0])
        m = int(next_m_parts[1]) + 1
        if m > 12:
            m = 1
            y += 1
        end_date = f"{y:04d}-{m:02d}-01"
        query = query.gte("date", start_date).lt("date", end_date)

    if limit:
        query = query.limit(limit)

    res = query.execute()
    records = res.data or []

    # Perform text search in memory if requested (handles partial description/note)
    if search and search.strip():
        s = search.strip().lower()
        records = [
            r for r in records
            if s in (r.get("description") or "").lower()
            or s in (r.get("category") or "").lower()
            or s in (r.get("note") or "").lower()
        ]

    # Convert numeric amount to float for consistent calculation
    for r in records:
        r["amount"] = float(r["amount"])

    return records


def get_all_time_transactions(
    user_id: str,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches all transactions for the user."""
    return get_transactions(user_id=user_id, access_token=access_token)


# ==============================================================================
# BUDGETS CRUD
# ==============================================================================

def set_budget(
    user_id: str,
    category: str,
    monthly_amount: float,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Sets or updates a monthly budget for a category (or 'Overall')."""
    if monthly_amount <= 0:
        raise ValueError("Budget amount must be greater than 0")

    client = _get_client(access_token)
    payload = {
        "user_id": user_id,
        "category": category.strip(),
        "monthly_amount": float(monthly_amount),
    }
    # Upsert based on unique constraint (user_id, category)
    res = (
        client.table("budgets")
        .upsert(payload, on_conflict="user_id,category")
        .execute()
    )
    if res.data and len(res.data) > 0:
        res.data[0]["monthly_amount"] = float(res.data[0]["monthly_amount"])
        return res.data[0]
    raise RuntimeError("Failed to set budget in Supabase.")


def get_budgets(
    user_id: str,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches all budgets set by the user."""
    client = _get_client(access_token)
    res = (
        client.table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    records = res.data or []
    for r in records:
        r["monthly_amount"] = float(r["monthly_amount"])

    # Sort 'Overall' first
    records.sort(key=lambda b: 0 if b.get("category") == "Overall" else 1)
    return records


def delete_budget(
    budget_id: str,
    user_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """Deletes a budget belonging to the user."""
    client = _get_client(access_token)
    res = (
        client.table("budgets")
        .delete()
        .eq("id", str(budget_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data and len(res.data) > 0)


# ==============================================================================
# SAVINGS GOALS CRUD
# ==============================================================================

def add_savings_goal(
    user_id: str,
    name: str,
    target_amount: float,
    saved_amount: float = 0.0,
    category_type: str = "Custom",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Adds a new savings goal for the user."""
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than 0")

    client = _get_client(access_token)
    payload = {
        "user_id": user_id,
        "name": name.strip(),
        "target_amount": float(target_amount),
        "saved_amount": float(max(0.0, saved_amount)),
        "category_type": category_type.strip(),
    }
    res = client.table("savings_goals").insert(payload).execute()
    if res.data and len(res.data) > 0:
        res.data[0]["target_amount"] = float(res.data[0]["target_amount"])
        res.data[0]["saved_amount"] = float(res.data[0]["saved_amount"])
        return res.data[0]
    raise RuntimeError("Failed to add savings goal in Supabase.")


def get_savings_goals(
    user_id: str,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches all savings goals for the user."""
    client = _get_client(access_token)
    res = (
        client.table("savings_goals")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    records = res.data or []
    for r in records:
        r["target_amount"] = float(r["target_amount"])
        r["saved_amount"] = float(r["saved_amount"])
    return records


def update_savings_goal(
    goal_id: str,
    user_id: str,
    name: str,
    target_amount: float,
    saved_amount: float,
    category_type: str,
    access_token: Optional[str] = None,
) -> bool:
    """Updates a savings goal belonging to the user."""
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than 0")

    client = _get_client(access_token)
    payload = {
        "name": name.strip(),
        "target_amount": float(target_amount),
        "saved_amount": float(max(0.0, saved_amount)),
        "category_type": category_type.strip(),
    }
    res = (
        client.table("savings_goals")
        .update(payload)
        .eq("id", str(goal_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data and len(res.data) > 0)


def deposit_to_savings_goal(
    goal_id: str,
    user_id: str,
    amount: float,
    access_token: Optional[str] = None,
) -> bool:
    """Deposits funds into an existing savings goal."""
    if amount <= 0:
        raise ValueError("Deposit amount must be greater than 0")

    client = _get_client(access_token)
    res = (
        client.table("savings_goals")
        .select("saved_amount")
        .eq("id", str(goal_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data or len(res.data) == 0:
        return False

    current_saved = float(res.data[0]["saved_amount"])
    new_saved = current_saved + float(amount)

    update_res = (
        client.table("savings_goals")
        .update({"saved_amount": new_saved})
        .eq("id", str(goal_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(update_res.data and len(update_res.data) > 0)


def delete_savings_goal(
    goal_id: str,
    user_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """Deletes a savings goal belonging to the user."""
    client = _get_client(access_token)
    res = (
        client.table("savings_goals")
        .delete()
        .eq("id", str(goal_id))
        .eq("user_id", user_id)
        .execute()
    )
    return bool(res.data and len(res.data) > 0)


# ==============================================================================
# DEMO SEED & RESET (PER USER)
# ==============================================================================

def clear_user_data(user_id: str, access_token: Optional[str] = None) -> None:
    """Clears all records belonging strictly to the specified user."""
    client = _get_client(access_token)
    client.table("transactions").delete().eq("user_id", user_id).execute()
    client.table("budgets").delete().eq("user_id", user_id).execute()
    client.table("savings_goals").delete().eq("user_id", user_id).execute()


def seed_user_demo_data(user_id: str, access_token: Optional[str] = None, force: bool = False) -> None:
    """
    Seeds realistic student transactions, budgets, and savings goals
    isolated to the authenticated user's account.
    """
    client = _get_client(access_token)
    existing = client.table("transactions").select("id").eq("user_id", user_id).limit(1).execute()
    if existing.data and len(existing.data) > 0 and not force:
        return

    if force:
        clear_user_data(user_id, access_token)

    today = date.today()
    curr_year = today.year
    curr_month = today.month

    def d(day: int, month_offset: int = 0) -> str:
        m = curr_month + month_offset
        y = curr_year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        clamped_day = min(day, 28)
        return f"{y:04d}-{m:02d}-{clamped_day:02d}"

    sample_transactions = [
        ("Income", 12000.0, "Allowance", "Monthly pocket money from parents", d(1, 0), "Bank Transfer", "Monthly budget transfer"),
        ("Income", 4500.0, "Freelance", "Front-end design freelance project", d(5, 0), "UPI", "Client payment"),
        ("Income", 1000.0, "Gifts", "Birthday gift from grandparents", d(8, 0), "Cash", "Cash in envelope"),

        ("Expense", 350.0, "Food", "Campus cafe coffee & muffin", d(2, 0), "UPI", "Study session with classmates"),
        ("Expense", 1200.0, "Education", "Data structures & AI textbook", d(3, 0), "Debit Card", "College bookstore"),
        ("Expense", 420.0, "Transport", "Weekly metro rail card recharge", d(4, 0), "UPI", "Student concession pass"),
        ("Expense", 1890.0, "Food", "Dinner with campus friends at pizzeria", d(6, 0), "UPI", "Split bill with 4 friends"),
        ("Expense", 699.0, "Bills/Subscriptions", "Spotify & Netflix student pack", d(7, 0), "Debit Card", "Auto-renewal"),
        ("Expense", 1450.0, "Shopping", "Gym hoodie & water bottle", d(9, 0), "Credit Card", "Campus sports shop"),
        ("Expense", 320.0, "Entertainment", "Weekend movie ticket", d(10, 0), "UPI", "Student discount"),
        ("Expense", 450.0, "Transport", "Cab ride to railway station", d(11, 0), "UPI", "Late night commute"),
        ("Expense", 680.0, "Food", "Groceries & midnight snack supplies", d(12, 0), "UPI", "Supermarket run"),

        ("Income", 12000.0, "Allowance", "Monthly pocket money", d(1, -1), "Bank Transfer", ""),
        ("Income", 3000.0, "Salary/Stipend", "Campus lab assistant stipend", d(6, -1), "Bank Transfer", ""),
        ("Expense", 3800.0, "Food", "Monthly food & mess spend", d(5, -1), "UPI", "Various meals"),
        ("Expense", 1500.0, "Transport", "Monthly travel & metro", d(10, -1), "UPI", "Transit pass"),
        ("Expense", 2200.0, "Shopping", "Semester college bag & shoes", d(15, -1), "Credit Card", "Sale discount"),
        ("Expense", 999.0, "Bills/Subscriptions", "Annual domain & cloud hosting", d(20, -1), "Debit Card", "Portfolio website"),
        ("Expense", 1100.0, "Entertainment", "Weekend concert with batchmates", d(25, -1), "Cash", "Festival tickets"),
    ]

    for t in sample_transactions:
        add_transaction(
            user_id=user_id,
            trans_type=t[0],
            amount=t[1],
            category=t[2],
            description=t[3],
            trans_date=t[4],
            payment_method=t[5],
            note=t[6],
            access_token=access_token,
        )

    set_budget(user_id=user_id, category="Overall", monthly_amount=10000.0, access_token=access_token)
    set_budget(user_id=user_id, category="Food", monthly_amount=4000.0, access_token=access_token)
    set_budget(user_id=user_id, category="Shopping", monthly_amount=2500.0, access_token=access_token)
    set_budget(user_id=user_id, category="Entertainment", monthly_amount=1500.0, access_token=access_token)
    set_budget(user_id=user_id, category="Transport", monthly_amount=1200.0, access_token=access_token)

    add_savings_goal(user_id=user_id, name="MacBook Air for Coding", target_amount=75000.0, saved_amount=32000.0, category_type="Laptop", access_token=access_token)
    add_savings_goal(user_id=user_id, name="Graduation Trip to Mountains", target_amount=18000.0, saved_amount=11500.0, category_type="Trip", access_token=access_token)
    add_savings_goal(user_id=user_id, name="Rainy Day Emergency Fund", target_amount=15000.0, saved_amount=9000.0, category_type="Emergency Fund", access_token=access_token)


# ==============================================================================
# CUSTOM CATEGORIES
# ==============================================================================

# In-memory fallback in case public.categories table migration is pending in Supabase
_local_categories_cache: Dict[str, List[Dict[str, Any]]] = {}


def get_custom_categories(
    user_id: str,
    trans_type: Optional[str] = None,
    access_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches all custom categories created by the authenticated user.
    Optionally filters by trans_type ('Income' or 'Expense').
    """
    cats = []
    try:
        client = _get_client(access_token)
        query = client.table("categories").select("*").eq("user_id", user_id)
        if trans_type:
            query = query.eq("category_type", trans_type)
        res = query.order("category_name").execute()
        if res.data is not None:
            cats = res.data
    except Exception:
        pass

    if not cats:
        # Fallback to local session cache if table is pending creation or in mock test
        user_cats = _local_categories_cache.get(user_id, [])
        if trans_type:
            cats = [c for c in user_cats if c["category_type"] == trans_type]
        else:
            cats = list(user_cats)

    # Ensure emoji key is always populated
    for c in cats:
        if not c.get("emoji"):
            c["emoji"] = "🏷️"

    return cats


def add_custom_category(
    user_id: str,
    category_name: str,
    category_type: str,
    emoji: str = "🏷️",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inserts a new custom category with emoji for the user in Supabase.
    """
    name = category_name.strip()
    if not name:
        raise ValueError("Category name cannot be empty.")
    if category_type not in ("Income", "Expense"):
        raise ValueError("Category type must be either 'Income' or 'Expense'.")

    category_emoji = emoji.strip() if emoji and emoji.strip() else "🏷️"

    # Check duplicates in existing custom categories
    existing = get_custom_categories(user_id, category_type, access_token)
    if any(c["category_name"].lower() == name.lower() for c in existing):
        raise ValueError(f"Category '{name}' already exists for {category_type}.")

    payload = {
        "user_id": user_id,
        "category_name": name,
        "category_type": category_type,
        "emoji": category_emoji,
    }

    try:
        client = _get_client(access_token)
        res = client.table("categories").insert(payload).execute()
        if res.data and len(res.data) > 0:
            item = res.data[0]
            if not item.get("emoji"):
                item["emoji"] = category_emoji
            return item
    except Exception:
        import uuid
        fallback_item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "category_name": name,
            "category_type": category_type,
            "emoji": category_emoji,
        }
        if user_id not in _local_categories_cache:
            _local_categories_cache[user_id] = []
        _local_categories_cache[user_id].append(fallback_item)
        return fallback_item

    raise RuntimeError("Failed to insert category into Supabase.")


def delete_custom_category(
    user_id: str,
    category_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """
    Deletes a custom category belonging to the user.
    Historical transactions using this category are kept intact.
    """
    cat_identifier = str(category_id).strip()

    # 1. Delete from local cache
    if user_id in _local_categories_cache:
        _local_categories_cache[user_id] = [
            c for c in _local_categories_cache[user_id]
            if str(c.get("id")) != cat_identifier and c.get("category_name") != cat_identifier
        ]

    # 2. Delete from Supabase
    try:
        client = _get_client(access_token)
        # Attempt delete by id
        client.table("categories").delete().eq("user_id", user_id).eq("id", cat_identifier).execute()
    except Exception:
        try:
            # If id didn't match UUID format, attempt delete by category_name
            client = _get_client(access_token)
            client.table("categories").delete().eq("user_id", user_id).eq("category_name", cat_identifier).execute()
        except Exception:
            pass

    return True


