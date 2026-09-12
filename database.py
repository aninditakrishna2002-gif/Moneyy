"""
database.py - SQLite Database Storage & Persistence Layer for MONEYY
Pure Python, standard library sqlite3 (zero external database dependencies).
"""

import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moneyy.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates a database connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes tables if they do not exist."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()

            # 1. Transactions Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # 2. Budgets Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL UNIQUE,
                    monthly_amount REAL NOT NULL CHECK(monthly_amount > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # 3. Savings Goals Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL CHECK(target_amount > 0),
                    saved_amount REAL NOT NULL DEFAULT 0.0 CHECK(saved_amount >= 0),
                    category_type TEXT NOT NULL DEFAULT 'Custom',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
    finally:
        conn.close()


# ==========================================
# TRANSACTION CRUD OPERATIONS
# ==========================================

def add_transaction(
    trans_type: str,
    amount: float,
    category: str,
    description: str,
    trans_date: str,
    payment_method: str,
    note: str = "",
    db_path: str = DB_PATH,
) -> int:
    """Inserts a new transaction."""
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if trans_type not in ("Income", "Expense"):
        raise ValueError("Type must be Income or Expense")
    if not description.strip():
        description = category

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (type, amount, category, description, date, payment_method, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (trans_type, float(amount), category.strip(), description.strip(), trans_date, payment_method.strip(), note.strip()),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_transaction(trans_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single transaction by ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (trans_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_transaction(
    trans_id: int,
    trans_type: str,
    amount: float,
    category: str,
    description: str,
    trans_date: str,
    payment_method: str,
    note: str = "",
    db_path: str = DB_PATH,
) -> bool:
    """Updates an existing transaction."""
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if trans_type not in ("Income", "Expense"):
        raise ValueError("Type must be Income or Expense")

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transactions
                SET type = ?, amount = ?, category = ?, description = ?, date = ?, payment_method = ?, note = ?
                WHERE id = ?
                """,
                (trans_type, float(amount), category.strip(), description.strip(), trans_date, payment_method.strip(), note.strip(), trans_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_transaction(trans_id: int, db_path: str = DB_PATH) -> bool:
    """Deletes a transaction by ID."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_transactions(
    trans_type: Optional[str] = None,
    category: Optional[str] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Retrieves transactions with optional filtering by type, category, month (YYYY-MM), or search query.
    Ordered by date DESC, id DESC.
    """
    query = "SELECT * FROM transactions WHERE 1=1"
    params: List[Any] = []

    if trans_type and trans_type != "All":
        query += " AND type = ?"
        params.append(trans_type)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if month and month != "All":
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    if search:
        query += " AND (description LIKE ? OR note LIKE ? OR category LIKE ?)"
        like_term = f"%{search.strip()}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY date DESC, id DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_time_transactions(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all transactions without any limits or filters."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


# ==========================================
# BUDGET CRUD OPERATIONS
# ==========================================

def set_budget(category: str, monthly_amount: float, db_path: str = DB_PATH) -> int:
    """Creates or updates a monthly budget for a category (or 'Overall')."""
    if monthly_amount <= 0:
        raise ValueError("Budget amount must be greater than 0")

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO budgets (category, monthly_amount)
                VALUES (?, ?)
                ON CONFLICT(category) DO UPDATE SET monthly_amount = excluded.monthly_amount
                """,
                (category.strip(), float(monthly_amount)),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_budgets(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all set budgets."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets ORDER BY CASE WHEN category = 'Overall' THEN 0 ELSE 1 END, category ASC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def delete_budget(budget_id: int, db_path: str = DB_PATH) -> bool:
    """Deletes a budget entry."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# SAVINGS GOALS CRUD OPERATIONS
# ==========================================

def add_savings_goal(
    name: str,
    target_amount: float,
    saved_amount: float = 0.0,
    category_type: str = "Custom",
    db_path: str = DB_PATH,
) -> int:
    """Adds a new savings goal."""
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than 0")
    if saved_amount < 0:
        saved_amount = 0.0

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO savings_goals (name, target_amount, saved_amount, category_type)
                VALUES (?, ?, ?, ?)
                """,
                (name.strip(), float(target_amount), float(saved_amount), category_type.strip()),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_savings_goals(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all savings goals."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings_goals ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def update_savings_goal(
    goal_id: int,
    name: str,
    target_amount: float,
    saved_amount: float,
    category_type: str,
    db_path: str = DB_PATH,
) -> bool:
    """Updates a savings goal."""
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than 0")
    if saved_amount < 0:
        saved_amount = 0.0

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE savings_goals
                SET name = ?, target_amount = ?, saved_amount = ?, category_type = ?
                WHERE id = ?
                """,
                (name.strip(), float(target_amount), float(saved_amount), category_type.strip(), goal_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def deposit_to_savings_goal(goal_id: int, amount: float, db_path: str = DB_PATH) -> bool:
    """Adds money to an existing savings goal."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE savings_goals
                SET saved_amount = MAX(0.0, saved_amount + ?)
                WHERE id = ?
                """,
                (float(amount), goal_id),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_savings_goal(goal_id: int, db_path: str = DB_PATH) -> bool:
    """Deletes a savings goal."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# DEMO DATA SEEDING & RESET
# ==========================================

def clear_all_data(db_path: str = DB_PATH) -> None:
    """Clears all transactions, budgets, and savings goals."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM budgets")
            cursor.execute("DELETE FROM savings_goals")
    finally:
        conn.close()


def seed_demo_data(db_path: str = DB_PATH, force: bool = False) -> None:
    """
    Seeds realistic student transactions, budgets, and savings goals.
    Only runs if transactions table is empty unless force=True.
    """
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        if count > 0 and not force:
            return  # Already has data
    finally:
        conn.close()

    if force:
        clear_all_data(db_path)

    # Use current month and previous month for dynamic dates
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
        # Current Month Income
        ("Income", 12000.0, "Allowance", "Monthly pocket money from parents", d(1, 0), "Bank Transfer", "Monthly budget transfer"),
        ("Income", 4500.0, "Freelance", "Front-end design freelance project", d(5, 0), "UPI", "Client payment"),
        ("Income", 1000.0, "Gifts", "Birthday gift from grandparents", d(8, 0), "Cash", "Cash in envelope"),

        # Current Month Expenses
        ("Expense", 350.0, "Food", "Campus cafe coffee & muffin", d(2, 0), "UPI", "Study session with classmates"),
        ("Expense", 1200.0, "Education", "Data structures & AI textbook", d(3, 0), "Debit Card", "College bookstore"),
        ("Expense", 420.0, "Transport", "Weekly metro rail card recharge", d(4, 0), "UPI", "Student concession pass"),
        ("Expense", 1890.0, "Food", "Dinner with campus friends at pizzeria", d(6, 0), "UPI", "Split bill with 4 friends"),
        ("Expense", 699.0, "Bills/Subscriptions", "Spotify & Netflix student pack", d(7, 0), "Debit Card", "Auto-renewal"),
        ("Expense", 1450.0, "Shopping", "Gym hoodie & water bottle", d(9, 0), "Credit Card", "Campus sports shop"),
        ("Expense", 320.0, "Entertainment", "Weekend movie ticket", d(10, 0), "UPI", "Student discount"),
        ("Expense", 450.0, "Transport", "Cab ride to railway station", d(11, 0), "UPI", "Late night commute"),
        ("Expense", 680.0, "Food", "Groceries & midnight snack supplies", d(12, 0), "UPI", "Supermarket run"),

        # Previous Month Transactions
        ("Income", 12000.0, "Allowance", "Monthly pocket money", d(1, -1), "Bank Transfer", ""),
        ("Income", 3000.0, "Salary/Stipend", "Campus lab assistant stipend", d(6, -1), "Bank Transfer", ""),
        ("Expense", 3800.0, "Food", "Monthly food & mess spend", d(5, -1), "UPI", "Various meals"),
        ("Expense", 1500.0, "Transport", "Monthly travel & metro", d(10, -1), "UPI", "Transit pass"),
        ("Expense", 2200.0, "Shopping", "Semester college bag & shoes", d(15, -1), "Credit Card", "Sale discount"),
        ("Expense", 999.0, "Bills/Subscriptions", "Annual domain & cloud hosting", d(20, -1), "Debit Card", "Portfolio website"),
        ("Expense", 1100.0, "Entertainment", "Weekend concert with batchmates", d(25, -1), "Cash", "Festival tickets"),
    ]

    for t in sample_transactions:
        add_transaction(t[0], t[1], t[2], t[3], t[4], t[5], t[6], db_path=db_path)

    set_budget("Overall", 10000.0, db_path=db_path)
    set_budget("Food", 4000.0, db_path=db_path)
    set_budget("Shopping", 2500.0, db_path=db_path)
    set_budget("Entertainment", 1500.0, db_path=db_path)
    set_budget("Transport", 1200.0, db_path=db_path)

    add_savings_goal("MacBook Air for Coding", 75000.0, 32000.0, "Laptop", db_path=db_path)
    add_savings_goal("Graduation Trip to Mountains", 18000.0, 11500.0, "Trip", db_path=db_path)
    add_savings_goal("Rainy Day Emergency Fund", 15000.0, 9000.0, "Emergency Fund", db_path=db_path)
