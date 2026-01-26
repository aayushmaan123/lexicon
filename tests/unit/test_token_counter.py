"""Unit tests for TokenCounter."""

import pytest

from lexicon.shared.token_counter.counter import TokenCounter


class TestTokenCounter:
    """Test suite for TokenCounter."""

    def test_init_with_valid_model(self):
        """Test initialization with valid OpenAI model."""
        counter = TokenCounter(model="gpt-4o")
        
        assert counter.model == "gpt-4o"
        assert counter.encoding is not None

    def test_init_with_claude_model_uses_fallback(self):
        """Test initialization with Claude model uses fallback encoding."""
        counter = TokenCounter(model="claude-3-5-sonnet-20241022")
        
        assert counter.model == "claude-3-5-sonnet-20241022"
        assert counter.encoding is not None

    def test_count_tokens_simple_text(self):
        """Test counting tokens in simple text."""
        counter = TokenCounter(model="gpt-4o")
        text = "Hello, world!"
        
        count = counter.count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_empty_string(self):
        """Test counting tokens in empty string."""
        counter = TokenCounter(model="gpt-4o")
        
        count = counter.count_tokens("")
        
        assert count == 0

    def test_count_tokens_whitespace(self):
        """Test counting tokens in whitespace."""
        counter = TokenCounter(model="gpt-4o")
        text = "   \n\t  "
        
        count = counter.count_tokens(text)
        
        assert isinstance(count, int)

    @pytest.mark.parametrize("text,expected_min", [
        ("Hello", 1),
        ("This is a test sentence.", 4),
        ("A" * 100, 10),  # Long repeated character
    ])
    def test_count_tokens_various_texts(self, text, expected_min):
        """Test counting tokens for various text inputs."""
        counter = TokenCounter(model="gpt-4o")
        
        count = counter.count_tokens(text)
        
        assert count >= expected_min

    def test_count_tokens_unicode_characters(self):
        """Test counting tokens with unicode characters."""
        counter = TokenCounter(model="gpt-4o")
        text = "Hello 世界 🌍"
        
        count = counter.count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_legal_text(self):
        """Test counting tokens in legal text."""
        counter = TokenCounter(model="gpt-4o")
        text = """
        WHEREAS, the parties hereto wish to enter into an agreement;
        NOW, THEREFORE, in consideration of the mutual covenants contained herein,
        the parties agree as follows:
        """
        
        count = counter.count_tokens(text)
        
        assert count > 20  # Should have a reasonable number of tokens

    def test_count_tokens_code_text(self):
        """Test counting tokens in code."""
        counter = TokenCounter(model="gpt-4o")
        text = """
        def example_function():
            return "Hello, world!"
        """
        
        count = counter.count_tokens(text)
        
        assert count > 5

    def test_count_tokens_special_characters(self):
        """Test counting tokens with special characters."""
        counter = TokenCounter(model="gpt-4o")
        text = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        count = counter.count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_markdown_text(self):
        """Test counting tokens in markdown."""
        counter = TokenCounter(model="gpt-4o")
        text = """
        # Heading 1
        ## Heading 2
        
        This is **bold** and this is *italic*.
        
        - List item 1
        - List item 2
        """
        
        count = counter.count_tokens(text)
        
        assert count > 10

    def test_count_tokens_consistent_results(self):
        """Test that counting the same text returns consistent results."""
        counter = TokenCounter(model="gpt-4o")
        text = "This is a consistency test."
        
        count1 = counter.count_tokens(text)
        count2 = counter.count_tokens(text)
        count3 = counter.count_tokens(text)
        
        assert count1 == count2 == count3

    @pytest.mark.parametrize("model", [
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20241022",
    ])
    def test_count_tokens_different_models(self, model):
        """Test token counting works for different models."""
        counter = TokenCounter(model=model)
        text = "This is a test message for token counting."
        
        count = counter.count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_very_long_text(self):
        """Test counting tokens in very long text."""
        counter = TokenCounter(model="gpt-4o")
        text = "This is a sentence. " * 1000  # ~5000 words
        
        count = counter.count_tokens(text)
        
        assert count > 1000  # Should have many tokens

    def test_count_tokens_with_newlines(self):
        """Test counting tokens with various newline formats."""
        counter = TokenCounter(model="gpt-4o")
        
        text1 = "Line 1\nLine 2\nLine 3"
        text2 = "Line 1\r\nLine 2\r\nLine 3"
        
        count1 = counter.count_tokens(text1)
        count2 = counter.count_tokens(text2)
        
        # Counts should be similar (newline encoding may differ slightly)
        assert abs(count1 - count2) <= 3

    def test_encoding_attribute_accessible(self):
        """Test that encoding attribute is accessible."""
        counter = TokenCounter(model="gpt-4o")
        
        assert hasattr(counter, "encoding")
        assert counter.encoding is not None
        assert hasattr(counter.encoding, "encode")
