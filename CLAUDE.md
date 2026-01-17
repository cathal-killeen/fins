# Personal Finance App - AI-Native Architecture

## Project Overview

Build a personal finance tracking application with AI-powered transaction categorization, data orchestration, and analytics.

**Core Technologies:**
- **Orchestration**: Prefect (workflow management)
- **Database**: DuckDB (analytics) + PostgreSQL (transactional data)
- **AI**: Anthropic Claude API (transaction categorization & insights)
- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript + Tailwind CSS

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Dashboard  - Transactions  - Analytics  - AI Chat    │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────┴──────────────────────────────────┐
│              Backend (FastAPI)                           │
│  - API Routes  - Auth  - File Upload  - WebSocket       │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼─────────┐
│  PostgreSQL    │          │  Prefect Cloud    │
│  (Transactions)│          │  (Orchestration)  │
└───────┬────────┘          └─────────┬─────────┘
        │                             │
        │    ┌────────────────────────┘
        │    │
┌───────▼────▼────┐         ┌──────────────────┐
│    DuckDB        │         │  Claude API      │
│  (Analytics)     │         │  (AI Services)   │
└──────────────────┘         └──────────────────┘
```

## Database Schema

### PostgreSQL (Transactional Data)

```sql
-- Users
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

-- Transactions
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
    confidence_score FLOAT, -- AI confidence (0-1)
    ai_categorized BOOLEAN DEFAULT false,
    user_verified BOOLEAN DEFAULT false,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    INDEX idx_transactions_user_id (user_id),
    INDEX idx_transactions_account_id (account_id),
    INDEX idx_transactions_date (transaction_date DESC),
    INDEX idx_transactions_category (category),
    INDEX idx_transactions_merchant (merchant_name)
);

-- Partition by month for performance
CREATE TABLE transactions_y2025m01 PARTITION OF transactions
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

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
```

### DuckDB (Analytics & Aggregations)

DuckDB will be used for:
- Fast analytical queries
- Historical trend analysis
- Complex aggregations
- Data exports
- ML feature engineering

Data is synced from PostgreSQL to DuckDB via Prefect workflows.

```sql
-- DuckDB analytics tables (materialized views)
CREATE TABLE analytics.daily_spending AS
SELECT 
    user_id,
    transaction_date,
    category,
    subcategory,
    SUM(amount) as total_amount,
    COUNT(*) as transaction_count,
    AVG(amount) as avg_amount
FROM transactions
GROUP BY user_id, transaction_date, category, subcategory;

-- Monthly aggregations
CREATE TABLE analytics.monthly_summary AS
SELECT 
    user_id,
    DATE_TRUNC('month', transaction_date) as month,
    category,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses,
    COUNT(*) as transaction_count
FROM transactions
GROUP BY user_id, month, category;

-- Merchant analysis
CREATE TABLE analytics.merchant_stats AS
SELECT 
    user_id,
    merchant_name,
    category,
    COUNT(*) as visit_count,
    SUM(amount) as total_spent,
    AVG(amount) as avg_spent,
    MIN(transaction_date) as first_visit,
    MAX(transaction_date) as last_visit
FROM transactions
WHERE merchant_name IS NOT NULL
GROUP BY user_id, merchant_name, category;
```

## Project Structure

```
finance-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # DB connections
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   └── budget.py
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py
│   │   │   └── account.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   ├── analytics.py
│   │   │   └── ai_chat.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py       # Claude API integration
│   │   │   ├── categorization.py   # Transaction categorization
│   │   │   ├── import_service.py   # CSV/OFX import
│   │   │   └── analytics_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── csv_parser.py
│   │       └── date_utils.py
│   ├── flows/                      # Prefect flows
│   │   ├── __init__.py
│   │   ├── sync_accounts.py        # Daily account sync
│   │   ├── categorize_transactions.py
│   │   ├── update_analytics.py     # Sync to DuckDB
│   │   ├── budget_alerts.py
│   │   └── recurring_detection.py
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   │   ├── OverviewCard.tsx
│   │   │   │   ├── SpendingChart.tsx
│   │   │   │   └── RecentTransactions.tsx
│   │   │   ├── Transactions/
│   │   │   │   ├── TransactionList.tsx
│   │   │   │   ├── TransactionRow.tsx
│   │   │   │   └── CategoryBadge.tsx
│   │   │   ├── Analytics/
│   │   │   │   ├── TrendsChart.tsx
│   │   │   │   └── CategoryBreakdown.tsx
│   │   │   ├── AI/
│   │   │   │   └── ChatInterface.tsx
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       └── Card.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Transactions.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── Budgets.tsx
│   │   │   └── Accounts.tsx
│   │   ├── hooks/
│   │   │   ├── useTransactions.ts
│   │   │   ├── useAnalytics.ts
│   │   │   └── useAI.ts
│   │   ├── api/
│   │   │   └── client.ts           # API client
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── docker-compose.yml
└── README.md
```

## Prefect Workflows

### 1. Daily Account Sync Flow

```python
# flows/sync_accounts.py
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
import asyncio

