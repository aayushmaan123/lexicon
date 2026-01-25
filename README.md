# Lexicon

**AI-powered legal document analysis and research system**

Lexicon is a comprehensive platform for legal professionals that combines advanced AI capabilities with traditional legal document processing. It provides intelligent analysis of legal documents, contract review, legal research, and document indexing using RAG (Retrieval-Augmented Generation).

## Features

- 📄 **Document Analysis**: Comprehensive analysis of legal documents with summarization, key points extraction, and party identification
- 📝 **Contract Review**: Intelligent contract review with risk assessment, clause extraction, and unusual clause detection
- 🔍 **Legal Research**: RAG-based legal research with natural language queries and citation extraction
- 📚 **Document Indexing**: Efficient document indexing for fast semantic search and retrieval

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lexicon.git
cd lexicon

# Install dependencies using Poetry
poetry install

# Or using pip
pip install -e .
```

## Configuration

Create a `.env` file in the root directory with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://lexicon:password@localhost:5432/lexicon_db
```

See `.env.example` for all available configuration options.

## CLI Usage

Lexicon provides a powerful command-line interface for all operations.

### Getting Help

```bash
# Show general help
python -m lexicon --help

# Show version
python -m lexicon --version

# Show help for specific commands
python -m lexicon analyze --help
python -m lexicon review --help
python -m lexicon research --help
python -m lexicon index --help
```

### Document Analysis

Analyze legal documents to extract summaries, key points, parties, and dates:

```bash
# Basic analysis
python -m lexicon analyze contract.pdf

# Specify document type
python -m lexicon analyze agreement.docx --type contract

# Output as JSON
python -m lexicon analyze document.pdf --output-format json

# Save to file
python -m lexicon analyze contract.pdf --save-to-file analysis.json
```

**Output includes:**
- Document type classification
- Comprehensive summary
- Key points extraction
- Party identification
- Important dates

### Contract Review

Perform comprehensive contract review with risk assessment:

```bash
# Full contract review
python -m lexicon review contract.pdf

# Focus on specific areas
python -m lexicon review contract.pdf --focus risks
python -m lexicon review contract.pdf --focus clauses
python -m lexicon review contract.pdf --focus obligations

# Output as JSON
python -m lexicon review contract.pdf --output-format json --save-to review.json
```

**Output includes:**
- Contract type and metadata
- Parties and roles
- Risk assessment (high/medium/low severity)
- Clause extraction and analysis
- Unusual clause detection
- Key obligations

### Legal Research

Perform legal research using natural language queries:

```bash
# Basic research query
python -m lexicon research "What are the elements of breach of contract?"

# Specify jurisdiction
python -m lexicon research "Statute of limitations for personal injury" --jurisdiction California

# Focus on specific document types
python -m lexicon research "Fair use doctrine" --query-type case_law

# Save results
python -m lexicon research "Contract formation requirements" --save-to research.json

# Hide source documents
python -m lexicon research "Negligence elements" --no-sources
```

**Output includes:**
- Comprehensive answer to your query
- Confidence and relevance scores
- Legal citations
- Source documents with relevance scores

### Document Indexing

Index documents for RAG-based search:

```bash
# Index a single document
python -m lexicon index contract.pdf

# Index a directory
python -m lexicon index documents/

# Recursive indexing
python -m lexicon index documents/ --recursive

# Specify file types
python -m lexicon index documents/ --file-types pdf,docx

# Specify document type
python -m lexicon index contracts/ --document-type contract --recursive

# Continue on errors
python -m lexicon index documents/ --skip-errors
```

**Output includes:**
- Indexing progress
- Success/failure statistics
- Total chunks created
- Embedding tokens used
- Total cost

## Python API Usage

You can also use Lexicon programmatically:

### Document Analysis

```python
from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.document_analysis import DocumentAnalysisService

# Create document entity
document = Document(
    filename="contract.pdf",
    file_path="/path/to/contract.pdf",
    file_size=12345,
    document_type=DocumentType.CONTRACT,
)

# Analyze document
service = DocumentAnalysisService()
result = service.analyze_document(document)

# Access results
print(result.metadata["summary"])
print(result.metadata["key_points"])
print(result.metadata["parties"])
```

### Contract Review

```python
from lexicon.services.contract_review import ContractReviewService

service = ContractReviewService()
contract = service.review_contract(document)

# Access review results
print(f"Contract Type: {contract.contract_type}")
print(f"Parties: {contract.parties}")
print(f"Risks: {len(contract.risks)}")
for risk in contract.risks:
    print(f"- {risk.severity}: {risk.description}")
```

### Legal Research

```python
from lexicon.domain.entities.legal_research import ResearchQuery, QueryType
from lexicon.services.legal_research import LegalResearchService

# Create research query
query = ResearchQuery(
    query_text="What are the elements of negligence?",
    jurisdiction="California",
    query_type=QueryType.CASE_LAW,
)

# Perform research
service = LegalResearchService()
result = service.research(query)

# Access results
print(result.answer)
print(f"Confidence: {result.confidence_score}")
print(f"Citations: {result.citations}")
```

### Document Indexing

```python
from lexicon.services.rag_orchestrator import RAGOrchestrator

orchestrator = RAGOrchestrator()

# Index a document
doc_id = orchestrator.index_document(document)

# Query indexed documents
results = orchestrator.query(
    query_text="contract termination clauses",
    top_k=5,
    rerank=True,
)

# Get usage statistics
stats = orchestrator.get_stats()
print(f"Total cost: ${stats['total_cost']:.4f}")
```

## Architecture

Lexicon is built with a clean, modular architecture:

```
lexicon/
├── api/              # FastAPI REST API
├── cli/              # Command-line interface
├── domain/           # Domain entities and business logic
├── infrastructure/   # External integrations (LLM, vector DB, cache)
├── services/         # Application services
└── shared/           # Shared utilities and configuration
```

### Key Components

- **LLM Providers**: OpenAI GPT-4o and GPT-4o-mini, Anthropic Claude
- **Vector Store**: ChromaDB for semantic search
- **Cache**: Redis for performance optimization
- **Database**: PostgreSQL for persistence
- **Document Parsers**: PDF (PyMuPDF) and DOCX support

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lexicon --cov-report=html

# Run specific test file
pytest tests/unit/test_rag_orchestrator.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Configuration

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `PRIMARY_LLM_MODEL` | Primary model for complex tasks | `gpt-4o` |
| `SECONDARY_LLM_MODEL` | Secondary model for simple tasks | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-large` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://...` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB data directory | `./chroma_data` |
| `MONTHLY_BUDGET_USD` | Monthly API budget | `40.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- ChromaDB for vector storage
- The open-source community

## Support

For issues, questions, or contributions, please open an issue on GitHub.