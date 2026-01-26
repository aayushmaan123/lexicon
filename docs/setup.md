# Lexicon Development Setup Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Services](#running-services)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Code Quality Tools](#code-quality-tools)
- [Development Workflow](#development-workflow)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [IDE Setup](#ide-setup)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required

1. **Python 3.11 or higher**
   ```bash
   # Check Python version
   python --version
   # or
   python3 --version
   ```
   
   - Download from: https://www.python.org/downloads/
   - Recommended: Use pyenv for Python version management

2. **Poetry** (Python dependency management)
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Verify installation
   poetry --version
   ```
   
   - Documentation: https://python-poetry.org/docs/

3. **Docker and Docker Compose** (for PostgreSQL and Redis)
   ```bash
   # Check Docker installation
   docker --version
   docker-compose --version
   ```
   
   - Download from: https://www.docker.com/get-started

4. **Git**
   ```bash
   git --version
   ```

### API Keys

5. **OpenAI API Key** (Required)
   - Sign up at: https://platform.openai.com/
   - Create an API key in your account dashboard
   - Pricing: https://openai.com/pricing

6. **Anthropic API Key** (Optional but recommended for fallback)
   - Sign up at: https://www.anthropic.com/
   - Create an API key in your account dashboard

### Optional

7. **Redis** (recommended for caching, optional for development)
   - Can run via Docker or install locally
   - Download: https://redis.io/download

8. **PostgreSQL** (optional for development, future use)
   - Can run via Docker or install locally
   - Download: https://www.postgresql.org/download/

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/lexicon.git
cd lexicon
```

### 2. Install Dependencies with Poetry

```bash
# Install all dependencies (including dev dependencies)
poetry install

# Activate the virtual environment
poetry shell

# Verify installation
python -m lexicon --version
```

**Alternative: Install with pip**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks (Optional but Recommended)

```bash
# Install pre-commit hooks
pre-commit install

# Test the hooks
pre-commit run --all-files
```

This will automatically run code formatting and linting before each commit.

## Configuration

### 1. Create Environment File

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your settings:

```env
# ===== REQUIRED =====

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-actual-openai-key-here

# ===== RECOMMENDED =====

# Anthropic Configuration (Recommended for fallback)
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Redis Configuration (Recommended for caching)
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600

# ===== OPTIONAL =====

# Database Configuration (Future use)
DATABASE_URL=postgresql://lexicon:password@localhost:5432/lexicon_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_data
CHROMA_COLLECTION_NAME=lexicon_documents

# Model Configuration
PRIMARY_LLM_MODEL=gpt-4o
SECONDARY_LLM_MODEL=gpt-4o-mini
FALLBACK_LLM_MODEL=claude-3-5-sonnet-20241022
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000

# Cost Management
MONTHLY_BUDGET_USD=40.00
ENABLE_COST_TRACKING=true

# Performance Configuration
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2
REQUEST_TIMEOUT=30

# Document Processing
MAX_FILE_SIZE_MB=50
CHUNK_SIZE_CONTRACT=512
CHUNK_OVERLAP_CONTRACT=50
CHUNK_SIZE_CASE_LAW=1024
CHUNK_OVERLAP_CASE_LAW=100
CHUNK_SIZE_GENERAL=768
CHUNK_OVERLAP_GENERAL=75
```

### 3. Verify Configuration

```bash
# Test that configuration loads correctly
python -c "from lexicon.shared.config import settings; print(f'Config loaded: {settings.primary_llm_model}')"
```

## Running Services

### Option 1: Using Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: lexicon-postgres
    environment:
      POSTGRES_DB: lexicon_db
      POSTGRES_USER: lexicon
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lexicon"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: lexicon-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

Start the services:

```bash
# Start all services in background
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### Option 2: Install Services Locally

#### PostgreSQL

**macOS (Homebrew)**:
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb lexicon_db
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb lexicon_db
sudo -u postgres createuser lexicon
```

**Windows**:
- Download installer from https://www.postgresql.org/download/windows/
- Run installer and follow setup wizard
- Use pgAdmin to create database

#### Redis

**macOS (Homebrew)**:
```bash
brew install redis
brew services start redis

# Test connection
redis-cli ping
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

**Windows**:
- Download from https://github.com/microsoftarchive/redis/releases
- Or use WSL2 with Ubuntu

### Verify Services are Running

```bash
# Test PostgreSQL
psql postgresql://lexicon:password@localhost:5432/lexicon_db -c "SELECT version();"

# Test Redis
redis-cli ping
# Expected output: PONG
```

## Running the Application

### CLI Usage

The CLI is the primary interface for Lexicon:

```bash
# Activate virtual environment first
poetry shell

# Show help
python -m lexicon --help

# Show version
python -m lexicon --version

# Analyze a document
python -m lexicon analyze examples/sample_contract.pdf

# Review a contract
python -m lexicon review examples/sample_contract.pdf

# Index documents for research
python -m lexicon index examples/ --recursive

# Perform legal research
python -m lexicon research "What are the elements of breach of contract?"
```

See [CLI Guide](cli_guide.md) for detailed CLI usage.

### REST API

Start the FastAPI server:

```bash
# Development mode with auto-reload
uvicorn lexicon.api.main:app --reload --host 0.0.0.0 --port 8000

# Alternative using Poetry
poetry run uvicorn lexicon.api.main:app --reload

# Production mode
uvicorn lexicon.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- API Root: http://localhost:8000/
- Interactive Docs (Swagger): http://localhost:8000/docs
- Alternative Docs (ReDoc): http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json
- Health Check: http://localhost:8000/health

**Test API with curl**:
```bash
# Health check
curl http://localhost:8000/health

# Analyze a document
curl -X POST "http://localhost:8000/api/v1/documents/analyze" \
  -F "file=@examples/sample_contract.pdf"
```

See [API Specification](api-spec.md) for detailed API usage.

## Running Tests

### Run All Tests

```bash
# Using pytest (recommended)
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=lexicon --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_rag_orchestrator.py

# Run specific test function
pytest tests/unit/test_rag_orchestrator.py::test_index_document

# Run tests in parallel (faster)
pytest -n auto
```

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_rag_orchestrator.py
│   ├── test_reranker.py
│   ├── test_cache_client.py
│   └── ...
├── integration/             # Integration tests (future)
│   └── test_api_endpoints.py
└── conftest.py             # Shared fixtures
```

### View Coverage Report

After running tests with coverage:

```bash
# Open HTML coverage report
open htmlcov/index.html    # macOS
xdg-open htmlcov/index.html    # Linux
start htmlcov/index.html   # Windows
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run with markers (if defined)
pytest -m "not slow"

# Run failed tests from last run
pytest --lf

# Run tests and stop on first failure
pytest -x
```

## Code Quality Tools

### Linting and Formatting

Lexicon uses **Ruff** for both linting and formatting:

```bash
# Format code (auto-fix)
ruff format .

# Lint code
ruff check .

# Lint and auto-fix issues
ruff check --fix .

# Check specific file
ruff check lexicon/services/rag_orchestrator.py

# Format specific file
ruff format lexicon/services/rag_orchestrator.py
```

### Ruff Configuration

Configuration is in `ruff.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before commits:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks for a commit (not recommended)
git commit --no-verify
```

Configuration in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

## Development Workflow

### Typical Development Session

```bash
# 1. Start services
docker-compose up -d

# 2. Activate virtual environment
poetry shell

# 3. Create feature branch
git checkout -b feature/my-new-feature

# 4. Make code changes
# ... edit files ...

# 5. Run tests
pytest

# 6. Format and lint
ruff format .
ruff check --fix .

# 7. Commit changes (pre-commit hooks run automatically)
git add .
git commit -m "Add new feature"

# 8. Push changes
git push origin feature/my-new-feature

# 9. Stop services when done
docker-compose down
```

### Adding New Dependencies

```bash
# Add a production dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Lock dependencies without installing
poetry lock

# Show outdated packages
poetry show --outdated
```

### Database Migrations (Future)

When database schema changes are needed:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current migration
alembic current

# Show migration history
alembic history
```

## Common Issues and Troubleshooting

### Issue: ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'lexicon'`

**Solution**:
```bash
# Ensure you're in the virtual environment
poetry shell

# Reinstall in editable mode
poetry install

# Or with pip
pip install -e .
```

### Issue: OpenAI API Key Error

**Problem**: `Error: OpenAI API key not found`

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
grep OPENAI_API_KEY .env

# Test API key
python -c "from lexicon.shared.config import settings; print(settings.openai_api_key[:10])"
```

### Issue: Redis Connection Failed

**Problem**: `Connection refused` or `Redis unavailable`

**Solution**:
```bash
# Check if Redis is running
docker-compose ps redis

# Or check local Redis
redis-cli ping

# Start Redis
docker-compose up -d redis

# Or start local Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

**Note**: Redis is optional. Lexicon will work without it (with degraded performance).

### Issue: Port Already in Use

**Problem**: `Error: Address already in use (port 8000)`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn lexicon.api.main:app --port 8001
```

### Issue: ChromaDB Collection Error

**Problem**: `Collection already exists` or `ChromaDB error`

**Solution**:
```bash
# Delete ChromaDB data directory
rm -rf chroma_data/

# Recreate with new collection
python -m lexicon index examples/ --recursive
```

### Issue: PDF Parsing Failed

**Problem**: `Failed to parse PDF: ...`

**Solutions**:
- Ensure PDF is not encrypted/password protected
- Try re-saving PDF with different software
- Check file is not corrupted: `file contract.pdf`
- Verify file size is within limits (50MB default)

### Issue: Import Errors After Update

**Problem**: Import errors after updating dependencies

**Solution**:
```bash
# Clear Poetry cache
poetry cache clear pypi --all

# Remove virtual environment
poetry env remove python3.11

# Reinstall dependencies
poetry install

# Or clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Issue: Tests Failing

**Problem**: Tests fail after changes

**Solution**:
```bash
# Run tests with verbose output
pytest -v

# Run specific failing test
pytest tests/unit/test_file.py::test_name -v

# Clear pytest cache
pytest --cache-clear

# Check for import issues
python -c "import lexicon; print('OK')"
```

### Issue: Docker Compose Issues

**Problem**: Services won't start

**Solution**:
```bash
# View logs
docker-compose logs

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Remove all Docker resources (CAUTION: removes all containers/volumes)
docker system prune -a --volumes
```

### Getting Help

If you encounter issues not covered here:

1. Check existing GitHub issues: https://github.com/yourusername/lexicon/issues
2. Enable debug logging: Set `LOG_LEVEL=DEBUG` in `.env`
3. Run with verbose output: Add `-v` flag to commands
4. Create a new issue with:
   - Operating system and version
   - Python version (`python --version`)
   - Poetry version (`poetry --version`)
   - Full error message and stack trace
   - Steps to reproduce

## IDE Setup

### Visual Studio Code

Recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral)
- Even Better TOML

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": false,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "ruff.lint.args": ["--config=ruff.toml"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".ruff_cache": true
  }
}
```

### PyCharm

1. Set Python interpreter:
   - File → Settings → Project → Python Interpreter
   - Add → Poetry Environment
   - Select existing environment

2. Configure Ruff:
   - File → Settings → Tools → External Tools
   - Add new tool for Ruff format/check

3. Enable pytest:
   - File → Settings → Tools → Python Integrated Tools
   - Testing → Default test runner → pytest

### Vim/Neovim

Use with Python LSP:

```lua
-- Example neovim config
require('lspconfig').pyright.setup{
  settings = {
    python = {
      pythonPath = vim.fn.getcwd() .. '/.venv/bin/python',
    }
  }
}

