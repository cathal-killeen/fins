# Fins - AI-Powered Personal Finance Tracker

Fins is a modern personal finance application that uses AI to automatically categorize transactions, provide insights, and help you manage your money better.

## Features

- **AI-Powered Transaction Categorization** - Automatically categorize transactions using LLMs
- **Multi-Provider LLM Support** - Works with Anthropic Claude, OpenAI, Azure, AWS Bedrock, and more
- **Smart Analytics** - DuckDB-powered analytics for fast insights
- **Workflow Automation** - Prefect-based orchestration for recurring tasks
- **Budget Tracking** - Set budgets and get alerts
- **Recurring Detection** - Automatically identify subscriptions and bills
- **Natural Language Queries** - Ask questions about your finances in plain English

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Transactional data storage
- **DuckDB** - Analytics and aggregations
- **Prefect** - Workflow orchestration
- **LiteLLM** - Multi-provider LLM support
- **SQLAlchemy** - ORM

### Frontend
- **React** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **React Query** - Data fetching

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [just](https://github.com/casey/just) - Command runner (optional but recommended)

### Setup with Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd fins
```

2. Create environment files:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Configure your LLM provider in `.env`:
```bash
# For Anthropic Claude
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=your-anthropic-api-key

# For OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=your-openai-api-key
```

4. Start the services:
```bash
docker compose up -d
```

5. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Set up PostgreSQL database:
```bash
createdb fins
psql -d fins -f init_db.sql
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the backend:
```bash
uv run uvicorn app.main:app --reload
```

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Run the frontend:
```bash
npm run dev
```

## LLM Provider Configuration

Fins supports multiple LLM providers through LiteLLM. Configure your preferred provider in the `.env` file:

### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=your-anthropic-api-key
```

### OpenAI
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=your-openai-api-key
```

### Azure OpenAI
```bash
LLM_PROVIDER=azure
LLM_MODEL=gpt-4
LLM_API_KEY=your-azure-api-key
LLM_API_BASE=https://your-resource.openai.azure.com/
```

### AWS Bedrock
```bash
LLM_PROVIDER=bedrock
LLM_MODEL=anthropic.claude-v2
# AWS credentials should be configured via AWS CLI or environment variables
```

### Ollama (Local)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama2
LLM_API_BASE=http://localhost:11434
```

## Prefect Workflows

Fins uses Prefect for workflow orchestration. The following workflows are available:

- **Daily Account Sync** - Sync transactions from bank APIs
- **AI Categorization** - Automatically categorize transactions
- **Analytics Update** - Sync data to DuckDB for analytics
- **Recurring Detection** - Identify recurring transactions
- **Budget Alerts** - Send alerts when budgets are exceeded

### Setting up Prefect

1. Sign up for Prefect Cloud (free tier): https://app.prefect.cloud

2. Login to Prefect:
```bash
prefect cloud login
```

3. Deploy workflows:
```bash
cd backend
python deploy_flows.py
```

4. Start a Prefect worker:
```bash
prefect worker start --pool default
```

## Project Structure

```
fins/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── flows/        # Prefect workflows
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   └── main.py       # FastAPI app
│   ├── init_db.sql       # Database schema
│   ├── pyproject.toml    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   └── utils/        # Utilities
│   ├── package.json      # Node dependencies
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Development

### Running Tests

Backend:
```bash
cd backend
uv run pytest
```

### Database Migrations

Fins uses Alembic for database migrations:

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

### Adding Transaction Partitions

Transactions are partitioned by month for performance. To add a new partition:

```sql
CREATE TABLE transactions_y2026m01 PARTITION OF transactions
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.

## Roadmap

### Phase 1 (MVP) - Current
- [x] Project setup
- [ ] User authentication
- [ ] Manual transaction import (CSV)
- [ ] AI categorization
- [ ] Basic dashboard
- [ ] Prefect workflows

### Phase 2 (Core Features)
- [ ] Bank API integration (Plaid)
- [ ] Budget tracking
- [ ] Recurring detection
- [ ] Advanced analytics
- [ ] Export functionality

### Phase 3 (AI Features)
- [ ] Natural language queries
- [ ] Financial insights
- [ ] Spending predictions
- [ ] Anomaly detection

### Phase 4 (Polish)
- [ ] Mobile responsive design
- [ ] Dark mode
- [ ] Multi-currency support
- [ ] Custom reports
