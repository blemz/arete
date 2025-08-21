"""
Services for Arete Graph-RAG system.

This package contains service layer components that provide business logic
and coordinate between different system components.
"""

from .embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
    ModelNotLoadedError,
    BatchProcessingError,
    get_embedding_service,
    clear_embedding_service_cache
)

from .expert_validation_service import ExpertValidationService
from .knowledge_graph_service import KnowledgeGraphService

__all__ = [
    # Embedding services
    "EmbeddingService",
    "EmbeddingServiceError", 
    "ModelNotLoadedError",
    "BatchProcessingError",
    "get_embedding_service",
    "clear_embedding_service_cache",
    # Other services
    "ExpertValidationService",
    "KnowledgeGraphService",
]