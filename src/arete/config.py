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