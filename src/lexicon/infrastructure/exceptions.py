"""Custom exceptions for the Lexicon AI platform.

All exceptions inherit from a base LexiconError to enable
consistent error handling throughout the application.
"""


class LexiconError(Exception):
    """Base exception for all Lexicon errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(LexiconError):
    """Raised when configuration is invalid or missing."""

    pass


class LLMError(LexiconError):
    """Raised when language model operations fail."""

    pass


class VectorStoreError(LexiconError):
    """Raised when vector store operations fail."""

    pass


class RetrievalError(LexiconError):
    """Raised when document retrieval fails."""

    pass


class RAGError(LexiconError):
    """Raised when RAG pipeline fails."""

    pass


class ValidationError(LexiconError):
    """Raised when data validation fails."""

    pass