@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
async def sync_single_account(account_id: str) -> dict:
    """
    Sync a single account with retry logic.
    Returns: {'account_id': str, 'new_transactions': int, 'success': bool}
    """
    # Implement bank API sync logic here
    # This is a placeholder for actual implementation
    pass

@task
async def deduplicate_transactions(user_id: str, account_id: str):
    """Remove duplicate transactions based on amount, date, and merchant"""
    pass

@task
async def queue_for_categorization(transaction_ids: list[str]):
    """Queue uncategorized transactions for AI processing"""
    pass

@flow(name="daily-account-sync", log_prints=True)
async def daily_account_sync_flow(user_id: str = None):
    """
    Main sync flow - runs daily for all users or on-demand for specific user.
    """
    # Get accounts to sync
    if user_id:
        accounts = await get_user_accounts(user_id)
    else:
        accounts = await get_all_active_accounts()
    
    print(f"Starting sync for {len(accounts)} accounts")
    
    # Sync all accounts in parallel
    sync_results = await sync_single_account.map(
        [account.id for account in accounts]
    )
    
    # Deduplicate transactions for each account
    await deduplicate_transactions.map(
        [(account.user_id, account.id) for account in accounts]
    )
    
    # Get all new uncategorized transactions
    uncategorized = await get_uncategorized_transactions()
    
    if uncategorized:
        print(f"Found {len(uncategorized)} uncategorized transactions")
        await queue_for_categorization([t.id for t in uncategorized])
    
    # Log summary
    total_new = sum(r['new_transactions'] for r in sync_results if r['success'])
    print(f"✅ Sync complete: {total_new} new transactions")
    
    return {
        'total_accounts': len(accounts),
        'successful_syncs': sum(1 for r in sync_results if r['success']),
        'new_transactions': total_new
    }
```

### 2. AI Categorization Flow

```python
# flows/categorize_transactions.py
from prefect import flow, task
from anthropic import Anthropic
import json

@task(retries=2, retry_delay_seconds=30)
async def categorize_batch(transaction_batch: list[dict]) -> list[dict]:
    """
    Categorize a batch of transactions using Claude API.
    Batch size: 20-50 transactions for cost efficiency.
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Check for learned patterns first
    categorized_by_rules = []
    needs_ai = []
    
    for txn in transaction_batch:
        rule = await check_categorization_rules(txn['merchant_name'], txn['description'])
        if rule and rule.confidence_score > 0.8:
            categorized_by_rules.append({
                'id': txn['id'],
                'category': rule.category,
                'subcategory': rule.subcategory,
                'confidence': rule.confidence_score,
                'method': 'rule'
            })
        else:
            needs_ai.append(txn)
    
    # AI categorize remaining transactions
    ai_results = []
    if needs_ai:
        prompt = build_categorization_prompt(needs_ai)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        ai_results = json.loads(message.content[0].text)
    
    return categorized_by_rules + ai_results

@task
async def save_categorizations(categorization_results: list[dict]):
    """Save categorization results to database"""
    for result in categorization_results:
        await update_transaction_category(
            transaction_id=result['id'],
            category=result['category'],
            subcategory=result.get('subcategory'),
            confidence=result['confidence'],
            ai_categorized=(result.get('method') == 'ai')
        )
        
        # Learn from high-confidence AI categorizations
        if result.get('method') == 'ai' and result['confidence'] > 0.9:
            await create_categorization_rule(result)

@flow(name="ai-categorization")
async def categorization_flow():
    """
    Categorize uncategorized transactions in batches.
    """
    uncategorized = await get_uncategorized_transactions(limit=500)
    
    if not uncategorized:
        print("No transactions to categorize")
        return
    
    print(f"Categorizing {len(uncategorized)} transactions")
    
    # Process in batches of 30
    batch_size = 30
    batches = [
        uncategorized[i:i+batch_size] 
        for i in range(0, len(uncategorized), batch_size)
    ]
    
    # Process batches in parallel (with rate limiting)
    results = await categorize_batch.map(batches)
    
    # Flatten results and save
    all_results = [item for batch in results for item in batch]
    await save_categorizations(all_results)
    
    print(f"✅ Categorized {len(all_results)} transactions")
```

### 3. Analytics Update Flow

```python
# flows/update_analytics.py
from prefect import flow, task
import duckdb

@task
async def sync_to_duckdb():
    """
    Sync data from PostgreSQL to DuckDB for analytics.
    Uses incremental updates based on last sync timestamp.
    """
    conn = duckdb.connect('analytics.duckdb')
    
    # Get last sync timestamp
    last_sync = await get_last_sync_timestamp()
    
    # Export new/updated transactions from PostgreSQL
    query = """
        SELECT * FROM transactions 
        WHERE updated_at > %s
    """
    new_data = await pg_query(query, [last_sync])
    
    # Upsert into DuckDB
    conn.execute("""
        INSERT OR REPLACE INTO transactions
        SELECT * FROM new_data
    """)
    
    # Update materialized views
    conn.execute("CALL refresh_daily_spending()")
    conn.execute("CALL refresh_monthly_summary()")
    conn.execute("CALL refresh_merchant_stats()")
    
    await update_sync_timestamp()
    
    print(f"✅ Synced {len(new_data)} records to DuckDB")

@task
async def generate_insights():
    """Generate AI-powered insights from analytics data"""
    # Query DuckDB for interesting patterns
    # Use Claude API to generate insights
    pass

@flow(name="analytics-update")
async def analytics_update_flow():
    """
    Update analytics database and generate insights.
    Runs every 6 hours.
    """
    await sync_to_duckdb()
    await generate_insights()
```

### 4. Recurring Transaction Detection

```python
# flows/recurring_detection.py
from prefect import flow, task
from datetime import datetime, timedelta

@task
async def detect_recurring_transactions(user_id: str):
    """
    Detect recurring transactions (subscriptions, bills).
    Algorithm: Find transactions with similar amounts and regular intervals.
    """
    # Get transactions from last 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    transactions = await get_user_transactions(user_id, since=six_months_ago)
    
    # Group by merchant and amount (within 5% variance)
    groups = group_similar_transactions(transactions)
    
    # Check for regular intervals
    recurring_groups = []
    for group in groups:
        if is_recurring_pattern(group):
            recurring_groups.append(group)
    
    return recurring_groups

@task
async def mark_as_recurring(recurring_groups: list):
    """Mark transactions as recurring and create recurring groups"""
    for group in recurring_groups:
        group_id = await create_recurring_group(group)
        await update_transactions_recurring(group['transaction_ids'], group_id)

@flow(name="recurring-detection")
async def recurring_detection_flow():
    """
    Detect and mark recurring transactions.
    Runs weekly.
    """
    users = await get_all_users()
    
    for user in users:
        recurring = await detect_recurring_transactions(user.id)
        if recurring:
            await mark_as_recurring(recurring)
            print(f"Found {len(recurring)} recurring patterns for user {user.id}")
```

### 5. Budget Alert Flow

```python
# flows/budget_alerts.py
from prefect import flow, task

@task
async def check_budget_status(user_id: str) -> list[dict]:
    """Check all active budgets for a user"""
    budgets = await get_active_budgets(user_id)
    alerts = []
    
    for budget in budgets:
        spent = await get_period_spending(
            user_id=user_id,
            category=budget.category,
            period=budget.period
        )
        
        percentage = spent / budget.amount
        
        if percentage >= budget.alert_threshold:
            alerts.append({
                'budget_id': budget.id,
                'category': budget.category,
                'spent': spent,
                'budget': budget.amount,
                'percentage': percentage
            })
    
    return alerts

@task
async def send_alert_notifications(user_id: str, alerts: list[dict]):
    """Send budget alert notifications to user"""
    if not alerts:
        return
    
    # Send email, push notification, or in-app notification
    await notification_service.send_budget_alerts(user_id, alerts)

@flow(name="budget-alerts")
async def budget_alerts_flow():
    """
    Check budgets and send alerts.
    Runs daily.
    """
    users = await get_all_users()
    
    for user in users:
        alerts = await check_budget_status(user.id)
        if alerts:
            await send_alert_notifications(user.id, alerts)
            print(f"Sent {len(alerts)} alerts to user {user.id}")
```

## AI Integration Details

### Transaction Categorization Prompt

```python
def build_categorization_prompt(transactions: list[dict]) -> str:
    """
    Build prompt for batch transaction categorization.
    """
    
    categories = {
        "Income": ["Salary", "Freelance", "Investment Income", "Gifts", "Refunds"],
        "Housing": ["Rent/Mortgage", "Utilities", "Internet", "Home Maintenance", "Furniture"],
        "Transportation": ["Gas", "Public Transit", "Ride Share", "Car Maintenance", "Parking"],
        "Food": ["Groceries", "Restaurants", "Coffee Shops", "Fast Food", "Delivery"],
        "Shopping": ["Clothing", "Electronics", "Home Goods", "Personal Care", "Books"],
        "Entertainment": ["Streaming Services", "Movies", "Gaming", "Hobbies", "Events"],
        "Healthcare": ["Medical", "Dental", "Pharmacy", "Health Insurance", "Fitness"],
        "Financial": ["Bank Fees", "Interest", "Investments", "Insurance", "Taxes"],
        "Personal": ["Haircut", "Spa", "Subscriptions", "Gifts", "Education"],
        "Travel": ["Flights", "Hotels", "Vacation", "Travel Insurance"],
        "Other": ["Uncategorized"]
    }
    
    prompt = f"""You are a financial transaction categorization expert. Analyze these transactions and categorize each one.

Available categories and subcategories:
{json.dumps(categories, indent=2)}

Transactions to categorize:
{json.dumps(transactions, indent=2)}

For each transaction, determine:
1. The most appropriate category and subcategory
2. Whether it appears to be a recurring transaction (subscription, bill, etc.)
3. Your confidence level (0.0 to 1.0)

Return ONLY a JSON array with this structure:
[
  {{
    "id": "transaction_id",
    "category": "category_name",
    "subcategory": "subcategory_name",
    "is_recurring": true/false,
    "confidence": 0.95,
    "reasoning": "brief explanation"
  }}
]

Guidelines:
- Use merchant name as primary signal
- Consider transaction amount patterns
- Look for subscription keywords (monthly, annual, membership)
- Be conservative with confidence scores
- If truly unclear, use confidence < 0.5 and suggest "Other"
"""
    
    return prompt
```

### Natural Language Query Interface

```python
# api/ai_chat.py
async def process_nl_query(user_id: str, query: str) -> dict:
    """
    Process natural language financial queries.
    Examples:
    - "How much did I spend on restaurants last month?"
    - "Show me my top 5 spending categories this year"
    - "Am I on track with my grocery budget?"
    """
    
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Get user's financial context
    context = await get_user_financial_context(user_id)
    
    prompt = f"""You are a financial analysis assistant. Analyze this user's financial data and answer their question.

User's Financial Context:
- Total accounts: {context['account_count']}
- Current month spending: ${context['current_month_spending']}
- Active budgets: {json.dumps(context['budgets'])}
- Top categories: {json.dumps(context['top_categories'])}

Recent transactions (last 30 days):
{json.dumps(context['recent_transactions'][:50], indent=2)}

User's question: {query}

Provide a clear, concise answer with specific numbers. If you need to query data, use this format:
{{
  "query_type": "spending_by_category|budget_status|transaction_search|trends",
  "parameters": {{}},
  "answer": "text answer"
}}
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(message.content[0].text)
```

## Deployment Instructions

### 1. Set Up Prefect Cloud (Free Tier)

```bash
# Install Prefect
pip install prefect

# Login to Prefect Cloud
prefect cloud login

# Create workspace (if needed)
prefect cloud workspace create my-finance-app

# Set up work pool
prefect work-pool create finance-pool --type process
```

### 2. Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/finance_db
DUCKDB_PATH=/path/to/analytics.duckdb
ANTHROPIC_API_KEY=sk-ant-...
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/.../workspaces/...
PREFECT_API_KEY=pnu_...
SECRET_KEY=your-secret-key
FRONTEND_URL=http://localhost:5173
```

### 3. Initialize Databases

```bash
# PostgreSQL (tables auto-created on app startup)
createdb finance_db

# DuckDB (auto-created on first run)
python -c "import duckdb; duckdb.connect('analytics.duckdb')"
```

### 4. Deploy Prefect Flows

