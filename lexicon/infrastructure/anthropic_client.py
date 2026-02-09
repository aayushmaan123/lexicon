"""Anthropic provider implementation."""

import json
import logging
from typing import Type

from anthropic import Anthropic
from pydantic import BaseModel

from lexicon.domain.llm.base import LLMProvider
from lexicon.shared.config import settings
from lexicon.shared.token_counter.counter import TokenCounter

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic implementation of LLM provider."""

    # Pricing per 1M tokens in USD
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(
        self, model: str = "claude-3-5-sonnet-20241022", api_key: str | None = None
    ):
        """Initialize Anthropic provider.

        Args:
            model: Model name (claude-3-5-sonnet-20241022 or claude-3-haiku-20240307)
            api_key: Anthropic API key (uses settings if not provided)
        """
        self.model = model
        self.api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=self.api_key)
        # Use GPT-4 tokenizer as approximation
        self.token_counter = TokenCounter(model="gpt-4")

        if model not in self.PRICING:
            raise ValueError(f"Unsupported model: {model}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion from a prompt.

        Args:
            prompt: The input prompt text
            **kwargs: Additional Anthropic API parameters
                (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        try:
            max_tokens = kwargs.pop("max_tokens", 4096)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise

    def generate_structured(
        self, prompt: str, response_model: Type[BaseModel], **kwargs
    ) -> BaseModel:
        """Generate structured output conforming to a Pydantic model.

        Args:
            prompt: The input prompt text
            response_model: Pydantic model class for structured output
            **kwargs: Additional Anthropic API parameters

        Returns:
            Instance of response_model with generated data
        """
        try:
            # Add JSON schema to prompt for structured output
            schema = response_model.model_json_schema()
            structured_prompt = (
                f"{prompt}\n\n"
                f"Please respond with valid JSON that matches this schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )

            max_tokens = kwargs.pop("max_tokens", 4096)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": structured_prompt}],
                **kwargs,
            )

            # Parse the JSON response into the Pydantic model
            response_text = response.content[0].text
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return response_model.model_validate_json(response_text)

        except Exception as e:
            logger.error(f"Anthropic structured generation failed: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: Input text to count tokens

        Returns:
            Number of tokens (approximate using GPT-4 tokenizer)
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
