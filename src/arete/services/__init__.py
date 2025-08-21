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
from .dense_retrieval_service import (
    DenseRetrievalService,
    SearchResult,
    RetrievalMetrics,
    create_dense_retrieval_service
)
from .sparse_retrieval_service import (
    SparseRetrievalService,
    BaseSparseRetriever,
    BM25Retriever,
    SPLADERetriever,
    create_sparse_retrieval_service
)

__all__ = [
    # Embedding services
    "EmbeddingService",
    "EmbeddingServiceError", 
    "ModelNotLoadedError",
    "BatchProcessingError",
    "get_embedding_service",
    "clear_embedding_service_cache",
    # Retrieval services
    "DenseRetrievalService",
    "SparseRetrievalService",
    "BaseSparseRetriever",
    "BM25Retriever",
    "SPLADERetriever",
    "SearchResult",
    "RetrievalMetrics",
    "create_dense_retrieval_service",
    "create_sparse_retrieval_service",
    # Other services
    "ExpertValidationService",
    "KnowledgeGraphService",
]