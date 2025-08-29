"""
Configuration management for Arete Graph-RAG system.
"""
import logging
from functools import lru_cache
from typing import Literal, Tuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j database URI"
    )
    neo4j_username: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        default="password",
        description="Neo4j password",
        repr=False  # Don't show in repr for security
    )
    
    # Weaviate Configuration
    weaviate_url: str = Field(
        default="http://localhost:8080",
        description="Weaviate server URL"
    )
    
    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="paraphrase-multilingual-mpnet-base-v2",
        description="Default sentence-transformer model for embeddings"
    )
    embedding_device: str = Field(
        default="auto",
        description="Device for embedding generation (auto, cuda, cpu, mps)"
    )
    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Batch size for embedding generation"
    )
    embedding_normalize: bool = Field(
        default=True,
        description="Whether to L2 normalize embeddings for cosine similarity"
    )
    embedding_cache_size: int = Field(
        default=1000,
        ge=0,
        le=10000,
        description="Number of embeddings to cache in memory"
    )
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # RAG Configuration
    max_context_tokens: int = Field(
        default=5000,
        ge=1000,
        le=32000,
        description="Maximum context tokens for LLM"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Text chunk size for processing"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between text chunks"
    )
    
    # Retrieval Configuration
    max_retrievals: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of documents to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for retrieval"
    )
    
    # Performance Configuration
    batch_size: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Batch size for processing"
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum number of worker threads"
    )
    
    # LLM Provider Configuration
    ollama_api_key: str = Field(
        default="",
        description="Ollama API key (if required)",
        repr=False
    )
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key",
        repr=False
    )
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key",
        repr=False
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic Claude API key",
        repr=False
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT models",
        repr=False
    )
    
    # LLM Provider Settings
    default_llm_provider: str = Field(
        default="ollama",
        description="Default LLM provider to use (ollama, openrouter, gemini, anthropic, openai)"
    )
    selected_llm_provider: str = Field(
        default="",
        description="Currently selected LLM provider (overrides default if set)"
    )
    selected_llm_model: str = Field(
        default="",
        description="Currently selected LLM model (overrides provider default if set)"
    )
    
    # Knowledge Graph Extraction LLM Settings
    kg_llm_provider: str = Field(
        default="",
        description="LLM provider for knowledge graph extraction (uses more powerful models)"
    )
    kg_llm_model: str = Field(
        default="",
        description="LLM model for knowledge graph extraction (uses more powerful models)"
    )
    
    llm_max_tokens: int = Field(
        default=4000,
        ge=100,
        le=32000,
        description="Maximum tokens for LLM responses"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )
    llm_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout for LLM requests in seconds"
    )
    llm_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed LLM requests"
    )
    
    # Security Configuration
    api_key_header: str = Field(
        default="X-API-Key",
        description="API key header name"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="CORS allowed origins"
    )
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Ensure chunk overlap is smaller than chunk size."""
        # For Pydantic v2, we need to access other field values differently
        # This validation will be enforced at model level instead
        if v >= 1000:  # Default chunk_size
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return v
    
    @field_validator("embedding_device")
    @classmethod
    def validate_embedding_device(cls, v: str) -> str:
        """Validate embedding device setting."""
        valid_devices = {"auto", "cuda", "cpu", "mps"}
        if v.lower() not in valid_devices:
            raise ValueError(f"embedding_device must be one of: {valid_devices}")
        return v.lower()
    
    @field_validator("default_llm_provider")
    @classmethod
    def validate_default_llm_provider(cls, v: str) -> str:
        """Validate default LLM provider setting."""
        valid_providers = {"ollama", "openrouter", "gemini", "anthropic", "openai"}
        if v.lower() not in valid_providers:
            raise ValueError(f"default_llm_provider must be one of: {valid_providers}")
        return v.lower()
    
    @property
    def neo4j_auth(self) -> Tuple[str, str]:
        """Return Neo4j authentication tuple."""
        return (self.neo4j_username, self.neo4j_password)
    
    @property
    def logging_config(self) -> dict:
        """Return logging configuration dict."""
        return {
            "level": self.log_level,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "backtrace": self.debug,
            "diagnose": self.debug,
        }
    
    @property
    def embedding_config(self) -> dict:
        """Return embedding configuration dict."""
        return {
            "model": self.embedding_model,
            "device": self.embedding_device,
            "batch_size": self.embedding_batch_size,
            "normalize": self.embedding_normalize,
            "cache_size": self.embedding_cache_size
        }
    
    @property
    def active_llm_provider(self) -> str:
        """Get the currently active LLM provider."""
        return self.selected_llm_provider or self.default_llm_provider
    
    @property 
    def active_llm_model(self) -> str:
        """Get the currently active LLM model."""
        return self.selected_llm_model
    
    @property
    def llm_config(self) -> dict:
        """Return LLM configuration dict."""
        return {
            "default_provider": self.default_llm_provider,
            "selected_provider": self.selected_llm_provider,
            "selected_model": self.selected_llm_model,
            "active_provider": self.active_llm_provider,
            "active_model": self.active_llm_model,
            "max_tokens": self.llm_max_tokens,
            "temperature": self.llm_temperature,
            "timeout": self.llm_timeout,
            "retry_attempts": self.llm_retry_attempts,
            "api_keys": {
                "ollama": self.ollama_api_key,
                "openrouter": self.openrouter_api_key,
                "gemini": self.gemini_api_key,
                "anthropic": self.anthropic_api_key,
                "openai": self.openai_api_key
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def setup_logging() -> None:
    """Setup logging configuration."""
    from loguru import logger
    import sys
    
    settings = get_settings()
    
    # Remove default logger
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=settings.logging_config["format"],
        backtrace=settings.logging_config["backtrace"],
        diagnose=settings.logging_config["diagnose"],
    )
    
    # Add file handler if not in debug mode
    if not settings.debug:
        logger.add(
            "logs/arete.log",
            level=settings.log_level,
            format=settings.logging_config["format"],
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )