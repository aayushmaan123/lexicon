# Lexicon REST API Specification

> ⚠️ **IMPORTANT DISCLAIMER**: This API provides AI-assisted document analysis for informational purposes only. All outputs should be verified by qualified professionals. This system does NOT access public legal databases and should not be used as a substitute for legal advice.

## Table of Contents

- [Overview](#overview)
- [Base URL and Versioning](#base-url-and-versioning)
- [Authentication](#authentication)
- [Common Response Formats](#common-response-formats)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Health and Info](#health-and-info)
  - [Document Operations](#document-operations)
  - [Contract Operations](#contract-operations)
  - [Legal Research](#legal-research)
  - [Knowledge Base Management](#knowledge-base-management)
- [Data Models](#data-models)
- [Usage Examples](#usage-examples)
- [Rate Limiting](#rate-limiting)

## Overview

The Lexicon REST API provides programmatic access to document analysis and AI-assisted research capabilities. The API follows REST principles and returns JSON responses.

> **Scope Note**: This API operates only on documents you upload and index. It does not access public legal databases (LexisNexis, Westlaw, PACER, etc.).

**Key Features**:
- AI-assisted document analysis (informational outputs)
- Contract review with best-effort risk assessment
- RAG-based research over your indexed documents
- Knowledge base management
- Automatic API documentation (OpenAPI/Swagger)
- Async request processing

**Technology**: FastAPI with automatic OpenAPI schema generation

## Base URL and Versioning

### Development
```
http://localhost:8000
```

### Production (Future)
```
https://api.lexicon.example.com
```

### API Version
Current version: **v1**

All endpoints are prefixed with `/api/v1/` to support future versioning:
```
http://localhost:8000/api/v1/{resource}
```

## Authentication

### Current Status
⚠️ **Authentication is not currently implemented.** The API is open for development and testing purposes.

### Future Implementation
Planned authentication method: **Bearer Token (JWT)**

```http
Authorization: Bearer <your-jwt-token>
```

**Flow**:
1. Obtain token via `/api/v1/auth/login` endpoint
2. Include token in `Authorization` header for all requests
3. Token expires after 24 hours
4. Refresh tokens used for long-lived sessions

## Common Response Formats

### Success Response
```json
{
  "field1": "value1",
  "field2": "value2",
  ...
}
```

### Error Response
```json
{
  "error": {
    "message": "Human-readable error message",
    "type": "ErrorType",
    "details": {
      "field": "additional context"
    }
  }
}
```

### Pagination (Future)
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required (future) |
| 403 | Forbidden | Insufficient permissions (future) |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded (future) |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Types

- `ValidationError`: Request validation failed
- `NotFoundError`: Requested resource not found
- `ProcessingError`: Error processing document or query
- `ExternalServiceError`: Error from external service (LLM, database)
- `InternalError`: Unexpected server error

## Endpoints

### Health and Info

#### GET /
Get API information and documentation links.

**Response**:
```json
{
  "name": "Lexicon API",
  "version": "1.0.0",
  "description": "Legal AI Platform API",
  "docs": "/docs",
  "redoc": "/redoc",
  "openapi": "/openapi.json"
}
```

#### GET /health
Health check endpoint.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-26T10:30:00Z",
  "version": "1.0.0"
}
```

#### GET /docs
Interactive API documentation (Swagger UI).

#### GET /redoc
Alternative API documentation (ReDoc).

#### GET /openapi.json
OpenAPI 3.0 specification in JSON format.

---

### Document Operations

Base path: `/api/v1/documents`

#### POST /api/v1/documents/analyze
Upload and analyze a document.

**Request**:
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: Document file (PDF or DOCX, required)

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

**Response**: `200 OK`
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "contract.pdf",
  "document_type": "contract",
  "summary": "This is a Software as a Service Agreement between Acme Corp and Beta Inc...",
  "key_points": [
    "Monthly subscription fee of $5,000",
    "12-month initial term with auto-renewal",
    "30-day termination notice required",
    "Unlimited user licenses",
    "99.9% uptime SLA guarantee"
  ],
  "parties": [
    {
      "name": "Acme Corporation",
      "role": "Provider"
    },
    {
      "name": "Beta Inc.",
      "role": "Customer"
    }
  ],
  "dates": [
    {
      "date": "2024-01-15",
      "description": "Effective Date"
    },
    {
      "date": "2025-01-15",
      "description": "Initial Term End"
    }
  ],
  "page_count": 15,
  "metadata": {
    "classified_type": "contract",
    "language": "en",
    "processing_time_ms": 3245
  }
}
```

**Error Responses**:

`400 Bad Request` - Invalid file:
```json
{
  "error": {
    "message": "Only PDF and DOCX files are supported",
    "type": "ValidationError"
  }
}
```

`500 Internal Server Error` - Processing failed:
```json
{
  "error": {
    "message": "Failed to analyze document: Unable to parse PDF",
    "type": "ProcessingError"
  }
}
```

#### POST /api/v1/documents/summarize
Summarize document text.

**Request**:
- **Method**: POST
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "text": "Long document text to summarize..."
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/summarize" \
  -H "Content-Type: application/json" \
  -d '{"text": "This agreement is made between..."}'
```

**Response**: `200 OK`
```json
{
  "summary": "Concise summary of the provided text..."
}
```

**Error Responses**:

`400 Bad Request`:
```json
{
  "error": {
    "message": "Text cannot be empty",
    "type": "ValidationError"
  }
}
```

---

### Contract Operations

Base path: `/api/v1/contracts`

#### POST /api/v1/contracts/review
Upload and review a contract.

**Request**:
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: Contract file (PDF or DOCX, required)

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/contracts/review" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

**Response**: `200 OK`
```json
{
  "contract_id": "123e4567-e89b-12d3-a456-426614174000",
  "contract_type": "Software as a Service Agreement",
  "parties": [
    {
      "name": "Acme Corporation",
      "type": "company",
      "role": "Service Provider",
      "contact_info": null
    },
    {
      "name": "Beta Inc.",
      "type": "company",
      "role": "Customer",
      "contact_info": null
    }
  ],
  "clauses": [
    {
      "type": "payment",
      "title": "Payment Terms",
      "content": "Customer shall pay Provider $5,000 per month...",
      "page_number": 3,
      "risk_level": "low",
      "is_unusual": false
    },
    {
      "type": "liability",
      "title": "Limitation of Liability",
      "content": "In no event shall Provider's liability exceed...",
      "page_number": 8,
      "risk_level": "medium",
      "is_unusual": false
    }
  ],
  "risks": [
    {
      "category": "Financial",
      "level": "high",
      "description": "Unlimited liability clause could expose company to catastrophic losses",
      "affected_clause": "Indemnification",
      "mitigation": "Negotiate liability cap equal to 12 months of fees paid"
    },
    {
      "category": "Legal",
      "level": "medium",
      "description": "Broad confidentiality obligations with no time limit",
      "affected_clause": "Confidentiality",
      "mitigation": "Request 5-year time limit on confidentiality obligations"
    }
  ],
  "effective_date": "2024-01-15",
  "expiration_date": "2025-01-15",
  "jurisdiction": "Delaware",
  "governing_law": "Laws of the State of Delaware",
  "overall_assessment": "This is a fairly standard SaaS agreement with moderate risk. The primary concerns are the unlimited liability exposure and broad confidentiality obligations. Recommend negotiating caps and time limits."
}
```

#### POST /api/v1/contracts/{contract_id}/clauses
Extract clauses from a contract (future endpoint).

#### GET /api/v1/contracts/{contract_id}/risks
Get risk assessment for a contract (future endpoint).

---

### Legal Research

Base path: `/api/v1/research`

#### POST /api/v1/research/query
Perform legal research query.

**Request**:
- **Method**: POST
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "query_text": "What are the elements of breach of contract?",
  "jurisdiction": "California",
  "query_type": "case_law",
  "user_context": "Contract dispute case"
}
```

**Field Descriptions**:
- `query_text` (required): The research question
- `jurisdiction` (optional): Legal jurisdiction (e.g., "US", "California", "New York")
- `query_type` (optional): Type of query - `case_law`, `statute`, `general`, `precedent`, `regulatory` (default: `general`)
- `user_context` (optional): Additional context to refine the query

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/research/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What are the elements of breach of contract?",
    "jurisdiction": "California",
    "query_type": "case_law"
  }'
```

**Response**: `200 OK`
```json
{
  "answer": "In California, a breach of contract claim requires four essential elements: (1) the existence of a valid contract, (2) plaintiff's performance or excuse for non-performance, (3) defendant's breach, and (4) resulting damages to the plaintiff. Each element must be proven by the plaintiff...",
  "confidence_score": 0.89,
  "relevance_score": 0.93,
  "sources": [
    {
      "document_id": "doc_123",
      "filename": "california_contracts.pdf",
      "chunk_text": "A cause of action for breach of contract requires...",
      "relevance_score": 0.95,
      "page_number": 42
    },
    {
      "document_id": "doc_456",
      "filename": "contract_law_treatise.pdf",
      "chunk_text": "The four elements necessary to establish breach...",
      "relevance_score": 0.91,
      "page_number": 128
    }
  ],
  "citations": [
    "Richman v. Hartley, 224 Cal.App.4th 1182 (2014)",
    "Oasis West Realty, LLC v. Goldman, 51 Cal.4th 811 (2011)",
    "Cal. Civ. Code § 1549"
  ]
}
```

**Confidence Score Interpretation**:
- **High (0.7 - 1.0)**: Strong evidence from multiple sources
- **Medium (0.4 - 0.7)**: Some evidence, may need verification
- **Low (0.0 - 0.4)**: Limited evidence, additional research recommended

**Error Responses**:

`400 Bad Request`:
```json
{
  "error": {
    "message": "Query text cannot be empty",
    "type": "ValidationError"
  }
}
```

`500 Internal Server Error`:
```json
{
  "error": {
    "message": "Failed to execute research query: No documents indexed",
    "type": "ProcessingError",
    "details": "Please index documents before performing research"
  }
}
```

---

### Knowledge Base Management

Base path: `/api/v1/knowledge-base`

#### POST /api/v1/knowledge-base/index
Index a document into the knowledge base.

**Request**:
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: Document file (PDF or DOCX, required)
  - `document_type`: Document type (optional, default: "general")

**Query Parameters**:
- `document_type`: `contract`, `case_law`, or `general`

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-base/index?document_type=contract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

**Response**: `200 OK`
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "contract.pdf",
  "status": "indexed",
  "message": "Document successfully indexed with 45 chunks"
}
```

**Error Responses**:

`400 Bad Request`:
```json
{
  "error": {
    "message": "Only PDF and DOCX files are supported",
    "type": "ValidationError"
  }
}
```

#### GET /api/v1/knowledge-base/stats
Get knowledge base statistics.

**Request**:
- **Method**: GET

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/knowledge-base/stats"
```

**Response**: `200 OK`
```json
{
  "total_documents": 127,
  "total_chunks": 5834,
  "embedding_model": "text-embedding-3-large",
  "collections": [
    "lexicon_documents"
  ]
}
```

#### DELETE /api/v1/knowledge-base/documents/{document_id}
Delete a document from the knowledge base (future endpoint).

#### POST /api/v1/knowledge-base/clear
Clear the entire knowledge base (future endpoint, admin only).

---

## Data Models

### DocumentTypeEnum
```
contract | case_law | general
```

### QueryTypeEnum
```
case_law | statute | general | precedent | regulatory
```

### RiskLevelEnum
```
high | medium | low
```

### Document Analysis Response
```typescript
{
  document_id: string;
  filename: string;
  document_type: string;
  summary: string;
  key_points: string[];
  parties: Array<{
    name: string;
    role: string;
  }>;
  dates: Array<{
    date: string;  // ISO 8601 date
    description: string;
  }>;
  page_count: number | null;
  metadata: object;
}
```

### Contract Review Response
```typescript
{
  contract_id: string;
  contract_type: string;
  parties: Array<{
    name: string;
    type: string;
    role: string;
    contact_info: string | null;
  }>;
  clauses: Array<{
    type: string;
    title: string;
    content: string;
    page_number: number | null;
    risk_level: "high" | "medium" | "low";
    is_unusual: boolean;
  }>;
  risks: Array<{
    category: string;
    level: "high" | "medium" | "low";
    description: string;
    affected_clause: string | null;
    mitigation: string | null;
  }>;
  effective_date: string | null;  // ISO 8601 date
  expiration_date: string | null;  // ISO 8601 date
  jurisdiction: string | null;
  governing_law: string | null;
  overall_assessment: string;
}
```

### Research Result Response
```typescript
{
  answer: string;
  confidence_score: number;  // 0.0 to 1.0
  relevance_score: number;   // 0.0 to 1.0
  sources: Array<{
    document_id: string;
    filename: string;
    chunk_text: string;
    relevance_score: number;
    page_number: number | null;
  }>;
  citations: string[];
}
```

---

## Usage Examples

### Python with httpx

```python
import httpx

# Document Analysis
async def analyze_document(file_path: str):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = await client.post(
                "http://localhost:8000/api/v1/documents/analyze",
                files=files
            )
        return response.json()

# Legal Research
async def research_query(question: str, jurisdiction: str = None):
    async with httpx.AsyncClient() as client:
        payload = {
            "query_text": question,
            "jurisdiction": jurisdiction,
            "query_type": "general"
        }
        response = await client.post(
            "http://localhost:8000/api/v1/research/query",
            json=payload
        )
        return response.json()

# Usage
result = await analyze_document("contract.pdf")
print(result["summary"])

research = await research_query(
    "What are the elements of negligence?",
    jurisdiction="California"
)
print(research["answer"])
```

### Python with requests (sync)

```python
import requests

# Document Analysis
def analyze_document(file_path: str):
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            "http://localhost:8000/api/v1/documents/analyze",
            files=files
        )
    return response.json()

# Contract Review
def review_contract(file_path: str):
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            "http://localhost:8000/api/v1/contracts/review",
            files=files
        )
    return response.json()

# Index Document
def index_document(file_path: str, doc_type: str = "general"):
    with open(file_path, "rb") as f:
        files = {"file": f}
        params = {"document_type": doc_type}
        response = requests.post(
            "http://localhost:8000/api/v1/knowledge-base/index",
            files=files,
            params=params
        )
    return response.json()

# Get Knowledge Base Stats
def get_kb_stats():
    response = requests.get(
        "http://localhost:8000/api/v1/knowledge-base/stats"
    )
    return response.json()

# Usage
analysis = analyze_document("document.pdf")
review = review_contract("contract.pdf")
index_result = index_document("legal_doc.pdf", "case_law")
stats = get_kb_stats()
```

### JavaScript/TypeScript

```javascript
// Document Analysis
async function analyzeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(
    "http://localhost:8000/api/v1/documents/analyze",
    {
      method: "POST",
      body: formData
    }
  );
  
  return await response.json();
}

// Legal Research
async function researchQuery(queryText, jurisdiction = null) {
  const payload = {
    query_text: queryText,
    jurisdiction: jurisdiction,
    query_type: "general"
  };
  
  const response = await fetch(
    "http://localhost:8000/api/v1/research/query",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );
  
  return await response.json();
}

// Usage
const fileInput = document.querySelector('input[type="file"]');
const analysis = await analyzeDocument(fileInput.files[0]);
console.log(analysis.summary);

const research = await researchQuery(
  "What are the elements of breach of contract?",
  "California"
);
console.log(research.answer);
```

### cURL Examples

```bash
# Document Analysis
curl -X POST "http://localhost:8000/api/v1/documents/analyze" \
  -F "file=@contract.pdf"

# Contract Review
curl -X POST "http://localhost:8000/api/v1/contracts/review" \
  -F "file=@contract.pdf"

# Legal Research
curl -X POST "http://localhost:8000/api/v1/research/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What are the elements of negligence?",
    "jurisdiction": "California",
    "query_type": "case_law"
  }'

# Index Document
curl -X POST "http://localhost:8000/api/v1/knowledge-base/index?document_type=contract" \
  -F "file=@legal_doc.pdf"

# Get Knowledge Base Stats
curl -X GET "http://localhost:8000/api/v1/knowledge-base/stats"

# Health Check
curl -X GET "http://localhost:8000/health"
```

---

## Rate Limiting

### Current Status
⚠️ **Rate limiting is not currently implemented.**

### Future Implementation

**Planned Limits** (per API key):
- **Free Tier**: 100 requests/hour, 1,000 requests/day
- **Pro Tier**: 1,000 requests/hour, 10,000 requests/day
- **Enterprise**: Custom limits

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643235600
```

**429 Response**:
```json
{
  "error": {
    "message": "Rate limit exceeded. Please try again in 3600 seconds.",
    "type": "RateLimitError",
    "details": {
      "limit": 100,
      "reset_at": "2024-01-26T12:00:00Z"
    }
  }
}
```

---

## API Versioning

The API uses URL-based versioning (`/api/v1/`). When breaking changes are introduced, a new version will be released (e.g., `/api/v2/`).

**Version Support Policy** (Future):
- Current version: Fully supported
- Previous version: Supported for 12 months after new version release
- Deprecated versions: 6-month deprecation notice

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
```
http://localhost:8000/openapi.json
```

Use this specification to:
- Generate client libraries (using openapi-generator)
- Import into API testing tools (Postman, Insomnia)
- Auto-generate documentation
- Validate requests/responses

---

## Support and Feedback

For API questions, issues, or feature requests:
- GitHub Issues: [github.com/yourusername/lexicon/issues](https://github.com/yourusername/lexicon/issues)
- Documentation: [Full API Docs](http://localhost:8000/docs)
- Email: support@lexicon.example.com

---

## Changelog

### v1.0.0 (Current)
- Initial API release
- Document analysis endpoints
- Contract review endpoints
- Legal research endpoints
- Knowledge base management endpoints
- Health check endpoints
