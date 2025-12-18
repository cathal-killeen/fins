# Fins Backend

FastAPI-based backend for the Fins personal finance application.

## Setup

### Install Dependencies

Using uv (recommended):
```bash
uv sync
```

### Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database connection string
- LLM API keys
- Prefect configuration (optional)

### Database Setup

1. Create the PostgreSQL database:
```bash
createdb fins
```

2. Run the initialization script:
```bash
psql -d fins -f init_db.sql
```

Or use the provided SQL directly in your PostgreSQL client.

### Run the Server

Development mode with auto-reload:
```bash
uv run uvicorn app.main:app --reload
```

Production mode:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── accounts.py   # Account management
│   │   ├── transactions.py  # Transaction CRUD
│   │   ├── analytics.py  # Analytics endpoints
│   │   └── ai_chat.py    # AI chat interface
│   ├── flows/            # Prefect workflows
│   │   ├── sync_accounts.py
│   │   ├── categorize_transactions.py
│   │   ├── update_analytics.py
│   │   ├── recurring_detection.py
│   │   └── budget_alerts.py
│   ├── models/           # SQLAlchemy models (TODO)
│   ├── schemas/          # Pydantic schemas (TODO)
│   ├── services/         # Business logic
│   │   ├── ai_service.py
│   │   ├── categorization.py
│   │   ├── import_service.py
│   │   └── analytics_service.py
│   ├── utils/            # Utility functions
│   ├── config.py         # Application configuration
│   ├── database.py       # Database connections
│   └── main.py           # FastAPI application
├── tests/                # Test files
├── init_db.sql           # Database schema
├── deploy_flows.py       # Prefect deployment script
├── pyproject.toml        # Project dependencies
└── README.md
```

## LLM Configuration

The backend supports multiple LLM providers via LiteLLM. Configure in `.env`:

```bash
LLM_PROVIDER=anthropic  # or openai, azure, bedrock, etc.
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=your-api-key
```

See main README for more provider options.

## Prefect Workflows

### Available Flows

1. **Daily Account Sync** (`sync_accounts.py`)
   - Syncs transactions from bank APIs
   - Runs daily at 2 AM
   - Deduplicates transactions

2. **AI Categorization** (`categorize_transactions.py`)
   - Categorizes uncategorized transactions
   - Runs every 6 hours
   - Learns from user corrections

3. **Analytics Update** (`update_analytics.py`)
   - Syncs PostgreSQL to DuckDB
   - Updates materialized views
   - Runs every 6 hours

4. **Recurring Detection** (`recurring_detection.py`)
   - Identifies recurring patterns
   - Runs weekly on Sundays
   - Creates recurring groups

5. **Budget Alerts** (`budget_alerts.py`)
   - Checks budget status
   - Sends alerts when thresholds exceeded
   - Runs daily at 8 AM

### Deploy Workflows

```bash
python deploy_flows.py
```

### Run Locally

Test a flow locally:
```bash
uv run python -c "
from app.flows.categorize_transactions import categorization_flow
import asyncio
asyncio.run(categorization_flow())
"
```

## Testing

Run tests:
```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=app --cov-report=html
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Accounts
- `GET /api/accounts` - List accounts
- `POST /api/accounts` - Create account
- `GET /api/accounts/{id}` - Get account
- `PATCH /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account
- `POST /api/accounts/{id}/sync` - Trigger sync

### Transactions
- `GET /api/transactions` - List transactions (with filters)
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/{id}` - Get transaction
- `PATCH /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction
- `POST /api/transactions/import` - Import CSV
- `POST /api/transactions/categorize` - Trigger categorization

### Analytics
- `GET /api/analytics/dashboard` - Dashboard summary
- `GET /api/analytics/spending` - Spending by category
- `GET /api/analytics/trends` - Spending trends
- `GET /api/analytics/monthly-summary` - Monthly summary
- `GET /api/analytics/merchants` - Top merchants
- `GET /api/analytics/recurring` - Recurring transactions
- `GET /api/analytics/export` - Export data

### AI
- `POST /api/ai/chat` - Natural language query
- `GET /api/ai/insights` - Get AI insights
- `POST /api/ai/categorize-suggestion` - Get category suggestion

## Database

### PostgreSQL Schema

See [init_db.sql](init_db.sql) for the complete schema.

Key tables:
- `users` - User accounts
- `accounts` - Bank accounts, credit cards, etc.
- `transactions` - All transactions (partitioned by month)
- `categorization_rules` - Learned AI patterns
- `budgets` - User budgets
- `sync_jobs` - Prefect job tracking

### DuckDB Analytics

DuckDB is used for fast analytical queries. Data is synced from PostgreSQL via the analytics update flow.

## Development

### Adding New API Endpoints

1. Create/update route handler in `app/api/`
2. Add business logic in `app/services/`
3. Update models/schemas as needed
4. Add tests

### Adding New Prefect Flows

1. Create flow in `app/flows/`
2. Define tasks with retry logic
3. Update `deploy_flows.py`
4. Test locally before deploying

### Database Migrations

Using Alembic:
```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Troubleshooting

### Database Connection Issues

Check PostgreSQL is running:
```bash
psql -U postgres -d fins -c "SELECT 1"
```

### LLM API Issues

Verify API key is set:
```bash
echo $LLM_API_KEY
```

Test connection:
```bash
uv run python -c "from app.services.ai_service import llm_service; print(llm_service.model)"
```

### Prefect Issues

Check Prefect connection:
```bash
prefect config view
```

View flow runs:
```bash
prefect flow-run ls
```
