# MONEYY 💸
> **Your money. Your choices.**
> *A simple, aesthetic personal money tracker for students from Class 12 to postgraduate level.*

---

## ✨ Overview

**MONEYY** is a modern, student-focused personal finance app built with Python (Flask + standard library SQLite). Designed with a clean, minimal, premium Gen-Z fintech aesthetic (lavender accents, rounded cards, large bold numbers, plenty of whitespace, and friendly micro-copy), it tracks all your incoming and outgoing money with zero complicated accounting jargon.

Everything in the app is built on a solid **transaction-first foundation**: all balances, monthly spend, savings rates, category breakdowns, budgets, and automated insights are calculated in real time directly from your transaction ledger. Data is stored locally in `moneyy.db` so all records persist when reopening the app.

---

## 🚀 Core Features

### 1. 🏠 Home / Dashboard
- **Current Balance**: All-time cash cushion (`Total Income - Total Expenses`).
- **Monthly Income & Expenses**: Inflows and outflows for the selected month.
- **Monthly Savings**: Remaining cash cushion with an instant **Savings % Badge**.
- **Spending Breakdown by Category**: Visual percentage bars and totals with category emojis.
- **Recent Transactions**: Quick ledger preview with one-tap navigation to the full ledger.
- **Simple Money Insights Banner**: Dynamic micro-insights like *"Your wallet is looking healthy 👀"* or *"Watch that Food spend 🎯"*.

### 2. ➕ Add Transaction
- **Type Toggle**: Effortlessly switch between `💸 Income` and `🛍️ Expense`.
- **Amount Input**: Supports quick-add pills (`+50`, `+100`, `+500`, `+1k`, `+2k`).
- **Income Categories**:
  - `Allowance`, `Salary/Stipend`, `Scholarship`, `Freelance`, `Gifts`, `Other`
- **Expense Categories**:
  - `Food`, `Transport`, `Housing`, `Education`, `Shopping`, `Entertainment`, `Health`, `Bills/Subscriptions`, `Travel`, `Family`, `Other`
- **Payment Methods**:
  - `UPI`, `Cash`, `Debit Card`, `Credit Card`, `Bank Transfer`, `Other`
- **Details**: Description, Date picker (defaults to today), and optional Note.

### 3. 💳 Transactions Ledger
- **Complete Transaction History**: View every transaction with emoji avatars, tags, and dates.
- **Live Search**: Instant search by description, category, or note.
- **Multi-Filters**: Filter by Income / Expense, specific category, or month.
- **Edit & Delete**: Edit any transaction in a pre-filled modal or delete with confirmation.
- **Net Calculation**: Shows real-time net total for any filtered selection.

### 4. 📊 Budgets & Limits
- **Overall Monthly Spending Limit**: Hero card with visual progress bar and alert badges.
- **Category Budgets**: Set dedicated monthly caps for `Food`, `Shopping`, `Entertainment`, etc.
- **Smart Warning Thresholds**:
  - 🟢 **Healthy** (`< 80%`): *"Looking good! ₹X remaining."*
  - ⚠️ **Close to Budget** (`80% - 99%`): *"Warning: Used X% with ₹Y left."*
  - 🚨 **Exceeded** (`>= 100%`): *"Exceeded budget by ₹Z! Pump the brakes."*

### 5. 🎯 Savings Goals
- **Student Goal Presets**: One-click creation for `💻 Laptop`, `🏖️ Trip`, `🛡️ Emergency Fund`, `📱 Phone`, or Custom goals.
- **Progress Tracking**: Animated progress bar, amount saved, target amount, and remaining funds needed.
- **Time to Goal ETA**: Calculates estimated months to reach each goal based on current monthly savings rate.
- **Quick Deposit**: Add funds directly to any savings goal anytime.

### 6. 💡 Financial Insights
- **Biggest Expense Category**: Pinpoints the top spending driver and its % share.
- **Average Daily Spending**: Real daily burn rate calculated for the current month.
- **Savings Rate**: Evaluates your financial discipline against student benchmarks.
- **Spending Compared with Previous Month**: Month-on-month comparison with delta amount, % change, and bar comparison.
- **Highest Spending Day**: Identifies the single date with the highest total expense and top purchase.
- **Spending Trends**: Daily timeline bar chart showing spending spikes.
- **Student Money Playbook**: Actionable advice tailored to your largest spending categories.

### 7. 🤔 Can I Afford It?
- **Reality Check Simulator**: Enter an item name and price.
- **Auto-Syncs Balance**: Automatically reads your live cash balance (or lets you adjust manually).
- **Instant Verdict**:
  - 🎉 `LOOKS GOOD`: Leaves a healthy cushion.
  - ⚠️ `THINK TWICE`: Takes `>50%` of funds or leaves low emergency cushion.
  - 🚫 `NOT RECOMMENDED`: Exceeds available balance (debt/overdraft).
- **Friendly Context**: Explains the math and gives smart student alternatives.

---

## 🎨 Design & Aesthetic

- **Color Palette**:
  - Off-white background: `#F8F9FD`
  - Dark readable typography: `#0F172A`
  - Lavender / purple accents: `#7C3AED` & `#8B5CF6`
  - Soft lilac surfaces: `#EDE9FE` & `#F5F3FF`
- **UI Details**:
  - 20px+ rounded cards with soft floating shadows
  - Large bold numbers with tabular figures for currency
  - Clean currency selector: **₹ (INR)**, **$ (USD)**, **€ (EUR)**, **£ (GBP)**
  - Responsive design with sticky bottom navigation on mobile devices
  - Friendly Gen-Z student microcopy:
    - *"Your money, decoded."*
    - *"Where did your money go?"*
    - *"Money in. Money out. No drama."*
    - *"Your wallet is looking healthy 👀"*

---

## 📁 Project Architecture

```
moneyy/
├── app.py                  # Flask server and RESTful JSON API endpoints
├── database.py             # SQLite persistence layer (transactions, budgets, goals)
├── finance_engine.py       # Pure Python financial logic, budgets, insights, afford engine
├── test_moneyy.py          # Unit test suite (11 tests covering all calculations & edge cases)
├── verify_app.py           # Integration test verifying all 12 API endpoints
├── requirements.txt        # Flask dependency
├── templates/
│   └── index.html          # Semantic, responsive single-page application
└── static/
    ├── css/
    │   └── style.css       # Clean Gen-Z fintech theme (lavender, rounded cards)
    └── js/
        └── app.js          # Client controller, search, filters, modals, async API calls
```

---

## 🛠️ How to Run

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the App
```bash
python app.py
```

### Step 3: Open in Browser
Open your browser and visit:
```
http://127.0.0.1:5000/
```

> **Note**: Demo data is automatically pre-seeded on first run so the dashboard is immediately populated. You can reset or reload demo data anytime using the ⚙️ settings icon in the top right.

---

## 🧪 Running Automated Tests

Run the complete unit test suite:
```bash
python test_moneyy.py
```

Run the API integration verification test:
```bash
python verify_app.py
```
