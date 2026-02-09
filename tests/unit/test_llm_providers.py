"""Unit tests for LLM providers."""

import pytest
from pydantic import BaseModel

from lexicon.infrastructure.anthropic_client import AnthropicProvider
from lexicon.infrastructure.openai_client import OpenAIProvider


class TestResponse(BaseModel):
    """Test response model for structured outputs."""
    message: str
    score: float


class TestOpenAIProvider:
    """Test suite for OpenAIProvider."""

    def test_init_with_valid_model(self, test_settings):
        """Test initialization with valid model."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"

    def test_init_with_invalid_model_raises_error(self):
        """Test initialization with invalid model raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            OpenAIProvider(model="invalid-model", api_key="test-key")
        
        assert "Unsupported model" in str(exc_info.value)

    def test_generate_returns_text(self, mock_openai_client):
        """Test generate method returns text response."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        response = provider.generate("Test prompt")
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_generate_with_kwargs(self, mock_openai_client):
        """Test generate method passes kwargs to API."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        response = provider.generate(
            "Test prompt",
            temperature=0.7,
            max_tokens=100
        )
        
        assert isinstance(response, str)
        # Verify kwargs were passed
        call_kwargs = mock_openai_client.return_value.chat.completions.create.call_args[1]
        assert call_kwargs.get("temperature") == 0.7
        assert call_kwargs.get("max_tokens") == 100

    def test_generate_structured_returns_pydantic_model(self, mock_openai_client):
        """Test generate_structured returns Pydantic model instance."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        response = provider.generate_structured(
            "Test prompt",
            response_model=TestResponse
        )
        
        assert isinstance(response, BaseModel)

    def test_generate_structured_with_missing_beta_api_raises_error(self, mock_openai_client):
        """Test generate_structured raises AttributeError when beta API unavailable."""
        # Mock beta API as unavailable
        mock_openai_client.return_value.beta = None
        
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        with pytest.raises(AttributeError) as exc_info:
            provider.generate_structured("Test prompt", TestResponse)
        
        assert "beta API" in str(exc_info.value)

    def test_count_tokens_returns_integer(self):
        """Test count_tokens returns integer token count."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        count = provider.count_tokens("This is a test message.")
        
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_empty_string_returns_zero(self):
        """Test count_tokens with empty string returns zero."""
        provider = OpenAIProvider(model="gpt-4o", api_key="test-key")
        
        count = provider.count_tokens("")
        
        assert count == 0

    @pytest.mark.parametrize("model,input_tokens,output_tokens,expected_min", [
        ("gpt-4o", 1000, 500, 0.0),
        ("gpt-4o-mini", 1000, 500, 0.0),
    ])
    def test_get_cost_calculates_correctly(self, model, input_tokens, output_tokens, expected_min):
        """Test get_cost calculates cost correctly for different models."""
        provider = OpenAIProvider(model=model, api_key="test-key")
        
        cost = provider.get_cost(input_tokens, output_tokens)
        
        assert cost >= expected_min
        assert isinstance(cost, float)

    def test_pricing_dictionary_exists(self):
        """Test that pricing dictionary is defined."""
        assert hasattr(OpenAIProvider, "PRICING")
        assert "gpt-4o" in OpenAIProvider.PRICING
        assert "gpt-4o-mini" in OpenAIProvider.PRICING


class TestAnthropicProvider:
    """Test suite for AnthropicProvider."""

    def test_init_with_valid_model(self):
        """Test initialization with valid model."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.api_key == "test-key"

    def test_init_with_invalid_model_raises_error(self):
        """Test initialization with invalid model raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AnthropicProvider(model="invalid-model", api_key="test-key")
        
        assert "Unsupported model" in str(exc_info.value)

    def test_generate_returns_text(self, mock_anthropic_client):
        """Test generate method returns text response."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        response = provider.generate("Test prompt")
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_generate_with_kwargs(self, mock_anthropic_client):
        """Test generate method passes kwargs to API."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        response = provider.generate(
            "Test prompt",
            temperature=0.5,
            max_tokens=200
        )
        
        assert isinstance(response, str)

    def test_generate_structured_returns_pydantic_model(self, mock_anthropic_client):
        """Test generate_structured returns Pydantic model instance."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        # Mock the response to return valid JSON
        mock_anthropic_client.return_value.messages.create.return_value.content = [
            type('obj', (object,), {'text': '{"message": "test", "score": 0.9}'})()
        ]
        
        response = provider.generate_structured(
            "Test prompt",
            response_model=TestResponse
        )
        
        assert isinstance(response, TestResponse)

    def test_count_tokens_returns_integer(self):
        """Test count_tokens returns integer token count."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        count = provider.count_tokens("This is a test message.")
        
        assert isinstance(count, int)
        assert count > 0

    def test_get_cost_calculates_correctly(self):
        """Test get_cost calculates cost correctly."""
        provider = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        cost = provider.get_cost(1000, 500)
        
        assert cost >= 0.0
        assert isinstance(cost, float)

    def test_pricing_dictionary_exists(self):
        """Test that pricing dictionary is defined."""
        assert hasattr(AnthropicProvider, "PRICING")
        assert "claude-3-5-sonnet-20241022" in AnthropicProvider.PRICING


class TestLLMProviderComparison:
    """Test suite comparing OpenAI and Anthropic providers."""

    def test_both_providers_implement_same_interface(self):
        """Test that both providers implement the same base interface."""
        openai = OpenAIProvider(model="gpt-4o", api_key="test-key")
        anthropic = AnthropicProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key"
        )
        
        # Both should have the same methods
        assert hasattr(openai, "generate")
        assert hasattr(anthropic, "generate")
        assert hasattr(openai, "generate_structured")
        assert hasattr(anthropic, "generate_structured")
        assert hasattr(openai, "count_tokens")
        assert hasattr(anthropic, "count_tokens")
        assert hasattr(openai, "get_cost")
        assert hasattr(anthropic, "get_cost")

    @pytest.mark.parametrize("provider_class,model", [
        (OpenAIProvider, "gpt-4o"),
        (AnthropicProvider, "claude-3-5-sonnet-20241022"),
    ])
    def test_providers_handle_empty_prompt(self, provider_class, model):
        """Test that providers handle empty prompts gracefully."""
        provider = provider_class(model=model, api_key="test-key")
        
        # Should not raise an error with empty prompt
        try:
            provider.count_tokens("")
        except Exception as e:
            pytest.fail(f"Provider raised exception on empty prompt: {e}")
