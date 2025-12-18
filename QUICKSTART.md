# Fins - Quick Start Guide

Get up and running with Fins in 5 minutes!

## Prerequisites

Before you begin, make sure you have:
- Python 3.12+ installed
- Node.js 20+ installed
- PostgreSQL 16+ installed and running
- [uv](https://github.com/astral-sh/uv) package manager installed
- [just](https://github.com/casey/just) command runner installed (recommended)
- An API key from your preferred LLM provider (Anthropic, OpenAI, etc.)

## Option 1: Quick Start with Just (Recommended)

### 1. Set Up Environment

```bash
# Create environment files from templates
just env-setup

# Edit .env and add your API key
# For Anthropic Claude:
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=your-anthropic-api-key-here

# For OpenAI:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=your-openai-api-key-here
```

### 2. Initialize Database

```bash
just db-init
```

### 3. Install Dependencies

```bash
just install
```

### 4. Start Development Servers

```bash
just dev
```

That's it! 🎉

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 2: Docker (Easiest)

### 1. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your LLM API key
```

### 2. Start Services

```bash
docker-compose up -d
```

Access the application:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 3: Manual Setup

### 1. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env and add your configuration

# Initialize database
createdb fins
psql -d fins -f init_db.sql

# Start backend
uv run uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start frontend
npm run dev
```

## Verify Installation

1. Open http://localhost:5173 in your browser
2. You should see the Fins dashboard
3. Check the API at http://localhost:8000/docs

## Next Steps

### 1. Set Up Prefect (Optional)

If you want to use workflow automation:

```bash
# Sign up for Prefect Cloud (free tier)
# https://app.prefect.cloud

# Login
prefect cloud login

# Deploy workflows
make prefect-deploy

# Start worker
make prefect-worker
```

### 2. Add Your First Account

1. Navigate to the Accounts page
2. Click "Add Account"
3. Enter your account details

### 3. Import Transactions

1. Go to Transactions page
2. Click "Import CSV"
3. Upload a CSV file from your bank
4. Watch as AI automatically categorizes them!

### 4. Explore Analytics

1. Visit the Analytics page
2. See your spending breakdown
3. Identify trends and patterns

## Common Issues

### Database Connection Error

Make sure PostgreSQL is running:
```bash
psql -U postgres -c "SELECT 1"
```

If it's not running, start it:
```bash
# macOS with Homebrew
brew services start postgresql@16

# Linux
sudo systemctl start postgresql
```

### Port Already in Use

If port 8000 or 5173 is already in use, edit `docker-compose.yml` or change the ports in the run commands.

### LLM API Errors

Verify your API key is correct:
```bash
# Check .env file
cat .env | grep LLM_API_KEY
```

Test the connection:
```bash
cd backend
uv run python -c "from app.services.ai_service import llm_service; print('LLM Provider:', llm_service.provider)"
```

## Available Just Commands

Run `just` or `just --list` to see all available commands:

```bash
just                   # Show available commands
just install           # Install dependencies
just dev               # Start dev servers
just up                # Start with Docker
just down              # Stop Docker services
just clean             # Clean build artifacts
just test              # Run tests
just db-init           # Initialize database
just db-reset          # Reset database (⚠️ destroys data)
just logs              # Show Docker logs
just prefect-deploy    # Deploy Prefect flows
just prefect-worker    # Start Prefect worker
just env-setup         # Create .env files
just format            # Format Python code
just lint              # Lint Python code
just stats             # Show project statistics
```

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Check the [backend README](backend/README.md) for API details
- Open an issue on GitHub for bugs or questions

## What's Next?

- Read [CLAUDE.md](CLAUDE.md) for the full architecture
- Explore the API documentation at http://localhost:8000/docs
- Check out the Prefect flows in `backend/app/flows/`
- Customize the frontend in `frontend/src/`

Happy tracking! 💰
