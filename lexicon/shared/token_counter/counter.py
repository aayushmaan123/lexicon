"""Token counting utility using tiktoken."""

import tiktoken


class TokenCounter:
    """Token counter utility for various models."""

    # Model encoding mappings
    MODEL_ENCODINGS = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "text-embedding-3-large": "cl100k_base",
        "text-embedding-3-small": "cl100k_base",
    }

    def __init__(self, model: str = "gpt-4o"):
        """Initialize token counter with a specific model.

        Args:
            model: Model name to use for token counting
        """
        self.model = model
        encoding_name = self.MODEL_ENCODINGS.get(model, "cl100k_base")
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            # Fallback to cl100k_base if specific encoding unavailable
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: Input text to count tokens

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def count_tokens_batch(self, texts: list[str]) -> list[int]:
        """Count tokens for multiple text strings.

        Args:
            texts: List of text strings

        Returns:
            List of token counts
        """
        return [self.count_tokens(text) for text in texts]
