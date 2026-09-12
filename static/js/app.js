/**
 * app.js - Frontend Application Controller for MONEYY
 * Tagline: "Your money. Your choices."
 * Modern Gen-Z personal finance tracker for students.
 */

(function () {
  'use strict';

  // ==========================================
  // GLOBAL STATE
  // ==========================================
  const state = {
    activeTab: 'dashboard',
    currentMonth: '',
    currency: localStorage.getItem('moneyy_currency') || '₹',
    meta: {
      income_categories: [],
      expense_categories: [],
      payment_methods: [],
      category_emojis: {},
      current_month: '',
    },
    filterType: 'All',
    filterCategory: 'All',
    searchQuery: '',
    transactions: [],
    dashboard: null,
    pendingDelete: null, // { type: 'transaction'|'budget'|'goal', id: number, label: string }
  };

  // ==========================================
  // DOM ELEMENT SELECTORS
  // ==========================================
  const dom = {
    // Navigation & Global Controls
    navTabs: document.querySelectorAll('.nav-tab'),
    mobileNavTabs: document.querySelectorAll('.mobile-nav-tab'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    globalMonthSelect: document.getElementById('global-month-select'),
    globalCurrencySelect: document.getElementById('global-currency-select'),
    settingsToggle: document.getElementById('btn-settings-toggle'),
    settingsDropdown: document.getElementById('settings-dropdown'),
    reloadDemoBtn: document.getElementById('btn-reload-demo'),
    clearAllBtn: document.getElementById('btn-clear-all-data'),
    logoHomeBtn: document.getElementById('logo-home-btn'),

    // Global Add Transaction Buttons
    openAddModalBtn: document.getElementById('btn-open-add-modal'),
    mobileAddModalBtn: document.getElementById('btn-mobile-add-modal'),
    txnsAddModalBtn: document.getElementById('btn-txns-add-modal'),

    // Dashboard Elements
    dashInsightBadge: document.getElementById('dash-insight-badge'),
    dashInsightIcon: document.getElementById('dash-insight-icon'),
    dashInsightTitle: document.getElementById('dash-insight-title'),
    dashInsightMessage: document.getElementById('dash-insight-message'),
    dashCurrentBalance: document.getElementById('dash-current-balance'),
    dashMonthlyIncome: document.getElementById('dash-monthly-income'),
    dashMonthlyExpenses: document.getElementById('dash-monthly-expenses'),
    dashMonthlySavings: document.getElementById('dash-monthly-savings'),
    dashSavingsPct: document.getElementById('dash-savings-percentage'),
    dashIncomeCount: document.getElementById('dash-income-count'),
    dashExpenseCount: document.getElementById('dash-expense-count'),
    dashBreakdownContainer: document.getElementById('dash-breakdown-container'),
    dashRecentTxnsContainer: document.getElementById('dash-recent-txns-container'),
    dashViewBudgetsBtn: document.getElementById('dash-view-budgets-btn'),
    dashViewAllTxnsBtn: document.getElementById('dash-view-all-txns-btn'),
    dashQuickAffordBtn: document.getElementById('dash-quick-afford-btn'),

    // Transactions Elements
    txnSearchInput: document.getElementById('txn-search-input'),
    txnSearchClear: document.getElementById('txn-search-clear'),
    txnTypeFilter: document.getElementById('txn-type-filter'),
    txnCategoryFilter: document.getElementById('txn-category-filter'),
    btnResetFilters: document.getElementById('btn-reset-filters'),
    txnsCountBadge: document.getElementById('txns-count-badge'),
    txnsNetBadge: document.getElementById('txns-net-badge'),
    txnsListContainer: document.getElementById('txns-list-container'),

    // Budgets Elements
    btnOpenBudgetModal: document.getElementById('btn-open-budget-modal'),
    btnEditOverallBudget: document.getElementById('btn-edit-overall-budget'),
    budgetOverallSpent: document.getElementById('budget-overall-spent'),
    budgetOverallTarget: document.getElementById('budget-overall-target'),
    budgetOverallRemaining: document.getElementById('budget-overall-remaining'),
    budgetOverallBar: document.getElementById('budget-overall-bar'),
    budgetOverallWarning: document.getElementById('budget-overall-warning'),
    budgetOverallWarningText: document.getElementById('budget-overall-warning-text'),
    budgetOverallPct: document.getElementById('budget-overall-pct'),
    categoryBudgetsContainer: document.getElementById('category-budgets-container'),

    // Goals Elements
    btnOpenGoalModal: document.getElementById('btn-open-goal-modal'),
    goalsContainer: document.getElementById('goals-container'),
    goalPresetPills: document.querySelectorAll('.goal-preset-pill'),

    // Insights Elements
    insightTopCatName: document.getElementById('insight-top-cat-name'),
    insightTopCatAmt: document.getElementById('insight-top-cat-amt'),
    insightTopCatPct: document.getElementById('insight-top-cat-pct'),
    insightTopCatIcon: document.getElementById('insight-top-cat-icon'),
    insightDailyAvg: document.getElementById('insight-daily-avg'),
    insightDaysElapsed: document.getElementById('insight-days-elapsed'),
    insightSavingsRate: document.getElementById('insight-savings-rate'),
    insightSavingsEval: document.getElementById('insight-savings-eval'),
    insightPeakDay: document.getElementById('insight-peak-day'),
    insightPeakAmt: document.getElementById('insight-peak-amt'),
    insightPeakItem: document.getElementById('insight-peak-item'),
    comparisonSubtext: document.getElementById('comparison-subtext'),
    comparisonMessage: document.getElementById('comparison-message'),
    comparisonPrevLabel: document.getElementById('comparison-prev-label'),
    comparisonPrevBar: document.getElementById('comparison-prev-bar'),
    comparisonPrevVal: document.getElementById('comparison-prev-val'),
    comparisonCurrLabel: document.getElementById('comparison-curr-label'),
    comparisonCurrBar: document.getElementById('comparison-curr-bar'),
    comparisonCurrVal: document.getElementById('comparison-curr-val'),
    comparisonBadge: document.getElementById('comparison-badge'),
    trendsChartContainer: document.getElementById('trends-chart-container'),
    studentTipsContainer: document.getElementById('student-tips-container'),

    // Can I Afford It Elements
    affordForm: document.getElementById('afford-form'),
    affordItemName: document.getElementById('afford-item-name'),
    affordPrice: document.getElementById('afford-price'),
    affordBalance: document.getElementById('afford-balance'),
    btnSyncAffordBalance: document.getElementById('btn-sync-afford-balance'),
    affordIdleState: document.getElementById('afford-idle-state'),
    affordVerdictContent: document.getElementById('afford-verdict-content'),
    verdictBanner: document.getElementById('verdict-banner'),
    verdictEmoji: document.getElementById('verdict-emoji'),
    verdictBadge: document.getElementById('verdict-badge'),
    verdictHeadline: document.getElementById('verdict-headline'),
    verdictExplanation: document.getElementById('verdict-explanation'),
    verdictPrice: document.getElementById('verdict-price'),
    verdictRemaining: document.getElementById('verdict-remaining'),
    verdictPct: document.getElementById('verdict-pct'),
    verdictRecommendation: document.getElementById('verdict-recommendation'),

    // Modals & Forms
    modalTransaction: document.getElementById('modal-transaction'),
    txnForm: document.getElementById('txn-form'),
    modalTxnTitle: document.getElementById('modal-txn-title'),
    txnEditId: document.getElementById('txn-edit-id'),
    formTypeSelector: document.getElementById('form-type-selector'),
    txnAmount: document.getElementById('txn-amount'),
    txnCategory: document.getElementById('txn-category'),
    txnDescription: document.getElementById('txn-description'),
    txnDate: document.getElementById('txn-date'),
    txnPaymentMethod: document.getElementById('txn-payment-method'),
    txnNote: document.getElementById('txn-note'),

    modalBudget: document.getElementById('modal-budget'),
    budgetForm: document.getElementById('budget-form'),
    budgetCategory: document.getElementById('budget-category'),
    budgetAmount: document.getElementById('budget-amount'),

    modalGoal: document.getElementById('modal-goal'),
    goalForm: document.getElementById('goal-form'),
    goalEditId: document.getElementById('goal-edit-id'),
    goalName: document.getElementById('goal-name'),
    goalCategoryType: document.getElementById('goal-category-type'),
    goalTarget: document.getElementById('goal-target'),
    goalSaved: document.getElementById('goal-saved'),

    modalDeposit: document.getElementById('modal-deposit'),
    depositForm: document.getElementById('deposit-form'),
    depositGoalId: document.getElementById('deposit-goal-id'),
    depositGoalName: document.getElementById('deposit-goal-name'),
    depositAmount: document.getElementById('deposit-amount'),

    modalDelete: document.getElementById('modal-delete'),
    deleteModalMessage: document.getElementById('delete-modal-message'),
    btnConfirmDelete: document.getElementById('btn-confirm-delete'),

    toastContainer: document.getElementById('toast-container'),
  };

  // ==========================================
  // UTILITY HELPERS
  // ==========================================

  function formatMoney(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    return Number(num).toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  function updateCurrencyLabels() {
    document.querySelectorAll('.currency-symbol').forEach((el) => {
      el.textContent = state.currency;
    });
    document.querySelectorAll('.amount-currency-symbol').forEach((el) => {
      el.textContent = state.currency;
    });
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px) scale(0.95)';
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  function openModal(modalEl) {
    if (!modalEl) return;
    modalEl.classList.add('open');
  }

  function closeModal(modalEl) {
    if (!modalEl) return;
    modalEl.classList.remove('open');
  }

  // ==========================================
  // TAB NAVIGATION
  // ==========================================

  function switchTab(tabName) {
    state.activeTab = tabName;

    // Desktop nav
    dom.navTabs.forEach((tab) => {
      const match = tab.dataset.tab === tabName;
      tab.classList.toggle('active', match);
      tab.setAttribute('aria-selected', match ? 'true' : 'false');
    });

    // Mobile nav
    dom.mobileNavTabs.forEach((tab) => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Tab panes
    dom.tabPanes.forEach((pane) => {
      const match = pane.id === `tab-${tabName}`;
      pane.classList.toggle('active', match);
    });

    // Trigger tab-specific refresh
    if (tabName === 'dashboard') loadDashboard();
    else if (tabName === 'transactions') loadTransactions();
    else if (tabName === 'budgets') loadBudgets();
    else if (tabName === 'goals') loadGoals();
    else if (tabName === 'insights') loadInsights();
    else if (tabName === 'afford') syncAffordBalance();
  }

  // ==========================================
  // API CALLS
  // ==========================================

  async function fetchMetadata() {
    try {
      const res = await fetch('/api/meta');
      const data = await res.json();
      if (data.success || data.income_categories) {
        state.meta = data;
        state.currentMonth = data.current_month;
        populateMonthSelector();
        populateCategoryOptions();
      }
    } catch (err) {
      console.error('Failed to load metadata:', err);
    }
  }

  function populateMonthSelector() {
    const select = dom.globalMonthSelect;
    select.innerHTML = '';

    const today = new Date();
    const months = [];

    // Generate last 5 months, current month, and next month
    for (let i = -1; i <= 5; i++) {
      const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const val = `${y}-${m}`;
      const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      months.push({ val, label: i === 0 ? `${label} (Current)` : label });
    }

    months.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m.val;
      opt.textContent = m.label;
      if (m.val === state.currentMonth) opt.selected = true;
      select.appendChild(opt);
    });

    const allOpt = document.createElement('option');
    allOpt.value = 'All';
    allOpt.textContent = 'All Months';
    select.appendChild(allOpt);
  }

  function populateCategoryOptions() {
    // Populate transactions category filter
    const filterCat = dom.txnCategoryFilter;
    filterCat.innerHTML = '<option value="All">All Categories</option>';

    const allCategories = [
      ...new Set([...state.meta.expense_categories, ...state.meta.income_categories]),
    ];
    allCategories.sort().forEach((cat) => {
      const emoji = state.meta.category_emojis[cat] || '🏷️';
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = `${emoji} ${cat}`;
      filterCat.appendChild(opt);
    });

    // Populate budget modal categories (expenses only)
    const budgetCat = dom.budgetCategory;
    budgetCat.innerHTML = '<option value="Overall">🎯 Overall Monthly Budget</option>';
    state.meta.expense_categories.forEach((cat) => {
      const emoji = state.meta.category_emojis[cat] || '🏷️';
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = `${emoji} ${cat}`;
      budgetCat.appendChild(opt);
    });
  }

  function updateFormCategories(type) {
    const catSelect = dom.txnCategory;
    catSelect.innerHTML = '';
    const list = type === 'Income' ? state.meta.income_categories : state.meta.expense_categories;

    list.forEach((cat) => {
      const emoji = state.meta.category_emojis[cat] || '🏷️';
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = `${emoji} ${cat}`;
      catSelect.appendChild(opt);
    });
  }

  // ==========================================
  // DASHBOARD LOADING
  // ==========================================

  async function loadDashboard() {
    try {
      const monthParam = state.currentMonth ? `?month=${state.currentMonth}` : '';
      const res = await fetch(`/api/dashboard${monthParam}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      const d = json.data;
      state.dashboard = d;

      // Update 4 Hero Metric Cards
      dom.dashCurrentBalance.textContent = formatMoney(d.current_balance);
      dom.dashMonthlyIncome.textContent = formatMoney(d.monthly_income);
      dom.dashMonthlyExpenses.textContent = formatMoney(d.monthly_expenses);
      dom.dashMonthlySavings.textContent = formatMoney(d.monthly_savings);

      // Savings % Pill
      if (d.monthly_savings < 0) {
        dom.dashSavingsPct.className = 'metric-pill pill-warning';
        dom.dashSavingsPct.textContent = 'Deficit';
      } else {
        dom.dashSavingsPct.className = 'metric-pill pill-lavender';
        dom.dashSavingsPct.textContent = `${d.savings_percentage}% saved`;
      }

      // Counts
      dom.dashIncomeCount.textContent = `${d.monthly_income > 0 ? '+' : ''}${formatMoney(d.monthly_income)} in`;
      dom.dashExpenseCount.textContent = `${d.spending_breakdown.length} categories`;

      // Quick Insight Banner
      if (d.quick_insight) {
        dom.dashInsightTitle.textContent = d.quick_insight.title;
        dom.dashInsightMessage.textContent = d.quick_insight.message;
        const iconMap = {
          neutral: '✨',
          danger: '🚨',
          warning: '⚠️',
          success: '👀',
          info: '🚀',
        };
        dom.dashInsightIcon.textContent = iconMap[d.quick_insight.type] || '💡';
      }

      // Spending Breakdown
      renderSpendingBreakdown(d.spending_breakdown);

      // Recent Transactions
      renderRecentTransactions(d.recent_transactions);

      updateCurrencyLabels();
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
  }

  function renderSpendingBreakdown(breakdown) {
    const container = dom.dashBreakdownContainer;
    container.innerHTML = '';

    if (!breakdown || breakdown.length === 0) {
      container.innerHTML = `<div class="empty-state-sm">No expenses recorded for this month yet. Tap <strong>+ Add Transaction</strong> to begin!</div>`;
      return;
    }

    breakdown.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'breakdown-item';
      row.innerHTML = `
        <div class="breakdown-meta">
          <span class="breakdown-cat">
            <span>${item.emoji}</span>
            <span>${item.category}</span>
          </span>
          <div>
            <span class="breakdown-val">${state.currency}${formatMoney(item.amount)}</span>
            <span class="breakdown-pct">(${item.percentage}%)</span>
          </div>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${Math.min(100, item.percentage)}%;"></div>
        </div>
      `;
      container.appendChild(row);
    });
  }

  function renderRecentTransactions(txns) {
    const container = dom.dashRecentTxnsContainer;
    container.innerHTML = '';

    if (!txns || txns.length === 0) {
      container.innerHTML = `<div class="empty-state-sm">No recent transactions. Tap <strong>+ Add Transaction</strong> to record cash flow!</div>`;
      return;
    }

    txns.forEach((t) => {
      const isInc = t.type === 'Income';
      const card = document.createElement('div');
      card.className = 'txn-mini-card';
      card.innerHTML = `
        <div class="txn-mini-left">
          <div class="txn-mini-icon">${t.emoji || '🏷️'}</div>
          <div>
            <div class="txn-mini-desc">${escapeHtml(t.description)}</div>
            <div class="txn-mini-meta">${t.category} • ${t.date} • ${t.payment_method}</div>
          </div>
        </div>
        <div class="txn-mini-amount ${isInc ? 'income' : 'expense'}">
          ${isInc ? '+' : '-'}${state.currency}${formatMoney(t.amount)}
        </div>
      `;
      container.appendChild(card);
    });
  }

  // ==========================================
  // TRANSACTIONS LEDGER
  // ==========================================

  async function loadTransactions() {
    try {
      const params = new URLSearchParams();
      if (state.filterType !== 'All') params.append('type', state.filterType);
      if (state.filterCategory !== 'All') params.append('category', state.filterCategory);
      if (state.currentMonth && state.currentMonth !== 'All') params.append('month', state.currentMonth);
      if (state.searchQuery.trim()) params.append('search', state.searchQuery.trim());

      const res = await fetch(`/api/transactions?${params.toString()}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      state.transactions = json.data;
      renderTransactionsList(json.data);
    } catch (err) {
      console.error('Error loading transactions:', err);
    }
  }

  function renderTransactionsList(txns) {
    const container = dom.txnsListContainer;
    container.innerHTML = '';

    dom.txnsCountBadge.textContent = `${txns.length} transaction${txns.length === 1 ? '' : 's'}`;

    // Calculate net amount for filtered view
    let net = 0;
    txns.forEach((t) => {
      if (t.type === 'Income') net += t.amount;
      else net -= t.amount;
    });

    dom.txnsNetBadge.textContent = `Net: ${net >= 0 ? '+' : '-'}${state.currency}${formatMoney(Math.abs(net))}`;
    dom.txnsNetBadge.style.color = net >= 0 ? 'var(--income-green)' : 'var(--text-main)';

    if (txns.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">💸</div>
          <h3>No transactions found</h3>
          <p>Try clearing filters or add a new transaction.</p>
        </div>
      `;
      return;
    }

    txns.forEach((t) => {
      const isInc = t.type === 'Income';
      const card = document.createElement('div');
      card.className = 'txn-card';
      card.innerHTML = `
        <div class="txn-left-col">
          <div class="txn-avatar">${t.emoji || '🏷️'}</div>
          <div class="txn-info">
            <span class="txn-title">${escapeHtml(t.description)}</span>
            <div class="txn-tags-row">
              <span class="tag-pill">${t.category}</span>
              <span class="tag-pill">${t.payment_method}</span>
              <span class="tag-date">${t.date}</span>
            </div>
            ${t.note ? `<div class="txn-note-preview">"${escapeHtml(t.note)}"</div>` : ''}
          </div>
        </div>
        <div class="txn-right-col">
          <span class="txn-amount-val ${isInc ? 'income' : 'expense'}">
            ${isInc ? '+' : '-'}${state.currency}${formatMoney(t.amount)}
          </span>
          <div class="txn-actions">
            <button class="btn-action-icon edit-txn" data-id="${t.id}" title="Edit transaction">✏️</button>
            <button class="btn-action-icon delete delete-txn" data-id="${t.id}" data-desc="${escapeHtml(t.description)}" title="Delete transaction">🗑️</button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    // Bind edit and delete buttons
    container.querySelectorAll('.edit-txn').forEach((btn) => {
      btn.addEventListener('click', () => openEditTransactionModal(Number(btn.dataset.id)));
    });

    container.querySelectorAll('.delete-txn').forEach((btn) => {
      btn.addEventListener('click', () => {
        confirmDelete('transaction', Number(btn.dataset.id), `Transaction "${btn.dataset.desc}"`);
      });
    });
  }

  // ==========================================
  // BUDGETS MANAGEMENT
  // ==========================================

  async function loadBudgets() {
    try {
      const monthParam = state.currentMonth ? `?month=${state.currentMonth}` : '';
      const res = await fetch(`/api/budgets${monthParam}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      const d = json.data;
      renderOverallBudget(d.overall_budget);
      renderCategoryBudgets(d.category_budgets);
      updateCurrencyLabels();
    } catch (err) {
      console.error('Error loading budgets:', err);
    }
  }

  function renderOverallBudget(ob) {
    if (!ob) {
      dom.budgetOverallSpent.textContent = '0';
      dom.budgetOverallTarget.textContent = '0';
      dom.budgetOverallRemaining.textContent = '0';
      dom.budgetOverallBar.style.width = '0%';
      dom.budgetOverallBar.className = 'progress-fill-lg';
      dom.budgetOverallWarning.className = 'budget-alert-badge alert-healthy';
      dom.budgetOverallWarningText.textContent = 'No overall budget set. Click Set Overall Limit!';
      dom.budgetOverallPct.textContent = '0% used';
      return;
    }

    dom.budgetOverallSpent.textContent = formatMoney(ob.spent);
    dom.budgetOverallTarget.textContent = formatMoney(ob.budget_amount);
    dom.budgetOverallRemaining.textContent = formatMoney(Math.abs(ob.remaining));
    dom.budgetOverallPct.textContent = `${ob.percentage}% used`;

    const barWidth = Math.min(100, Math.max(0, ob.percentage));
    dom.budgetOverallBar.style.width = `${barWidth}%`;

    dom.budgetOverallBar.className = `progress-fill-lg ${ob.status}`;
    dom.budgetOverallWarning.className = `budget-alert-badge alert-${ob.status}`;
    const icon = ob.status === 'exceeded' ? '🚨' : ob.status === 'warning' ? '⚠️' : '🟢';
    dom.budgetOverallWarningText.textContent = `${icon} ${ob.warning_msg}`;
  }

  function renderCategoryBudgets(budgets) {
    const container = dom.categoryBudgetsContainer;
    container.innerHTML = '';

    if (!budgets || budgets.length === 0) {
      container.innerHTML = `
        <div class="empty-state-sm" style="grid-column: 1 / -1;">
          No category budgets created yet. Tap <strong>+ Set Category Budget</strong> to set limits on Food, Shopping, etc.
        </div>
      `;
      return;
    }

    budgets.forEach((b) => {
      const card = document.createElement('div');
      card.className = 'cat-budget-card';
      const isExceeded = b.status === 'exceeded';
      const isWarning = b.status === 'warning';

      card.innerHTML = `
        <div class="cat-budget-top">
          <span class="cat-budget-name">
            <span>${b.emoji}</span>
            <span>${b.category}</span>
          </span>
          <div class="txn-actions">
            <button class="btn-action-icon delete-budget" data-id="${b.id}" data-cat="${b.category}" title="Remove budget">✕</button>
          </div>
        </div>
        <div class="cat-budget-vals">
          <span>Spent: <strong>${state.currency}${formatMoney(b.spent)}</strong></span>
          <span>Limit: ${state.currency}${formatMoney(b.budget_amount)}</span>
        </div>
        <div class="progress-track mb-4">
          <div class="progress-fill ${isExceeded ? 'exceeded' : isWarning ? 'warning' : ''}" style="width: ${Math.min(100, b.percentage)}%; background: ${isExceeded ? '#EF4444' : isWarning ? '#F59E0B' : 'var(--primary-gradient)'};"></div>
        </div>
        <div class="cat-budget-vals">
          <span class="metric-pill alert-${b.status}">${b.warning_msg}</span>
          <span style="font-weight: 700; font-size: 0.8rem; color: var(--text-muted);">${b.percentage}%</span>
        </div>
      `;
      container.appendChild(card);
    });

    container.querySelectorAll('.delete-budget').forEach((btn) => {
      btn.addEventListener('click', () => {
        confirmDelete('budget', Number(btn.dataset.id), `Budget for ${btn.dataset.cat}`);
      });
    });
  }

  // ==========================================
  // SAVINGS GOALS MANAGEMENT
  // ==========================================

  async function loadGoals() {
    try {
      const monthParam = state.currentMonth ? `?month=${state.currentMonth}` : '';
      const res = await fetch(`/api/goals${monthParam}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      renderGoals(json.data);
      updateCurrencyLabels();
    } catch (err) {
      console.error('Error loading goals:', err);
    }
  }

  function renderGoals(goals) {
    const container = dom.goalsContainer;
    container.innerHTML = '';

    if (!goals || goals.length === 0) {
      container.innerHTML = `
        <div class="empty-state-sm" style="grid-column: 1 / -1;">
          No savings goals yet! Pick a preset above or tap <strong>+ Create Savings Goal</strong> to start saving for a Laptop, Trip, or Phone!
        </div>
      `;
      return;
    }

    goals.forEach((g) => {
      const card = document.createElement('div');
      card.className = 'goal-card';
      card.innerHTML = `
        <div>
          <div class="goal-header">
            <div class="goal-avatar">${g.icon}</div>
            <span class="badge-pill">${g.category_type}</span>
          </div>
          <h3 class="goal-title">${escapeHtml(g.name)}</h3>
          <div class="goal-amounts-row mt-2">
            <div>
              <span class="stat-label">Saved</span>
              <div class="goal-saved-num">${state.currency}${formatMoney(g.saved_amount)}</div>
            </div>
            <div class="text-right">
              <span class="stat-label">Target</span>
              <div class="goal-target-num">${state.currency}${formatMoney(g.target_amount)}</div>
            </div>
          </div>
          <div class="progress-track mb-1" style="height: 10px;">
            <div class="progress-fill" style="width: ${g.progress_pct}%;"></div>
          </div>
          <div class="cat-budget-vals">
            <span style="font-size: 0.78rem; font-weight: 700; color: var(--primary);">${g.progress_pct}% completed</span>
            <span style="font-size: 0.78rem; color: var(--text-muted);">${state.currency}${formatMoney(g.remaining)} needed</span>
          </div>
          <div class="goal-eta-badge">
            <span>⏱️</span>
            <span>${g.estimated_time}</span>
          </div>
        </div>

        <div class="goal-actions-row">
          <button class="btn btn-primary btn-sm deposit-goal-btn" data-id="${g.id}" data-name="${escapeHtml(g.name)}">+ Deposit</button>
          <button class="btn btn-outline btn-sm edit-goal-btn" data-id="${g.id}">Edit</button>
          <button class="btn-action-icon delete delete-goal-btn" data-id="${g.id}" data-name="${escapeHtml(g.name)}" title="Delete goal">🗑️</button>
        </div>
      `;
      container.appendChild(card);
    });

    // Bind deposit, edit, delete
    container.querySelectorAll('.deposit-goal-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        dom.depositGoalId.value = btn.dataset.id;
        dom.depositGoalName.textContent = `Deposit to "${btn.dataset.name}"`;
        dom.depositAmount.value = '';
        openModal(dom.modalDeposit);
      });
    });

    container.querySelectorAll('.edit-goal-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const goal = goals.find((item) => item.id === Number(btn.dataset.id));
        if (!goal) return;
        dom.goalEditId.value = goal.id;
        dom.goalName.value = goal.name;
        dom.goalCategoryType.value = goal.category_type;
        dom.goalTarget.value = goal.target_amount;
        dom.goalSaved.value = goal.saved_amount;
        dom.modalGoal.querySelector('.modal-title').textContent = 'Edit Savings Goal';
        openModal(dom.modalGoal);
      });
    });

    container.querySelectorAll('.delete-goal-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        confirmDelete('goal', Number(btn.dataset.id), `Savings Goal "${btn.dataset.name}"`);
      });
    });
  }

  // ==========================================
  // INSIGHTS TAB
  // ==========================================

  async function loadInsights() {
    try {
      const monthParam = state.currentMonth ? `?month=${state.currentMonth}` : '';
      const res = await fetch(`/api/insights${monthParam}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      const d = json.data;

      // 1. Biggest Expense
      dom.insightTopCatName.textContent = d.biggest_expense.category;
      dom.insightTopCatAmt.textContent = formatMoney(d.biggest_expense.amount);
      dom.insightTopCatPct.textContent = `${d.biggest_expense.percentage}% of expenses`;
      dom.insightTopCatIcon.textContent = d.biggest_expense.emoji || '🍔';

      // 2. Average Daily Spending
      dom.insightDailyAvg.textContent = formatMoney(d.avg_daily_spending);
      dom.insightDaysElapsed.textContent = `Across ${d.days_elapsed} days in month`;

      // 3. Savings Rate
      dom.insightSavingsRate.textContent = `${d.savings_rate}%`;
      if (d.savings_rate >= 30) {
        dom.insightSavingsEval.className = 'metric-pill pill-success';
        dom.insightSavingsEval.textContent = 'Excellent savings discipline 🔥';
      } else if (d.savings_rate > 0) {
        dom.insightSavingsEval.className = 'metric-pill pill-lavender';
        dom.insightSavingsEval.textContent = 'Positive cash cushion 👍';
      } else {
        dom.insightSavingsEval.className = 'metric-pill pill-warning';
        dom.insightSavingsEval.textContent = 'Negative cash flow ⚠️';
      }

      // 4. Highest Spending Day
      dom.insightPeakDay.textContent = d.highest_spending_day.date || 'N/A';
      dom.insightPeakAmt.textContent = formatMoney(d.highest_spending_day.amount);
      dom.insightPeakItem.textContent = d.highest_spending_day.top_item || 'No spend';

      // 5. Month Comparison
      const comp = d.month_comparison;
      dom.comparisonMessage.textContent = comp.message;
      dom.comparisonPrevVal.textContent = `${state.currency}${formatMoney(comp.previous_month_expenses)}`;
      dom.comparisonCurrVal.textContent = `${state.currency}${formatMoney(comp.current_month_expenses)}`;
      dom.comparisonSubtext.textContent = `This Month (${d.month}) vs Previous Month (${d.previous_month})`;

      const maxExp = Math.max(comp.previous_month_expenses, comp.current_month_expenses, 1);
      dom.comparisonPrevBar.style.width = `${(comp.previous_month_expenses / maxExp) * 100}%`;
      dom.comparisonCurrBar.style.width = `${(comp.current_month_expenses / maxExp) * 100}%`;

      // 6. Spending Trends Chart
      renderSpendingTrendsChart(d.spending_trends);

      // 7. Student Money Tips
      renderStudentTips(d.student_tips);

      updateCurrencyLabels();
    } catch (err) {
      console.error('Error loading insights:', err);
    }
  }

  function renderSpendingTrendsChart(trends) {
    const container = dom.trendsChartContainer;
    container.innerHTML = '';

    if (!trends || trends.length === 0) {
      container.innerHTML = `<div class="empty-state-sm" style="width: 100%;">No daily expenses recorded for this month.</div>`;
      return;
    }

    const maxAmt = Math.max(...trends.map((t) => t.amount), 100);

    trends.forEach((item) => {
      const heightPct = Math.max(8, (item.amount / maxAmt) * 100);
      const barWrapper = document.createElement('div');
      barWrapper.className = 'trend-bar-wrapper';
      barWrapper.title = `${item.date}: ${state.currency}${formatMoney(item.amount)}`;
      barWrapper.innerHTML = `
        <div class="trend-bar" style="height: ${heightPct}%;"></div>
        <span class="trend-day-label">${item.day}</span>
      `;
      container.appendChild(barWrapper);
    });
  }

  function renderStudentTips(tips) {
    const container = dom.studentTipsContainer;
    container.innerHTML = '';

    if (!tips || tips.length === 0) {
      container.innerHTML = `<div class="empty-state-sm">No tips available right now.</div>`;
      return;
    }

    tips.forEach((tip) => {
      const box = document.createElement('div');
      box.className = 'tip-box';
      box.innerHTML = `
        <div class="tip-top">
          <span>${tip.icon}</span>
          <span>${escapeHtml(tip.title)}</span>
        </div>
        <p class="tip-desc">${escapeHtml(tip.desc)}</p>
      `;
      container.appendChild(box);
    });
  }

  // ==========================================
  // CAN I AFFORD IT?
  // ==========================================

  async function syncAffordBalance() {
    try {
      const res = await fetch('/api/dashboard');
      const json = await res.json();
      if (json.success) {
        dom.affordBalance.value = json.data.current_balance;
      }
    } catch (err) {
      console.error('Failed to sync balance:', err);
    }
  }

  async function evaluateAffordability(e) {
    e.preventDefault();
    const itemName = dom.affordItemName.value.trim();
    const price = parseFloat(dom.affordPrice.value);
    const balance = parseFloat(dom.affordBalance.value);

    if (isNaN(price) || price <= 0) {
      showToast('Please enter a valid price greater than 0', 'error');
      return;
    }

    try {
      const res = await fetch('/api/afford', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_name: itemName,
          price: price,
          current_balance: isNaN(balance) ? null : balance,
        }),
      });

      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      const d = json.data;

      // Render Verdict
      dom.affordIdleState.style.display = 'none';
      dom.affordVerdictContent.style.display = 'block';

      dom.verdictBanner.className = `verdict-banner ${d.badge_color}`;
      dom.verdictEmoji.textContent = d.emoji;
      dom.verdictBadge.textContent = d.verdict;

      dom.verdictHeadline.textContent = d.headline;
      dom.verdictExplanation.textContent = d.explanation;

      dom.verdictPrice.textContent = formatMoney(d.price);
      dom.verdictRemaining.textContent = formatMoney(d.remaining_balance);
      dom.verdictPct.textContent = `${d.percentage_of_balance}%`;
      dom.verdictRecommendation.textContent = d.recommendation;

      updateCurrencyLabels();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // ==========================================
  // MODAL FORMS SUBMISSIONS
  // ==========================================

  // 1. Transaction Form Submit
  async function handleTransactionSubmit(e) {
    e.preventDefault();
    const editId = dom.txnEditId.value;
    const typeBtn = dom.formTypeSelector.querySelector('.segment-btn.active');
    const transType = typeBtn ? typeBtn.dataset.type : 'Expense';

    const payload = {
      type: transType,
      amount: parseFloat(dom.txnAmount.value),
      category: dom.txnCategory.value,
      description: dom.txnDescription.value.trim(),
      date: dom.txnDate.value,
      payment_method: dom.txnPaymentMethod.value,
      note: dom.txnNote.value.trim(),
    };

    if (isNaN(payload.amount) || payload.amount <= 0) {
      showToast('Amount must be greater than 0', 'error');
      return;
    }

    try {
      const url = editId ? `/api/transactions/${editId}` : '/api/transactions';
      const method = editId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      showToast(json.message || 'Transaction saved!', 'success');
      closeModal(dom.modalTransaction);
      dom.txnForm.reset();

      // Refresh data
      loadDashboard();
      if (state.activeTab === 'transactions') loadTransactions();
      if (state.activeTab === 'budgets') loadBudgets();
      if (state.activeTab === 'goals') loadGoals();
      if (state.activeTab === 'insights') loadInsights();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // 2. Budget Form Submit
  async function handleBudgetSubmit(e) {
    e.preventDefault();
    const payload = {
      category: dom.budgetCategory.value,
      amount: parseFloat(dom.budgetAmount.value),
    };

    if (isNaN(payload.amount) || payload.amount <= 0) {
      showToast('Budget amount must be greater than 0', 'error');
      return;
    }

    try {
      const res = await fetch('/api/budgets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      showToast(json.message || 'Budget saved!', 'success');
      closeModal(dom.modalBudget);
      loadBudgets();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // 3. Goal Form Submit
  async function handleGoalSubmit(e) {
    e.preventDefault();
    const editId = dom.goalEditId.value;
    const payload = {
      name: dom.goalName.value.trim(),
      category_type: dom.goalCategoryType.value,
      target_amount: parseFloat(dom.goalTarget.value),
      saved_amount: parseFloat(dom.goalSaved.value || 0),
    };

    if (!payload.name) {
      showToast('Goal name is required', 'error');
      return;
    }
    if (isNaN(payload.target_amount) || payload.target_amount <= 0) {
      showToast('Target amount must be greater than 0', 'error');
      return;
    }

    try {
      const url = editId ? `/api/goals/${editId}` : '/api/goals';
      const method = editId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      showToast(json.message || 'Goal saved!', 'success');
      closeModal(dom.modalGoal);
      loadGoals();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // 4. Deposit Form Submit
  async function handleDepositSubmit(e) {
    e.preventDefault();
    const goalId = dom.depositGoalId.value;
    const amount = parseFloat(dom.depositAmount.value);

    if (isNaN(amount) || amount <= 0) {
      showToast('Deposit amount must be greater than 0', 'error');
      return;
    }

    try {
      const res = await fetch(`/api/goals/${goalId}/deposit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      showToast(json.message || 'Deposit added!', 'success');
      closeModal(dom.modalDeposit);
      loadGoals();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // 5. Delete Handling
  function confirmDelete(type, id, label) {
    state.pendingDelete = { type, id, label };
    dom.deleteModalMessage.textContent = `Are you sure you want to delete ${label}? This cannot be undone.`;
    openModal(dom.modalDelete);
  }

  async function handleConfirmDelete() {
    if (!state.pendingDelete) return;
    const { type, id } = state.pendingDelete;

    try {
      let url = '';
      if (type === 'transaction') url = `/api/transactions/${id}`;
      else if (type === 'budget') url = `/api/budgets/${id}`;
      else if (type === 'goal') url = `/api/goals/${id}`;

      const res = await fetch(url, { method: 'DELETE' });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      showToast(json.message || 'Item deleted successfully', 'success');
      closeModal(dom.modalDelete);
      state.pendingDelete = null;

      // Reload appropriate views
      loadDashboard();
      if (type === 'transaction') loadTransactions();
      if (type === 'budget') loadBudgets();
      if (type === 'goal') loadGoals();
      if (state.activeTab === 'insights') loadInsights();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // Edit Transaction Helper
  async function openEditTransactionModal(id) {
    try {
      const res = await fetch(`/api/transactions/${id}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error);

      const t = json.data;
      dom.txnEditId.value = t.id;
      dom.modalTxnTitle.textContent = 'Edit Transaction';

      // Set type toggle
      dom.formTypeSelector.querySelectorAll('.segment-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.type === t.type);
      });
      updateFormCategories(t.type);

      dom.txnAmount.value = t.amount;
      dom.txnCategory.value = t.category;
      dom.txnDescription.value = t.description;
      dom.txnDate.value = t.date;
      dom.txnPaymentMethod.value = t.payment_method;
      dom.txnNote.value = t.note || '';

      openModal(dom.modalTransaction);
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function openAddTransactionModal() {
    dom.txnEditId.value = '';
    dom.modalTxnTitle.textContent = 'Add Transaction';
    dom.txnForm.reset();

    // Default to Expense
    dom.formTypeSelector.querySelectorAll('.segment-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.type === 'Expense');
    });
    updateFormCategories('Expense');

    // Default date to today
    const today = new Date().toISOString().split('T')[0];
    dom.txnDate.value = today;

    openModal(dom.modalTransaction);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ==========================================
  // EVENT LISTENERS BINDING
  // ==========================================

  function bindEvents() {
    // Navigation Tabs (Desktop & Mobile)
    dom.navTabs.forEach((tab) => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    dom.mobileNavTabs.forEach((tab) => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    dom.logoHomeBtn.addEventListener('click', () => switchTab('dashboard'));
    dom.dashViewBudgetsBtn.addEventListener('click', () => switchTab('budgets'));
    dom.dashViewAllTxnsBtn.addEventListener('click', () => switchTab('transactions'));
    dom.dashQuickAffordBtn.addEventListener('click', () => switchTab('afford'));

    // Global Add Transaction Buttons
    dom.openAddModalBtn.addEventListener('click', openAddTransactionModal);
    dom.mobileAddModalBtn.addEventListener('click', openAddTransactionModal);
    dom.txnsAddModalBtn.addEventListener('click', openAddTransactionModal);

    // Global Month Select
    dom.globalMonthSelect.addEventListener('change', (e) => {
      state.currentMonth = e.target.value;
      loadDashboard();
      if (state.activeTab === 'transactions') loadTransactions();
      if (state.activeTab === 'budgets') loadBudgets();
      if (state.activeTab === 'goals') loadGoals();
      if (state.activeTab === 'insights') loadInsights();
    });

    // Global Currency Select
    dom.globalCurrencySelect.value = state.currency;
    dom.globalCurrencySelect.addEventListener('change', (e) => {
      state.currency = e.target.value;
      localStorage.setItem('moneyy_currency', state.currency);
      updateCurrencyLabels();
      loadDashboard();
      if (state.activeTab === 'transactions') loadTransactions();
      if (state.activeTab === 'budgets') loadBudgets();
      if (state.activeTab === 'goals') loadGoals();
      if (state.activeTab === 'insights') loadInsights();
      if (state.activeTab === 'afford') syncAffordBalance();
    });

    // Settings Dropdown
    dom.settingsToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      dom.settingsDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!dom.settingsDropdown.contains(e.target) && e.target !== dom.settingsToggle) {
        dom.settingsDropdown.classList.remove('show');
      }
    });

    dom.reloadDemoBtn.addEventListener('click', async () => {
      dom.settingsDropdown.classList.remove('show');
      try {
        const res = await fetch('/api/demo/seed', { method: 'POST' });
        const json = await res.json();
        showToast(json.message, 'success');
        loadDashboard();
        if (state.activeTab === 'transactions') loadTransactions();
        if (state.activeTab === 'budgets') loadBudgets();
        if (state.activeTab === 'goals') loadGoals();
        if (state.activeTab === 'insights') loadInsights();
      } catch (err) {
        showToast('Failed to reload demo data', 'error');
      }
    });

    dom.clearAllBtn.addEventListener('click', async () => {
      dom.settingsDropdown.classList.remove('show');
      if (!confirm('Are you sure you want to clear all transactions, budgets, and goals?')) return;
      try {
        const res = await fetch('/api/demo/clear', { method: 'POST' });
        const json = await res.json();
        showToast(json.message, 'success');
        loadDashboard();
        if (state.activeTab === 'transactions') loadTransactions();
        if (state.activeTab === 'budgets') loadBudgets();
        if (state.activeTab === 'goals') loadGoals();
        if (state.activeTab === 'insights') loadInsights();
      } catch (err) {
        showToast('Failed to clear data', 'error');
      }
    });

    // Modal Close Buttons
    document.querySelectorAll('[data-close-modal]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.closeModal;
        closeModal(document.getElementById(modalId));
      });
    });

    // Close on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach((backdrop) => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) closeModal(backdrop);
      });
    });

    // Transaction Form Type Toggle
    dom.formTypeSelector.querySelectorAll('.segment-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        dom.formTypeSelector.querySelectorAll('.segment-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        updateFormCategories(btn.dataset.type);
      });
    });

    // Quick Amount Chips in Modal
    document.querySelectorAll('[data-quick-amount]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const addVal = parseFloat(chip.dataset.quickAmount);
        const curr = parseFloat(dom.txnAmount.value) || 0;
        dom.txnAmount.value = curr + addVal;
      });
    });

    // Form Submissions
    dom.txnForm.addEventListener('submit', handleTransactionSubmit);
    dom.budgetForm.addEventListener('submit', handleBudgetSubmit);
    dom.goalForm.addEventListener('submit', handleGoalSubmit);
    dom.depositForm.addEventListener('submit', handleDepositSubmit);
    dom.btnConfirmDelete.addEventListener('click', handleConfirmDelete);

    // Transactions Search & Filters
    let searchDebounceTimer;
    dom.txnSearchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimer);
      const val = e.target.value;
      dom.txnSearchClear.style.display = val ? 'block' : 'none';
      searchDebounceTimer = setTimeout(() => {
        state.searchQuery = val;
        loadTransactions();
      }, 250);
    });

    dom.txnSearchClear.addEventListener('click', () => {
      dom.txnSearchInput.value = '';
      dom.txnSearchClear.style.display = 'none';
      state.searchQuery = '';
      loadTransactions();
    });

    dom.txnTypeFilter.querySelectorAll('.segment-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        dom.txnTypeFilter.querySelectorAll('.segment-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        state.filterType = btn.dataset.type;
        loadTransactions();
      });
    });

    dom.txnCategoryFilter.addEventListener('change', (e) => {
      state.filterCategory = e.target.value;
      loadTransactions();
    });

    dom.btnResetFilters.addEventListener('click', () => {
      dom.txnSearchInput.value = '';
      dom.txnSearchClear.style.display = 'none';
      state.searchQuery = '';
      state.filterType = 'All';
      state.filterCategory = 'All';
      dom.txnTypeFilter.querySelectorAll('.segment-btn').forEach((b) => {
        b.classList.toggle('active', b.dataset.type === 'All');
      });
      dom.txnCategoryFilter.value = 'All';
      loadTransactions();
    });

    // Budgets Modals
    dom.btnOpenBudgetModal.addEventListener('click', () => {
      dom.budgetCategory.value = 'Food';
      dom.budgetAmount.value = '';
      openModal(dom.modalBudget);
    });

    dom.btnEditOverallBudget.addEventListener('click', () => {
      dom.budgetCategory.value = 'Overall';
      dom.budgetAmount.value = '';
      openModal(dom.modalBudget);
    });

    // Goals Modals & Presets
    dom.btnOpenGoalModal.addEventListener('click', () => {
      dom.goalEditId.value = '';
      dom.goalForm.reset();
      dom.modalGoal.querySelector('.modal-title').textContent = 'Create Savings Goal';
      openModal(dom.modalGoal);
    });

    dom.goalPresetPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        dom.goalEditId.value = '';
        dom.goalName.value = pill.dataset.name;
        dom.goalCategoryType.value = pill.dataset.type;
        dom.goalTarget.value = pill.dataset.amount;
        dom.goalSaved.value = '0';
        dom.modalGoal.querySelector('.modal-title').textContent = `Create Goal: ${pill.dataset.name}`;
        openModal(dom.modalGoal);
      });
    });

    // Can I Afford It
    dom.affordForm.addEventListener('submit', evaluateAffordability);
    dom.btnSyncAffordBalance.addEventListener('click', syncAffordBalance);
  }

  // ==========================================
  // INITIALIZATION
  // ==========================================
  async function init() {
    updateCurrencyLabels();
    await fetchMetadata();
    bindEvents();
    loadDashboard();
  }

  // Run on DOM loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
