"""Prompt templates for legal research tasks."""

RESEARCH_QUERY_PROMPT = """You are an expert legal researcher. Answer the following legal research query using the provided context from legal documents.

Query: {query_text}
Jurisdiction: {jurisdiction}
Query Type: {query_type}
{user_context}

Context from Legal Documents:
{rag_context}

Instructions:
- Provide a comprehensive, accurate answer based on the context provided
- Cite specific sources when making claims
- If the context is insufficient, acknowledge the limitations
- Use clear, professional legal language
- Organize your answer logically with proper structure
- Include relevant case law, statutes, or regulations mentioned in the context
- Note any jurisdictional considerations

Answer:"""

EXTRACT_CITATIONS_PROMPT = """You are an expert legal researcher. Extract all legal citations from the following text.

Identify and extract:
- Case law citations (e.g., "Brown v. Board of Education, 347 U.S. 483 (1954)")
- Statute citations (e.g., "42 U.S.C. § 1983")
- Regulatory citations
- Other legal references

Return ONLY valid JSON in this exact format:
{{
    "citations": [
        {{
            "citation_text": "Full citation text",
            "type": "case|statute|regulation|other",
            "context": "Brief context where citation appears"
        }}
    ]
}}

Text to analyze:
{text}

JSON Response:"""

SYNTHESIZE_ANSWER_PROMPT = """You are an expert legal researcher. Synthesize a comprehensive answer to the legal research query using the retrieved documents.

Query: {query}

Retrieved Documents:
{context}

Instructions:
- Synthesize information from all relevant documents
- Provide a clear, well-structured answer
- Support your answer with specific citations from the documents
- Address all aspects of the query
- Note any conflicting information or alternative interpretations
- Include relevant jurisdiction-specific considerations
- Assess the strength and reliability of the sources
- Provide practical guidance where appropriate

Synthesize your answer:"""

ASSESS_RELEVANCE_PROMPT = """You are an expert legal researcher. Assess the relevance of each document to the given legal research query.

Query: {query}

Documents to assess:
{documents}

Instructions:
- Evaluate how relevant each document is to answering the query
- Consider topical relevance, jurisdictional match, and authority
- Score each document from 0.0 (completely irrelevant) to 1.0 (highly relevant)
- Consider whether the document provides:
  * Direct answers to the query
  * Supporting case law or statutes
  * Relevant legal principles or doctrines
  * Applicable precedents

Return ONLY valid JSON in this exact format:
{{
    "relevance_scores": [
        {{
            "document_index": 0,
            "score": 0.85,
            "reasoning": "Brief explanation of relevance"
        }}
    ]
}}

JSON Response:"""
