"""OpenAI provider implementation."""

import logging
from typing import Type

from openai import OpenAI
from pydantic import BaseModel

from lexicon.domain.llm.base import LLMProvider
from lexicon.shared.config import settings
from lexicon.shared.token_counter.counter import TokenCounter

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""

    # Pricing per 1M tokens in USD
    PRICING = {
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        """Initialize OpenAI provider.

        Args:
            model: Model name (gpt-4o or gpt-4o-mini)
            api_key: OpenAI API key (uses settings if not provided)
        """
        self.model = model
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key)
        self.token_counter = TokenCounter(model=model)

        if model not in self.PRICING:
            raise ValueError(f"Unsupported model: {model}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion from a prompt.

        Args:
            prompt: The input prompt text
            **kwargs: Additional OpenAI API parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise

    def generate_structured(
        self, prompt: str, response_model: Type[BaseModel], **kwargs
    ) -> BaseModel:
        """Generate structured output conforming to a Pydantic model.

        Args:
            prompt: The input prompt text
            response_model: Pydantic model class for structured output
            **kwargs: Additional OpenAI API parameters

        Returns:
            Instance of response_model with generated data
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=response_model,
                **kwargs,
            )
            return response.choices[0].message.parsed

        except Exception as e:
            logger.error(f"OpenAI structured generation failed: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: Input text to count tokens

        Returns:
            Number of tokens
        """
        return self.token_counter.count_tokens(text)

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a given number of input and output tokens.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = self.PRICING[self.model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
