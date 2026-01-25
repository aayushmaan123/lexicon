# Lexicon CLI User Guide

This guide provides detailed examples and best practices for using the Lexicon CLI.

## Table of Contents

- [Installation and Setup](#installation-and-setup)
- [Document Analysis](#document-analysis)
- [Contract Review](#contract-review)
- [Legal Research](#legal-research)
- [Document Indexing](#document-indexing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Installation and Setup

### Prerequisites

1. Python 3.11 or higher
2. OpenAI API key
3. (Optional) Anthropic API key for fallback
4. (Optional) Redis for caching
5. (Optional) PostgreSQL for persistence

### Environment Setup

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional but recommended
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379/0

# Model Configuration
PRIMARY_LLM_MODEL=gpt-4o
SECONDARY_LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# Budget Management
MONTHLY_BUDGET_USD=40.0
ENABLE_COST_TRACKING=true
```

### Verify Installation

```bash
python -m lexicon --version
python -m lexicon --help
```

## Document Analysis

The `analyze` command performs comprehensive analysis of legal documents.

### Basic Usage

```bash
# Analyze a contract
python -m lexicon analyze contract.pdf

# Analyze a DOCX file
python -m lexicon analyze agreement.docx
```

### Advanced Options

```bash
# Specify document type for better analysis
python -m lexicon analyze employment_agreement.pdf --type contract

# Output as JSON for programmatic use
python -m lexicon analyze contract.pdf --output-format json

# Save to file
python -m lexicon analyze contract.pdf --save-to-file analysis.json

# Combine options
python -m lexicon analyze nda.pdf \
  --type contract \
  --output-format json \
  --save-to-file nda_analysis.json
```

### Understanding the Output

#### Text Format

```
==============================================================================
DOCUMENT ANALYSIS: contract.pdf
==============================================================================

DOCUMENT INFORMATION
------------------------------------------------------------------------------
Type: contract
Pages: 15
Characters: 45,234

SUMMARY
------------------------------------------------------------------------------
This is a Software as a Service Agreement between...

KEY POINTS
------------------------------------------------------------------------------
1. Monthly subscription fee of $5,000
2. 12-month initial term with auto-renewal
3. 30-day termination notice required
...

PARTIES
------------------------------------------------------------------------------
- Acme Corporation (Provider)
- Beta Inc. (Customer)

IMPORTANT DATES
------------------------------------------------------------------------------
- 2024-01-15: Effective Date
- 2025-01-15: Initial Term End
```

#### JSON Format

```json
{
  "filename": "contract.pdf",
  "document_type": "contract",
  "summary": "This is a Software as a Service Agreement...",
  "key_points": [
    "Monthly subscription fee of $5,000",
    "12-month initial term with auto-renewal",
    ...
  ],
  "parties": [
    {"name": "Acme Corporation", "role": "Provider"},
    {"name": "Beta Inc.", "role": "Customer"}
  ],
  "dates": [
    {"date": "2024-01-15", "description": "Effective Date"},
    ...
  ],
  "page_count": 15,
  "character_count": 45234
}
```

## Contract Review

The `review` command provides comprehensive contract review with risk assessment.

### Basic Usage

```bash
# Full contract review
python -m lexicon review contract.pdf
```

### Focus Areas

```bash
# Focus on risks only
python -m lexicon review contract.pdf --focus risks

# Focus on clauses
python -m lexicon review contract.pdf --focus clauses

# Focus on obligations
python -m lexicon review contract.pdf --focus obligations

# Review all aspects (default)
python -m lexicon review contract.pdf --focus all
```

### Output Formats

```bash
# Human-readable text (default)
python -m lexicon review contract.pdf

# JSON for integration
python -m lexicon review contract.pdf --output-format json

# Save to file
python -m lexicon review contract.pdf --save-to review_report.txt
```

### Understanding Risk Levels

The review categorizes risks into three severity levels:

- **HIGH** (🔴): Immediate attention required, significant legal or financial risk
- **MEDIUM** (🟡): Should be addressed, moderate risk
- **LOW** (🟢): Minor concerns, low risk

### Example Output

```
CONTRACT REVIEW: saas_agreement.pdf

RISK ASSESSMENT
------------------------------------------------------------------------------
!!! HIGH - Financial
Description: Unlimited liability clause could expose company to catastrophic losses
Recommendation: Add liability cap equal to 12 months of fees paid

!! MEDIUM - Legal
Description: Broad indemnification obligations with no carve-outs
Recommendation: Negotiate mutual indemnification with specific exclusions

! LOW - Operational
Description: Short 30-day payment terms may strain cash flow
Recommendation: Request standard 60-day payment terms
```

## Legal Research

The `research` command performs RAG-based legal research using your indexed documents.

### Basic Usage

```bash
# Simple research query
python -m lexicon research "What are the elements of breach of contract?"
```

### Advanced Queries

```bash
# Specify jurisdiction
python -m lexicon research \
  "Statute of limitations for personal injury claims" \
  --jurisdiction California

# Focus on specific document types
python -m lexicon research \
  "Fair use doctrine in copyright law" \
  --query-type case_law

# Complex query with all options
python -m lexicon research \
  "Requirements for valid contract formation" \
  --jurisdiction "New York" \
  --query-type contract \
  --output-format json \
  --save-to research_results.json
```

### Controlling Output

```bash
# Show source documents (default)
python -m lexicon research "negligence elements"

# Hide source documents for cleaner output
python -m lexicon research "negligence elements" --no-sources
```

### Understanding Confidence Scores

- **High Confidence (>70%)**: Strong evidence from multiple sources
- **Medium Confidence (40-70%)**: Some evidence, may need verification
- **Low Confidence (<40%)**: Limited evidence, additional research recommended

### Example Research Session

```bash
# Index legal documents first
python -m lexicon index legal_library/ --recursive

# Perform research
python -m lexicon research \
  "What constitutes good faith in contract performance?" \
  --jurisdiction "California"
```

Output:
```
LEGAL RESEARCH RESULTS

ANALYSIS METRICS
Confidence: 85.3%
Relevance: 91.2%
Sources: 8

ANSWER
Good faith in contract performance requires parties to deal honestly and fairly
with each other, avoiding conduct that would deprive the other party of the
benefits of their agreement. In California, the implied covenant of good faith
and fair dealing is implied in every contract...

CITATIONS
1. Comunale v. Traders & General Ins. Co., 50 Cal.2d 654 (1958)
2. Cal. Civ. Code § 1714
...
```

## Document Indexing

The `index` command prepares documents for RAG-based research.

### Indexing Single Documents

```bash
# Index a single file
python -m lexicon index contract.pdf

# Specify document type
python -m lexicon index employment_contract.pdf --document-type contract
```

### Indexing Directories

```bash
# Index all files in a directory (non-recursive)
python -m lexicon index contracts/

# Recursive indexing
python -m lexicon index legal_library/ --recursive

# Filter by file type
python -m lexicon index documents/ --file-types pdf
python -m lexicon index documents/ --file-types pdf,docx
```

### Advanced Indexing

```bash
# Index with specific document type
python -m lexicon index case_law/ \
  --recursive \
  --document-type case_law \
  --file-types pdf

# Skip errors to continue indexing
python -m lexicon index large_library/ \
  --recursive \
  --skip-errors

# Stop on first error
python -m lexicon index critical_docs/ \
  --no-skip-errors
```

### Understanding Indexing Output

```
Scanning for files in: legal_library/
Found 127 files to index

Indexing documents... ████████████████████████████████ 100%

INDEXING SUMMARY
Total files: 127
Successfully indexed: 125
Failed: 2
Total chunks created: 3,456
Embedding tokens: 2,891,234
Total cost: $0.3759

Failed Files:
  • corrupted.pdf: Failed to parse PDF
  • invalid.docx: Unsupported file format
```

### Cost Management

Monitor indexing costs:

```bash
# For large libraries, start with a subset
python -m lexicon index sample_docs/ --recursive

# Check the cost in the output
# Then proceed with full indexing if acceptable
python -m lexicon index full_library/ --recursive
```

## Best Practices

### Document Analysis

1. **Specify Document Type**: Use `--type` for better classification
2. **Save Results**: Use `--save-to-file` for record-keeping
3. **Use JSON**: For integration with other tools, use `--output-format json`

### Contract Review

1. **Review Incrementally**: Start with `--focus risks` for quick assessment
2. **Document Findings**: Always save review reports
3. **Cross-Reference**: Use analysis output to understand context

### Legal Research

1. **Index First**: Always index documents before researching
2. **Be Specific**: More specific queries yield better results
3. **Specify Jurisdiction**: When applicable, always include jurisdiction
4. **Check Confidence**: Low confidence scores indicate need for verification

### Document Indexing

1. **Organize First**: Structure your document library before indexing
2. **Use Document Types**: Specify contract/case_law/general for better retrieval
3. **Monitor Costs**: Start small and scale up
4. **Regular Updates**: Re-index when documents are added or updated

## Troubleshooting

### Common Issues

#### API Key Errors

```
Error: OpenAI API key not found
```

**Solution**: Ensure `.env` file exists with valid `OPENAI_API_KEY`

#### File Format Errors

```
Error: Unsupported file format: .txt
```

**Solution**: Lexicon supports PDF and DOCX only. Convert other formats first.

#### Memory Issues

```
Error: Out of memory during indexing
```

**Solution**: Index in smaller batches or reduce `--file-types` filter

#### No Research Results

```
No relevant documents found in the database
```

**Solution**: Ensure documents are indexed first using `lexicon index`

### Debug Mode

Enable detailed error messages:

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Then run commands to see detailed output
python -m lexicon analyze contract.pdf
```

### Getting Help

```bash
# General help
python -m lexicon --help

# Command-specific help
python -m lexicon analyze --help
python -m lexicon review --help
python -m lexicon research --help
python -m lexicon index --help
```

## Advanced Usage

### Batch Processing

```bash
# Process multiple files
for file in contracts/*.pdf; do
  python -m lexicon analyze "$file" \
    --output-format json \
    --save-to-file "analysis/$(basename "$file" .pdf).json"
done
```

### Integration with Scripts

```python
import subprocess
import json

# Run analysis and capture output
result = subprocess.run(
    ["python", "-m", "lexicon", "analyze", "contract.pdf", "--output-format", "json"],
    capture_output=True,
    text=True
)

# Parse JSON output
analysis = json.loads(result.stdout)
print(f"Summary: {analysis['summary']}")
```

### Pipeline Example

```bash
# 1. Index documents
python -m lexicon index contracts/ --recursive --document-type contract

# 2. Research specific topic
python -m lexicon research \
  "termination clauses in SaaS contracts" \
  --save-to termination_research.json

# 3. Review a new contract
python -m lexicon review new_contract.pdf \
  --focus risks \
  --save-to new_contract_review.txt
```

## Conclusion

The Lexicon CLI provides powerful tools for legal document processing and research. By following this guide, you can effectively analyze contracts, perform legal research, and manage your legal document library.

For more information, see the main README or open an issue on GitHub.
