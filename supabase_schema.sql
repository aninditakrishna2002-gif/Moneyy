-- ==============================================================================
-- MONEYY Supabase Schema & Row Level Security (RLS) Migration
-- Run this script in the Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
-- ==============================================================================

-- 1. TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
    amount NUMERIC(12, 2) NOT NULL CHECK(amount > 0),
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    date DATE NOT NULL,
    payment_method TEXT NOT NULL,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Ensure user_id column exists if table was pre-existing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'transactions' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.transactions 
        ADD COLUMN user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
    END IF;
END $$;

-- 2. BUDGETS TABLE
CREATE TABLE IF NOT EXISTS public.budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    category TEXT NOT NULL,
    monthly_amount NUMERIC(12, 2) NOT NULL CHECK(monthly_amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_user_category UNIQUE (user_id, category)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'budgets' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.budgets 
        ADD COLUMN user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
        ALTER TABLE public.budgets 
        ADD CONSTRAINT unique_user_category UNIQUE (user_id, category);
    END IF;
END $$;

-- 3. SAVINGS GOALS TABLE
CREATE TABLE IF NOT EXISTS public.savings_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    name TEXT NOT NULL,
    target_amount NUMERIC(12, 2) NOT NULL CHECK(target_amount > 0),
    saved_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.0 CHECK(saved_amount >= 0),
    category_type TEXT NOT NULL DEFAULT 'Custom',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'savings_goals' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.savings_goals 
        ADD COLUMN user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
    END IF;
END $$;

-- ==============================================================================
-- INDEXES FOR FAST USER DATA FILTERING
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON public.transactions(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON public.transactions(user_id, type);
CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON public.budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_savings_goals_user_id ON public.savings_goals(user_id);

-- ==============================================================================
-- TABLE PRIVILEGES (GRANT ACCESS TO ROLES)
-- Required by PostgREST so authenticated users and service_role can access tables
-- ==============================================================================
GRANT ALL ON TABLE public.transactions TO authenticated, service_role;
GRANT ALL ON TABLE public.budgets TO authenticated, service_role;
GRANT ALL ON TABLE public.savings_goals TO authenticated, service_role;

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Ensures each authenticated user can ONLY view, insert, update and delete their OWN records.
-- ==============================================================================

-- Enable RLS on all 3 tables
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.savings_goals ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- TRANSACTIONS RLS
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own transactions" ON public.transactions;
CREATE POLICY "Users can view their own transactions"
    ON public.transactions FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own transactions" ON public.transactions;
CREATE POLICY "Users can insert their own transactions"
    ON public.transactions FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own transactions" ON public.transactions;
CREATE POLICY "Users can update their own transactions"
    ON public.transactions FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own transactions" ON public.transactions;
CREATE POLICY "Users can delete their own transactions"
    ON public.transactions FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role full access for backend management
DROP POLICY IF EXISTS "Service role full access on transactions" ON public.transactions;
CREATE POLICY "Service role full access on transactions"
    ON public.transactions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- BUDGETS RLS
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own budgets" ON public.budgets;
CREATE POLICY "Users can view their own budgets"
    ON public.budgets FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own budgets" ON public.budgets;
CREATE POLICY "Users can insert their own budgets"
    ON public.budgets FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own budgets" ON public.budgets;
CREATE POLICY "Users can update their own budgets"
    ON public.budgets FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own budgets" ON public.budgets;
CREATE POLICY "Users can delete their own budgets"
    ON public.budgets FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role full access for backend management
DROP POLICY IF EXISTS "Service role full access on budgets" ON public.budgets;
CREATE POLICY "Service role full access on budgets"
    ON public.budgets FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- SAVINGS GOALS RLS
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own savings goals" ON public.savings_goals;
CREATE POLICY "Users can view their own savings goals"
    ON public.savings_goals FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own savings goals" ON public.savings_goals;
CREATE POLICY "Users can insert their own savings goals"
    ON public.savings_goals FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own savings goals" ON public.savings_goals;
CREATE POLICY "Users can update their own savings goals"
    ON public.savings_goals FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own savings goals" ON public.savings_goals;
CREATE POLICY "Users can delete their own savings goals"
    ON public.savings_goals FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role full access for backend management
DROP POLICY IF EXISTS "Service role full access on savings_goals" ON public.savings_goals;
CREATE POLICY "Service role full access on savings_goals"
    ON public.savings_goals FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ==============================================================================
-- 4. CUSTOM CATEGORIES TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid(),
    category_name TEXT NOT NULL,
    category_type TEXT NOT NULL CHECK(category_type IN ('Income', 'Expense')),
    emoji TEXT NOT NULL DEFAULT '🏷️',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_user_category_type UNIQUE (user_id, category_name, category_type)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'categories' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.categories 
        ADD COLUMN user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE DEFAULT auth.uid();
        ALTER TABLE public.categories 
        ADD CONSTRAINT unique_user_category_type UNIQUE (user_id, category_name, category_type);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'categories' 
        AND column_name = 'emoji'
    ) THEN
        ALTER TABLE public.categories 
        ADD COLUMN emoji TEXT NOT NULL DEFAULT '🏷️';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_categories_user_type ON public.categories(user_id, category_type);

GRANT ALL ON TABLE public.categories TO authenticated, service_role;

ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- CATEGORIES RLS
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own categories" ON public.categories;
CREATE POLICY "Users can view their own categories"
    ON public.categories FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own categories" ON public.categories;
CREATE POLICY "Users can insert their own categories"
    ON public.categories FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own categories" ON public.categories;
CREATE POLICY "Users can update their own categories"
    ON public.categories FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own categories" ON public.categories;
CREATE POLICY "Users can delete their own categories"
    ON public.categories FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access on categories" ON public.categories;
CREATE POLICY "Service role full access on categories"
    ON public.categories FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

