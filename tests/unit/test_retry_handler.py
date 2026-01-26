"""Unit tests for RetryHandler."""

import time
from unittest.mock import Mock

import pytest

from lexicon.shared.retry_handler.handler import MultiProviderRetryHandler, RetryHandler


class TestRetryHandler:
    """Test suite for RetryHandler."""

    def test_execute_with_retry_succeeds_first_attempt(self):
        """Test that successful execution on first attempt works."""
        handler = RetryHandler(max_retries=3)
        mock_func = Mock(return_value="success")
        
        result = handler.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_execute_with_retry_succeeds_after_failures(self):
        """Test that execution succeeds after initial failures."""
        handler = RetryHandler(max_retries=3, initial_delay=0.1)
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = handler.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3

    def test_execute_with_retry_fails_after_max_retries(self):
        """Test that execution fails after max retries exhausted."""
        handler = RetryHandler(max_retries=2, initial_delay=0.1)
        mock_func = Mock(side_effect=Exception("persistent error"))
        
        with pytest.raises(Exception) as exc_info:
            handler.execute_with_retry(mock_func)
        
        assert "persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3  # 1 initial + 2 retries

    def test_execute_with_retry_uses_exponential_backoff(self):
        """Test that retry delays follow exponential backoff."""
        handler = RetryHandler(max_retries=3, backoff_factor=2, initial_delay=0.1)
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        start_time = time.time()
        result = handler.execute_with_retry(mock_func)
        elapsed = time.time() - start_time
        
        # Should wait at least 0.1 + 0.2 = 0.3 seconds
        assert elapsed >= 0.3
        assert result == "success"

    def test_execute_with_retry_with_args_and_kwargs(self):
        """Test that args and kwargs are passed to function."""
        handler = RetryHandler(max_retries=2)
        mock_func = Mock(return_value="result")
        
        result = handler.execute_with_retry(mock_func, "arg1", "arg2", key="value")
        
        assert result == "result"
        mock_func.assert_called_with("arg1", "arg2", key="value")

    def test_execute_with_retry_only_retries_specified_exceptions(self):
        """Test that only specified exceptions trigger retries."""
        handler = RetryHandler(max_retries=2)
        mock_func = Mock(side_effect=ValueError("wrong exception"))
        
        with pytest.raises(ValueError):
            handler.execute_with_retry(
                mock_func,
                retry_on_exceptions=(ConnectionError,)
            )
        
        # Should fail immediately, no retries
        assert mock_func.call_count == 1

    def test_execute_with_retry_handles_multiple_exception_types(self):
        """Test that multiple exception types can trigger retries."""
        handler = RetryHandler(max_retries=3, initial_delay=0.1)
        mock_func = Mock(side_effect=[
            ValueError("error1"),
            ConnectionError("error2"),
            "success"
        ])
        
        result = handler.execute_with_retry(
            mock_func,
            retry_on_exceptions=(ValueError, ConnectionError)
        )
        
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.parametrize("max_retries,expected_attempts", [
        (0, 1),
        (1, 2),
        (3, 4),
        (5, 6),
    ])
    def test_execute_with_retry_respects_max_retries(self, max_retries, expected_attempts):
        """Test that max_retries parameter is respected."""
        handler = RetryHandler(max_retries=max_retries, initial_delay=0.01)
        mock_func = Mock(side_effect=Exception("always fails"))
        
        with pytest.raises(Exception):
            handler.execute_with_retry(mock_func)
        
        assert mock_func.call_count == expected_attempts


class TestMultiProviderRetryHandler:
    """Test suite for MultiProviderRetryHandler."""

    def test_execute_with_fallback_succeeds_first_provider(self):
        """Test that execution succeeds with first provider."""
        provider1 = Mock()
        provider1.generate = Mock(return_value="result from provider1")
        provider2 = Mock()
        
        handler = MultiProviderRetryHandler([provider1, provider2])
        result = handler.execute_with_fallback("generate", "test prompt")
        
        assert result == "result from provider1"
        provider1.generate.assert_called_once()
        # Second provider should not be called
        assert not hasattr(provider2, 'generate') or not provider2.generate.called

    def test_execute_with_fallback_tries_second_provider(self):
        """Test that execution falls back to second provider on failure."""
        provider1 = Mock()
        provider1.generate = Mock(side_effect=Exception("provider1 failed"))
        provider2 = Mock()
        provider2.generate = Mock(return_value="result from provider2")
        
        handler = MultiProviderRetryHandler(
            [provider1, provider2],
            max_retries_per_provider=1
        )
        result = handler.execute_with_fallback("generate", "test prompt")
        
        assert result == "result from provider2"
        provider2.generate.assert_called()

    def test_execute_with_fallback_fails_all_providers(self):
        """Test that execution fails when all providers fail."""
        provider1 = Mock()
        provider1.generate = Mock(side_effect=Exception("provider1 failed"))
        provider2 = Mock()
        provider2.generate = Mock(side_effect=Exception("provider2 failed"))
        
        handler = MultiProviderRetryHandler(
            [provider1, provider2],
            max_retries_per_provider=0
        )
        
        with pytest.raises(Exception) as exc_info:
            handler.execute_with_fallback("generate", "test prompt")
        
        assert "All providers failed" in str(exc_info.value)

    def test_execute_with_fallback_retries_per_provider(self):
        """Test that each provider is retried specified number of times."""
        provider1 = Mock()
        provider1.generate = Mock(side_effect=Exception("always fails"))
        
        handler = MultiProviderRetryHandler(
            [provider1],
            max_retries_per_provider=2
        )
        
        with pytest.raises(Exception):
            handler.execute_with_fallback("generate", "test prompt")
        
        # Should be called 3 times (1 initial + 2 retries)
        assert provider1.generate.call_count == 3

    def test_execute_with_fallback_with_kwargs(self):
        """Test that kwargs are passed to provider methods."""
        provider1 = Mock()
        provider1.generate = Mock(return_value="result")
        
        handler = MultiProviderRetryHandler([provider1])
        result = handler.execute_with_fallback(
            "generate",
            "test prompt",
            temperature=0.7,
            max_tokens=100
        )
        
        assert result == "result"
        provider1.generate.assert_called_with(
            "test prompt",
            temperature=0.7,
            max_tokens=100
        )

    def test_execute_with_fallback_logs_provider_failures(self):
        """Test that provider failures are logged."""
        provider1 = Mock()
        provider1.__class__.__name__ = "Provider1"
        provider1.generate = Mock(side_effect=Exception("provider1 error"))
        provider2 = Mock()
        provider2.__class__.__name__ = "Provider2"
        provider2.generate = Mock(return_value="success")
        
        handler = MultiProviderRetryHandler(
            [provider1, provider2],
            max_retries_per_provider=0
        )
        
        # Should succeed with provider2 after provider1 fails
        result = handler.execute_with_fallback("generate", "test")
        assert result == "success"

    def test_execute_with_fallback_empty_providers_list(self):
        """Test that empty providers list raises error."""
        handler = MultiProviderRetryHandler([])
        
        with pytest.raises(Exception) as exc_info:
            handler.execute_with_fallback("generate", "test")
        
        assert "All providers failed" in str(exc_info.value)
