"""Configuration management for Lexicon application."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Anthropic Configuration
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://lexicon:password@localhost:5432/lexicon_db",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(
        default=20, description="Maximum overflow connections"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_ttl: int = Field(default=3600, description="Redis cache TTL in seconds")

    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="./chroma_data", description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="lexicon_documents", description="ChromaDB collection name"
    )

    # Model Configuration
    primary_llm_model: str = Field(default="gpt-4o", description="Primary LLM model")
    secondary_llm_model: str = Field(
        default="gpt-4o-mini", description="Secondary LLM model for lighter tasks"
    )
    fallback_llm_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Fallback LLM model"
    )
    embedding_model: str = Field(
        default="text-embedding-3-large", description="Embedding model"
    )
    embedding_dimensions: int = Field(default=3072, description="Embedding dimensions")

    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")

    # Cost Management
    monthly_budget_usd: float = Field(default=40.0, description="Monthly budget in USD")
    enable_cost_tracking: bool = Field(default=True, description="Enable cost tracking")

    # Performance Configuration
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_backoff_factor: int = Field(default=2, description="Retry backoff factor")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")

    # Document Processing
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    chunk_size_contract: int = Field(default=512, description="Chunk size for contracts")
    chunk_overlap_contract: int = Field(
        default=50, description="Chunk overlap for contracts"
    )
    chunk_size_case_law: int = Field(default=1024, description="Chunk size for case law")
    chunk_overlap_case_law: int = Field(
        default=100, description="Chunk overlap for case law"
    )
    chunk_size_general: int = Field(default=768, description="Chunk size for general docs")
    chunk_overlap_general: int = Field(
        default=75, description="Chunk overlap for general docs"
    )


# Global settings instance
settings = Settings()
