"""Prompt templates for document analysis tasks."""

SUMMARIZE_DOCUMENT_PROMPT = """You are a legal document analyst. Provide a concise, professional summary of the following document.

Focus on:
- Main purpose and type of document
- Key legal implications or obligations
- Critical dates, amounts, or terms
- Main parties involved (if applicable)

Keep the summary clear and under 300 words.

Document:
{text}

Summary:"""

EXTRACT_KEY_POINTS_PROMPT = """You are a legal document analyst. Extract the key points from the following document.

Return a list of the most important points, focusing on:
- Critical obligations, rights, and duties
- Important terms, conditions, or clauses
- Significant dates, deadlines, or milestones
- Notable amounts, payments, or financial terms
- Material risks or liabilities

Format each point as a clear, standalone statement. Return 5-10 key points.

Document:
{text}

Key Points (one per line, starting with "-"):"""

EXTRACT_PARTIES_PROMPT = """You are a legal document analyst. Extract structured information about parties and dates from the following document.

Identify:
- All parties involved (individuals, companies, organizations)
- Their roles (e.g., "plaintiff", "defendant", "buyer", "seller", "contractor", "client")
- Important dates (e.g., execution date, effective date, expiration date, deadlines)
- Date descriptions (what each date represents)

Return ONLY valid JSON in this exact format:
{{
    "parties": [
        {{"name": "Party Name", "role": "Role Description"}},
        {{"name": "Another Party", "role": "Their Role"}}
    ],
    "dates": [
        {{"date": "YYYY-MM-DD or description", "description": "What this date represents"}},
        {{"date": "Another date", "description": "Description"}}
    ]
}}

If no parties or dates are found, return empty arrays.

Document:
{text}

JSON Response:"""

CLASSIFY_DOCUMENT_PROMPT = """You are a legal document classifier. Analyze the following document and classify it into ONE of these categories:

1. "contract" - Agreements, contracts, terms of service, licenses, NDAs, employment agreements, leases
2. "case_law" - Court decisions, judicial opinions, case briefs, legal precedents
3. "general" - Any other legal document (memos, correspondence, filings, policies, etc.)

Consider:
- Language patterns (contractual language, judicial language, etc.)
- Structure and format
- Purpose and context
- Parties and their relationships

Return ONLY the category name: "contract", "case_law", or "general"

Document:
{text}

Classification:"""
