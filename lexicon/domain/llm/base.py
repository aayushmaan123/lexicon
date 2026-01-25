"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class LLMProvider(ABC):
    """Abstract base class for Large Language Model providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion from a prompt.

        Args:
            prompt: The input prompt text
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_structured(
        self, prompt: str, response_model: Type[BaseModel], **kwargs
    ) -> BaseModel:
        """Generate structured output conforming to a Pydantic model.

        Args:
            prompt: The input prompt text
            response_model: Pydantic model class for structured output
            **kwargs: Additional provider-specific parameters

        Returns:
            Instance of response_model with generated data
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: Input text to count tokens

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a given number of input and output tokens.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pass
