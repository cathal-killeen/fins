-- Personal Finance App - Database Initialization Script
-- PostgreSQL Schema

-- Create database (run this separately if needed)
-- CREATE DATABASE fins;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (Bank accounts, credit cards, investments)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(50) NOT NULL, -- checking, savings, credit_card, investment, cash
    institution VARCHAR(255),
    account_name VARCHAR(255) NOT NULL,
    account_number_last4 VARCHAR(4),
    currency VARCHAR(3) DEFAULT 'USD',
    current_balance NUMERIC(15, 2),
    available_balance NUMERIC(15, 2),
    credit_limit NUMERIC(15, 2), -- For credit cards
    is_active BOOLEAN DEFAULT true,
    last_synced_at TIMESTAMP,
    sync_error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for accounts
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_accounts_active ON accounts(is_active);

-- Transactions (partitioned by month for performance)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    post_date DATE,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT NOT NULL,
    merchant_name VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    is_recurring BOOLEAN DEFAULT false,
    recurring_group_id UUID,
    confidence_score FLOAT,
    ai_categorized BOOLEAN DEFAULT false,
    user_verified BOOLEAN DEFAULT false,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (transaction_date);

-- Create partitions for 2025 (add more as needed)
CREATE TABLE transactions_y2025m01 PARTITION OF transactions
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE transactions_y2025m02 PARTITION OF transactions
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE transactions_y2025m03 PARTITION OF transactions
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE transactions_y2025m04 PARTITION OF transactions
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE transactions_y2025m05 PARTITION OF transactions
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE transactions_y2025m06 PARTITION OF transactions
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE transactions_y2025m07 PARTITION OF transactions
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE transactions_y2025m08 PARTITION OF transactions
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE transactions_y2025m09 PARTITION OF transactions
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE transactions_y2025m10 PARTITION OF transactions
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE transactions_y2025m11 PARTITION OF transactions
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE transactions_y2025m12 PARTITION OF transactions
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Create indexes for transactions
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_name);
CREATE INDEX idx_transactions_recurring ON transactions(recurring_group_id) WHERE recurring_group_id IS NOT NULL;

-- AI Categorization Rules (learned patterns)
CREATE TABLE categorization_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL, -- merchant_exact, merchant_contains, description_pattern
    pattern_value TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    confidence_score FLOAT DEFAULT 1.0,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, pattern_type, pattern_value)
);

CREATE INDEX idx_categorization_rules_user ON categorization_rules(user_id);
CREATE INDEX idx_categorization_rules_pattern ON categorization_rules(pattern_type, pattern_value);

-- Budgets
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    amount NUMERIC(15, 2) NOT NULL,
    period VARCHAR(20) NOT NULL, -- monthly, quarterly, yearly
    start_date DATE NOT NULL,
    end_date DATE,
    rollover_enabled BOOLEAN DEFAULT false,
    alert_threshold FLOAT DEFAULT 0.8, -- Alert at 80%
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, category, subcategory, period, start_date)
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);
CREATE INDEX idx_budgets_active ON budgets(is_active);
CREATE INDEX idx_budgets_period ON budgets(period, start_date);

-- Prefect Job Tracking
CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- account_sync, categorization, analytics
    prefect_flow_run_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_jobs_user_id ON sync_jobs(user_id);
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX idx_sync_jobs_type ON sync_jobs(job_type);
CREATE INDEX idx_sync_jobs_flow_run ON sync_jobs(prefect_flow_run_id);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for easy transaction queries with account info
CREATE VIEW transactions_with_accounts AS
SELECT
    t.*,
    a.account_name,
    a.account_type,
    a.institution
FROM transactions t
JOIN accounts a ON t.account_id = a.id;

-- Function to get user spending summary
CREATE OR REPLACE FUNCTION get_user_spending_summary(
    p_user_id UUID,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    category VARCHAR,
    total_spent NUMERIC,
    transaction_count BIGINT,
    avg_amount NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.category,
        SUM(ABS(t.amount)) as total_spent,
        COUNT(*) as transaction_count,
        AVG(ABS(t.amount)) as avg_amount
    FROM transactions t
    WHERE t.user_id = p_user_id
        AND t.transaction_date BETWEEN p_start_date AND p_end_date
        AND t.amount < 0  -- Only expenses
    GROUP BY t.category
    ORDER BY total_spent DESC;
END;
$$ LANGUAGE plpgsql;

-- Insert default categories (optional)
COMMENT ON TABLE transactions IS 'Main transactions table - partitioned by month for performance';
COMMENT ON TABLE categorization_rules IS 'AI-learned rules for automatic transaction categorization';
COMMENT ON TABLE budgets IS 'User-defined spending budgets with alerts';
COMMENT ON TABLE sync_jobs IS 'Tracks Prefect workflow execution status';
