"""Application configuration management.

This module handles loading and validating configuration from environment
variables with strong typing and clear defaults.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Environment(str, Enum):
    """Application deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AppConfig:
    """Core application configuration.

    All configuration values are loaded from environment variables.
    Sensitive values (API keys, secrets) must never have defaults.
    """

    # Environment
    environment: Environment
    log_level: LogLevel
    debug: bool

    # Application
    app_name: str = "lexicon"
    version: str = "0.1.0"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables.

        Returns:
            AppConfig instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        env_str = os.getenv("ENVIRONMENT", "development")
        try:
            environment = Environment(env_str)
        except ValueError:
            raise ValueError(
                f"Invalid ENVIRONMENT: {env_str}. "
                f"Must be one of: {[e.value for e in Environment]}"
            )

        log_level_str = os.getenv("LOG_LEVEL", "INFO")
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            raise ValueError(
                f"Invalid LOG_LEVEL: {log_level_str}. "
                f"Must be one of: {[l.value for l in LogLevel]}"
            )

        debug = os.getenv("DEBUG", "false").lower() == "true"

        return cls(
            environment=environment,
            log_level=log_level,
            debug=debug,
        )


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration for LLM providers.

    Note: API keys are intentionally not included here.
    They should be injected at runtime via secure secrets management.
    """

    default_model: str
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "LLMProviderConfig":
        """Load LLM configuration from environment variables.

        Returns:
            LLMProviderConfig instance

        Raises:
            ValueError: If required variables are missing
        """
        model = os.getenv("LLM_DEFAULT_MODEL")
        if not model:
            raise ValueError("LLM_DEFAULT_MODEL environment variable is required")

        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        timeout = int(os.getenv("LLM_TIMEOUT", "30"))

        return cls(
            default_model=model,
            default_temperature=temperature,
            default_max_tokens=max_tokens,
            timeout=timeout,
        )


@dataclass(frozen=True)
class VectorStoreConfig:
    """Configuration for vector store.

    Connection details and credentials should be injected at runtime.
    """

    collection_name: str = "legal_documents"
    embedding_dimension: int = 1536
    similarity_metric: str = "cosine"

    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        """Load vector store configuration from environment variables.

        Returns:
            VectorStoreConfig instance
        """
        collection = os.getenv("VECTOR_COLLECTION_NAME", "legal_documents")
        dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        metric = os.getenv("SIMILARITY_METRIC", "cosine")

        return cls(
            collection_name=collection,
            embedding_dimension=dimension,
            similarity_metric=metric,
        )


def load_config() -> tuple[AppConfig, LLMProviderConfig, VectorStoreConfig]:
    """Load all configuration from environment.

    Returns:
        Tuple of (AppConfig, LLMProviderConfig, VectorStoreConfig)

    Raises:
        ValueError: If configuration is invalid
    """
    app_config = AppConfig.from_env()
    llm_config = LLMProviderConfig.from_env()
    vector_config = VectorStoreConfig.from_env()

    return app_config, llm_config, vector_config