```python
# deploy_flows.py
from flows.sync_accounts import daily_account_sync_flow
from flows.categorize_transactions import categorization_flow
from flows.update_analytics import analytics_update_flow
from flows.recurring_detection import recurring_detection_flow
from flows.budget_alerts import budget_alerts_flow

if __name__ == "__main__":
    # Deploy sync flow (runs daily at 2 AM)
    daily_account_sync_flow.serve(
        name="daily-account-sync",
        cron="0 2 * * *",
        tags=["sync", "production"]
    )
    
    # Deploy categorization flow (runs every 6 hours)
    categorization_flow.serve(
        name="ai-categorization",
        cron="0 */6 * * *",
        tags=["ai", "production"]
    )
    
    # Deploy analytics flow (runs every 6 hours)
    analytics_update_flow.serve(
        name="analytics-update",
        cron="0 */6 * * *",
        tags=["analytics", "production"]
    )
    
    # Deploy recurring detection (runs weekly on Sundays)
    recurring_detection_flow.serve(
        name="recurring-detection",
        cron="0 3 * * 0",
        tags=["ml", "production"]
    )
    
    # Deploy budget alerts (runs daily at 8 AM)
    budget_alerts_flow.serve(
        name="budget-alerts",
        cron="0 8 * * *",
        tags=["alerts", "production"]
    )
```

```bash
# Start Prefect worker
prefect worker start --pool finance-pool
```

### 5. Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 6. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Key Features to Implement

### Phase 1 (MVP - 4-6 weeks)
- [ ] User authentication (JWT)
- [ ] Manual transaction import (CSV)
- [ ] Basic transaction CRUD
- [ ] AI categorization with Claude
- [ ] Simple dashboard with charts
- [ ] Transaction list with filters
- [ ] Prefect daily sync workflow

### Phase 2 (Core Features - 6-8 weeks)
- [ ] Bank API integration (Plaid)
- [ ] Automatic account syncing
- [ ] Budget creation and tracking
- [ ] Budget alerts workflow
- [ ] Advanced analytics dashboard
- [ ] Recurring transaction detection
- [ ] DuckDB analytics integration
- [ ] Export functionality

### Phase 3 (AI Features - 4-6 weeks)
- [ ] Natural language query interface
- [ ] AI financial insights
- [ ] Spending predictions
- [ ] Anomaly detection
- [ ] Personalized recommendations
- [ ] Smart budget suggestions

### Phase 4 (Polish - 4 weeks)
- [ ] Mobile responsive design
- [ ] Dark mode
- [ ] Advanced filtering and search
- [ ] Custom reports
- [ ] Multi-currency support
- [ ] Data export (PDF, Excel)
- [ ] Performance optimization

## Development Guidelines

### Testing Prefect Flows Locally

```python
import asyncio
from flows.categorize_transactions import categorization_flow

# Test flow locally
async def test():
    result = await categorization_flow()
    print(f"Categorized: {result}")

asyncio.run(test())
```

### Monitoring & Observability

- Use Prefect Cloud UI to monitor flow runs
- Set up alerts for failed flows
- Log key metrics (transaction counts, API costs)
- Monitor DuckDB query performance
- Track AI categorization accuracy

### Cost Optimization

1. **Batch AI requests** (30-50 transactions per call)
2. **Cache categorization rules** (learn from user corrections)
3. **Use DuckDB for analytics** (reduce PostgreSQL load)
4. **Implement rate limiting** on AI features
5. **Use Prefect caching** for expensive operations

### Security Considerations

- Encrypt sensitive data at rest
- Use environment variables for secrets
- Implement rate limiting on API
- Validate all user inputs
- Use prepared statements (SQL injection prevention)
- Implement audit logging
- Add 2FA for user accounts
- Secure API keys in Prefect Cloud

## Success Metrics

- Transaction categorization accuracy > 90%
- Average categorization time < 2 seconds
- Daily sync success rate > 99%
- API response time < 200ms (p95)
- User satisfaction score > 4.5/5

## Next Steps

1. Set up project repository
2. Initialize PostgreSQL and DuckDB
3. Set up Prefect Cloud account
4. Implement basic FastAPI endpoints
5. Create first Prefect flow (account sync)
6. Build basic React dashboard
7. Integrate Claude API for categorization
8. Deploy to staging environment

---

**Note**: This is a comprehensive guide. Start with Phase 1 MVP and iterate based on user feedback and requirements.
