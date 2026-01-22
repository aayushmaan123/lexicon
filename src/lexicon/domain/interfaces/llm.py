"""Abstract interfaces for Language Model providers.

This module defines provider-agnostic interfaces for LLM interactions.
All LLM providers (OpenAI, DeepSeek, Anthropic, etc.) must implement these interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM provider.

    Attributes:
        model_name: Name of the model to use
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        additional_params: Provider-specific parameters
    """

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    additional_params: dict[str, Any] | None = None


@dataclass(frozen=True)
class LLMMessage:
    """Represents a message in LLM conversation.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
        metadata: Optional metadata
    """

    role: str
    content: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class LLMResponse:
    """Response from LLM provider.

    Attributes:
        content: Generated text content
        model: Model that generated the response
        usage: Token usage statistics
        metadata: Additional response metadata
    """

    content: str
    model: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None


class ILanguageModel(ABC):
    """Abstract interface for Language Model providers.

    This interface ensures all LLM providers can be used interchangeably,
    following the dependency inversion principle.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Generate a response from the language model.

        Args:
            messages: List of conversation messages
            config: Optional configuration overrides

        Returns:
            LLMResponse containing the generated content

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream response from the language model.

        Args:
            messages: List of conversation messages
            config: Optional configuration overrides

        Yields:
            Response content chunks

        Raises:
            LLMError: If streaming fails
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats

        Raises:
            LLMError: If embedding fails
        """
        pass
