"""
Arete: A Graph-RAG system for AI tutoring of classical philosophical texts.

This package provides a comprehensive framework for building an AI tutoring system
that specializes in classical philosophy using Graph-RAG (Retrieval-Augmented Generation)
architecture with knowledge graphs.

Key Components:
- Graph: Neo4j-based knowledge graph management
- RAG: Retrieval-Augmented Generation pipeline
- Models: Data models and schemas
- Services: Business logic and orchestration
- Pipelines: Data processing and ingestion
- UI: User interface components

The system combines dense vector search, sparse retrieval, and graph traversal
to provide contextually rich and philosophically accurate responses.
"""

__version__ = "0.1.0"
__author__ = "Arete Development Team"
__email__ = "dev@arete.ai"

from .models import *
from .services import *

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
]