-- Ruff integration
require('null-ls').setup({
  sources = {
    require('null-ls').builtins.formatting.ruff,
    require('null-ls').builtins.diagnostics.ruff,
  },
})
```

## Next Steps

After completing setup:

1. **Explore Examples**: Check `examples/` directory for sample code
2. **Read Documentation**: 
   - [CLI Guide](cli_guide.md) for command-line usage
   - [API Specification](api-spec.md) for REST API
   - [Architecture](architecture.md) for system design
   - [RAG Pipeline](rag_pipeline.md) for RAG implementation
3. **Index Sample Documents**: `python -m lexicon index examples/ --recursive`
4. **Try Analysis**: `python -m lexicon analyze examples/sample_contract.pdf`
5. **Start Development**: Create your first feature or fix an issue

## Quick Reference

### Common Commands

```bash
# Setup
poetry install                 # Install dependencies
poetry shell                   # Activate virtual environment
cp .env.example .env          # Create environment file

# Services
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose logs -f        # View logs

# CLI
python -m lexicon analyze file.pdf           # Analyze document
python -m lexicon review file.pdf            # Review contract
python -m lexicon index docs/ --recursive    # Index documents
python -m lexicon research "query"           # Research query

# API
uvicorn lexicon.api.main:app --reload       # Start API server

# Testing & Quality
pytest                        # Run tests
pytest --cov=lexicon         # Run with coverage
ruff format .                # Format code
ruff check --fix .           # Lint and fix
pre-commit run --all-files   # Run pre-commit hooks

# Dependencies
poetry add package           # Add dependency
poetry update                # Update dependencies
poetry show --outdated       # Check for updates
```

Happy coding! 🚀
