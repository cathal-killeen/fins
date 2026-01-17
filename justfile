# Fins - Just Commands
# Run `just` or `just --list` to see available commands

# Default recipe to display help information
default:
    @just --list

# Install all dependencies
install:
    @echo "Installing backend dependencies..."
    cd backend && uv sync
    @echo "Installing frontend dependencies..."
    cd frontend && npm install
    @echo "✅ All dependencies installed"

# Start development servers (backend and frontend in parallel)
dev:
    @echo "Starting development servers..."
    @echo "Backend: http://localhost:8000"
    @echo "Frontend: http://localhost:5173"
    just backend & just frontend

# Start all services with Docker Compose
up:
    docker compose up -d
    @echo "✅ Services started"
    @echo "Frontend: http://localhost:5173"
    @echo "Backend: http://localhost:8000"
    @echo "API Docs: http://localhost:8000/docs"

# Stop all Docker services
down:
    docker compose down
    @echo "✅ Services stopped"

# Start only PostgreSQL database in Docker
db-up:
    docker compose up postgres -d
    @echo "✅ PostgreSQL started"
    @echo "Database: postgresql://postgres:postgres@localhost:5432/fins"
    @echo ""
    @echo "You can now run backend and frontend separately:"
    @echo "  just backend  # Run backend locally"
    @echo "  just frontend # Run frontend locally"

# Stop PostgreSQL database
db-down:
    docker compose stop postgres
    @echo "✅ PostgreSQL stopped"

# Clean up build artifacts and caches
clean:
    @echo "Cleaning build artifacts..."
    -find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    -find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
    -find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null
    -find . -type f -name "*.pyc" -delete 2>/dev/null
    -find . -type f -name "*.duckdb" -delete 2>/dev/null
    @echo "✅ Cleaned up build artifacts"

# Run all tests
test:
    cd backend && uv run pytest
    @echo "✅ Tests completed"

# Run backend development server
backend:
    cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run frontend development server
frontend:
    cd frontend && npm run dev

# Initialize the database
db-init:
    @echo "Creating database..."
    -createdb fins
    @echo "Running initialization script..."
    psql -d fins -f backend/init_db.sql
    @echo "✅ Database initialized"

# Create a development test user matching the hardcoded auth user
create-test-user:
    @echo "Creating test user..."
    @PGPASSWORD=postgres psql -h localhost -U postgres -d fins -c "BEGIN; DELETE FROM users WHERE id = '00000000-0000-0000-0000-000000000001' OR email = 'test@fins.dev'; INSERT INTO users (id, email, password_hash, full_name) VALUES ('00000000-0000-0000-0000-000000000001', 'test@fins.dev', 'dev-password-not-used', 'Test User'); COMMIT;"
    @echo "✅ Test user ready (id: 00000000-0000-0000-0000-000000000001)"

# Reset the database (WARNING: destroys all data)
db-reset:
    @echo "⚠️  WARNING: This will destroy all data!"
    @echo "Are you sure? Press Ctrl+C to cancel, or Enter to continue..."
    @read -p ""
    -dropdb fins
    just db-init
    @echo "✅ Database reset complete"

# Show Docker logs
logs:
    docker-compose logs -f

# Deploy Prefect flows
prefect-deploy:
    cd backend && uv run python deploy_flows.py

# Start Prefect worker
prefect-worker:
    prefect worker start --pool default

# Create .env files from examples
env-setup:
    @echo "Creating .env files..."
    @cp -n .env.example .env 2>/dev/null || echo ".env already exists"
    @cp -n backend/.env.example backend/.env 2>/dev/null || echo "backend/.env already exists"
    @cp -n frontend/.env.example frontend/.env 2>/dev/null || echo "frontend/.env already exists"
    @echo "✅ Environment files created"
    @echo "⚠️  Remember to configure your API keys in the .env files!"

# Format Python code with ruff
format:
    cd backend && uv run ruff format .

# Lint Python code
lint:
    cd backend && uv run ruff check .

# Run frontend type checking
type-check:
    cd frontend && npm run type-check

# Build frontend for production
build-frontend:
    cd frontend && npm run build

# Build backend Docker image
build-backend:
    docker build -t fins-backend ./backend

# Build all Docker images
build:
    docker compose build

# Run database migrations
migrate:
    @echo "Running database migrations..."
    cd backend && uv run alembic upgrade head
    @echo "✅ Migrations complete"

# Create a new database migration
migration message:
    @echo "Creating new migration: {{message}}"
    cd backend && uv run alembic revision --autogenerate -m "{{message}}"
    @echo "✅ Migration created"

# Show current database migration status
db-status:
    @echo "Current database status:"
    cd backend && uv run alembic current

# Show migration history
db-history:
    @echo "Migration history:"
    cd backend && uv run alembic history

# Rollback one migration
db-rollback:
    @echo "Rolling back one migration..."
    cd backend && uv run alembic downgrade -1
    @echo "✅ Rollback complete"

# Rollback to specific migration
db-rollback-to revision:
    @echo "Rolling back to {{revision}}..."
    cd backend && uv run alembic downgrade {{revision}}
    @echo "✅ Rollback complete"

# Start a Python REPL with app context
shell:
    cd backend && uv run python

# Test LLM connectivity using current backend/.env settings
llm-test:
    cd backend && uv run python scripts/llm_test.py

# List Gemini models available for the configured API key
llm-list-models:
    cd backend && uv run python scripts/llm_list_models.py

# Show project statistics
stats:
    @echo "Project Statistics:"
    @echo "===================="
    @echo "Python files:"
    @find backend -name "*.py" | wc -l
    @echo "TypeScript/TSX files:"
    @find frontend/src -name "*.ts" -o -name "*.tsx" | wc -l
    @echo "Total lines of Python code:"
    @find backend -name "*.py" -exec wc -l {} + | tail -1
    @echo "Total lines of TypeScript code:"
    @find frontend/src \( -name "*.ts" -o -name "*.tsx" \) -exec wc -l {} + | tail -1
