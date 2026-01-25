"""Prompt templates for contract review and analysis tasks."""

EXTRACT_CLAUSES_PROMPT = """You are an expert contract attorney. Extract and categorize all significant clauses from the following contract.

For each clause, identify:
- Type: payment, termination, confidentiality, indemnification, liability, intellectual_property, governing_law, dispute_resolution, warranties, force_majeure, non_compete, assignment, amendment, severability, notice, or general
- Title: A clear, descriptive title for the clause
- Content: The full text of the clause
- Page number: If identifiable from the text
- Obligations: List of specific obligations or requirements imposed by the clause

Return ONLY valid JSON in this exact format:
{{
    "clauses": [
        {{
            "type": "clause_type",
            "title": "Clause Title",
            "content": "Full clause text...",
            "page_number": 1,
            "obligations": ["Obligation 1", "Obligation 2"]
        }}
    ]
}}

Focus on material clauses that affect rights, obligations, risks, or liabilities. Exclude boilerplate unless it contains unusual provisions.

Contract text:
{text}

JSON Response:"""

ANALYZE_RISK_PROMPT = """You are an expert contract risk analyst. Analyze the following contract and identify all significant risks.

For each risk, determine:
- Severity: high, medium, or low
- Category: financial, legal, operational, reputational, compliance, or performance
- Description: Clear explanation of the risk and its potential impact
- Recommendation: Specific action to mitigate or address the risk

Consider:
- Unfavorable terms or one-sided obligations
- Unlimited liability or indemnification clauses
- Broad confidentiality or non-compete provisions
- Vague or ambiguous language
- Missing protections or standard clauses
- Unusual termination conditions
- Payment terms and schedules
- Intellectual property rights
- Dispute resolution mechanisms

Return ONLY valid JSON in this exact format:
{{
    "risks": [
        {{
            "severity": "high|medium|low",
            "category": "category_name",
            "description": "Detailed risk description",
            "recommendation": "Specific recommendation"
        }}
    ]
}}

Contract text:
{text}

JSON Response:"""

EXTRACT_OBLIGATIONS_PROMPT = """You are an expert contract attorney. Extract all obligations, duties, and requirements from the following contract.

For each obligation, identify:
- The party responsible (if specified)
- The specific obligation or duty
- Any deadline or timeframe
- Any conditions or triggers

Return ONLY valid JSON in this exact format:
{{
    "obligations": [
        {{
            "party": "Party name or 'Both' or 'Either'",
            "description": "Specific obligation description",
            "deadline": "Timeframe or deadline, if any",
            "conditions": "Any conditions or triggers"
        }}
    ]
}}

Focus on actionable obligations such as:
- Payment requirements
- Delivery deadlines
- Performance standards
- Reporting requirements
- Confidentiality duties
- Non-compete restrictions
- Termination notice periods
- Indemnification obligations

Contract text:
{text}

JSON Response:"""

DETECT_UNUSUAL_CLAUSES_PROMPT = """You are an expert contract attorney. Review the following contract clauses and identify any that are unusual, non-standard, or particularly favorable/unfavorable.

Consider:
- Industry-standard practices
- Balance of rights and obligations
- Uncommon restrictions or requirements
- Overly broad or vague provisions
- Missing standard protections
- Unusually long time periods
- Atypical liability allocations
- Non-standard termination rights

For each clause provided, respond with whether it is unusual (true/false) and if true, explain why.

Return ONLY valid JSON in this exact format:
{{
    "evaluations": [
        {{
            "clause_index": 0,
            "unusual": true,
            "reason": "Explanation of why this clause is unusual"
        }}
    ]
}}

Clauses to evaluate:
{clauses_json}

JSON Response:"""

EXTRACT_CONTRACT_METADATA_PROMPT = """You are an expert contract attorney. Extract key metadata and information from the following contract.

Identify:
- Contract type (e.g., "Employment Agreement", "NDA", "Service Agreement", "Lease", "Purchase Agreement")
- All parties involved (name, type, role)
- Effective date
- Expiration or termination date
- Jurisdiction (state, country)
- Governing law
- Overall assessment (1-2 sentence summary of the contract's purpose and key terms)

Return ONLY valid JSON in this exact format:
{{
    "contract_type": "Type of contract",
    "parties": [
        {{
            "name": "Party name",
            "type": "individual|corporation|llc|partnership|government|other",
            "role": "Buyer|Seller|Employee|Employer|etc",
            "contact_info": "Contact information if available"
        }}
    ],
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "jurisdiction": "Jurisdiction or null",
    "governing_law": "Governing law description or null",
    "overall_assessment": "Brief summary of the contract"
}}

Contract text:
{text}

JSON Response:"""
