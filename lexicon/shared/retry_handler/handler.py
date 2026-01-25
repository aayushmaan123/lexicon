"""Retry logic with exponential backoff and multi-provider fallback."""

import logging
import time
from typing import Any, Callable, List

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handler for retrying operations with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: int = 2,
        initial_delay: float = 1.0,
    ):
        """Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            initial_delay: Initial delay in seconds before first retry
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_on_exceptions: tuple = (Exception,),
        **kwargs,
    ) -> Any:
        """Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            retry_on_exceptions: Tuple of exceptions to retry on
            **kwargs: Keyword arguments for the function

        Returns:
            Result from the function

        Raises:
            Exception: Last exception if all retries failed
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_on_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: "
                        f"{str(e)}. Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                    delay *= self.backoff_factor
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. "
                        f"Last error: {str(e)}"
                    )

        raise last_exception


class MultiProviderRetryHandler:
    """Handler for retrying with multiple provider fallback."""

    def __init__(
        self,
        providers: List[Any],
        max_retries_per_provider: int = 3,
        backoff_factor: int = 2,
    ):
        """Initialize multi-provider retry handler.

        Args:
            providers: List of provider instances to try in order
            max_retries_per_provider: Maximum retries per provider
            backoff_factor: Multiplier for exponential backoff
        """
        self.providers = providers
        self.retry_handler = RetryHandler(
            max_retries=max_retries_per_provider,
            backoff_factor=backoff_factor,
        )

    def execute_with_fallback(
        self,
        method_name: str,
        *args,
        retry_on_exceptions: tuple = (Exception,),
        **kwargs,
    ) -> Any:
        """Execute a method with multi-provider fallback.

        Args:
            method_name: Name of the method to call on providers
            *args: Positional arguments for the method
            retry_on_exceptions: Tuple of exceptions to retry on
            **kwargs: Keyword arguments for the method

        Returns:
            Result from the successful provider

        Raises:
            Exception: If all providers fail
        """
        last_exception = None

        for provider in self.providers:
            try:
                method = getattr(provider, method_name)
                return self.retry_handler.execute_with_retry(
                    method,
                    *args,
                    retry_on_exceptions=retry_on_exceptions,
                    **kwargs,
                )
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed: {str(e)}. "
                    f"Trying next provider..."
                )
                continue

        error_msg = f"All providers failed. Last error: {str(last_exception)}"
        logger.error(error_msg)
        raise Exception(error_msg)
