# Lexicon AI

**Production-Grade Legal AI Agent Platform**

A clean-architecture Python platform for legal research and document intelligence, featuring retrieval-augmented generation (RAG), multi-agent orchestration, and enterprise compliance.

## Architecture

Lexicon follows **Clean Architecture** principles with strict separation of concerns:

```
src/lexicon/
├── domain/              # Core business logic (no external dependencies)
│   ├── entities/        # Business objects (Document, Query, AgentResponse)
│   └── interfaces/      # Abstract interfaces (ILanguageModel, IVectorStore, IRAGPipeline)
├── application/         # Use cases and orchestration
│   └── services/        # Application services
└── infrastructure/      # External adapters and implementations
    ├── adapters/        # Concrete implementations (LLM providers, vector stores)
    └── config/          # Configuration and dependency injection
```

### Design Principles

1. **Dependency Inversion**: Core domain depends on abstractions, not implementations
2. **Provider Agnostic**: All external services (LLMs, vector stores) use abstract interfaces
3. **Immutable Entities**: Domain objects are frozen dataclasses
4. **Explicit Configuration**: No magic, all settings from environment with validation
5. **Async-First**: All I/O operations are asynchronous

## Prerequisites

- Python 3.11 or higher
- pip or poetry for dependency management

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in development mode
pip install -e ".[dev]"
```

## Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `ENVIRONMENT`: deployment environment (development/staging/production)
- `LOG_LEVEL`: logging level (DEBUG/INFO/WARNING/ERROR)

## Project Structure

```
lexicon/
├── src/lexicon/              # Source code
│   ├── domain/               # Domain layer (no external dependencies)
│   │   ├── entities/         # Core business objects
│   │   └── interfaces/       # Abstract interfaces for external systems
│   ├── application/          # Application layer (use cases)
│   │   └── services/         # Application services
│   └── infrastructure/       # Infrastructure layer (adapters)
│       ├── adapters/         # Concrete implementations
│       └── config/           # Configuration management
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── pyproject.toml            # Project configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Development

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff src tests

# Type checking
mypy src
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/lexicon --cov-report=html

# Run specific test file
pytest tests/unit/test_entities.py
```

## Phase 1 Scope (Current)

✅ **Completed:**
- Clean architecture project structure
- Core domain entities (Document, Query, AgentResponse)
- Abstract interfaces for LLM providers (ILanguageModel)
- Abstract interfaces for RAG (IVectorStore, IDocumentRetriever, IRAGPipeline)
- Configuration management with environment variables
- Structured logging infrastructure
- Error handling with custom exceptions
- Type-safe codebase with strict mypy configuration

⏳ **Not Implemented (Phase 2):**
- Concrete LLM provider implementations (OpenAI, DeepSeek, etc.)
- Concrete vector store implementations (Pinecone, Weaviate, etc.)
- RAG pipeline implementation
- Multi-agent orchestration
- Document processing and ingestion
- API layer (if needed)
- Deployment configurations

## Architecture Decisions

### Why Clean Architecture?

Legal AI systems require:
- **Auditability**: Clear separation makes code review straightforward
- **Testability**: Domain logic can be tested without external dependencies
- **Flexibility**: Easy to swap LLM providers or vector stores
- **Compliance**: Core business logic isolated from infrastructure concerns

### Why Provider-Agnostic Interfaces?

Legal enterprises need:
- **Vendor Independence**: Not locked into specific AI providers
- **Regulatory Compliance**: Ability to use on-premise or compliant providers
- **Cost Optimization**: Can switch providers based on cost/performance
- **Risk Mitigation**: No single point of failure

## Engineering Standards

- **Python 3.11+**: Modern Python with latest type system features
- **Async-First**: All I/O operations use async/await
- **Strong Typing**: Full type annotations with strict mypy checking
- **Immutable Data**: Domain entities are frozen dataclasses
- **Clear Docstrings**: All public APIs documented with Google-style docstrings
- **No Magic**: Explicit configuration, no hidden behavior

## License

MIT

## Contributing

This is a Phase 1 scaffold. Contributions for Phase 2 implementation are welcome following the established architectural patterns.