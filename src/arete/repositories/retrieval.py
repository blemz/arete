"""
Retrieval Repository for Arete Graph-RAG system.

Provides unified retrieval interface combining dense and sparse retrieval
methods for comprehensive search capabilities. Follows the repository pattern
established in the codebase with proper abstractions and dependency injection.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

# Import types only to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.dense_retrieval_service import DenseRetrievalService, SearchResult
    from ..services.sparse_retrieval_service import SparseRetrievalService
from ..config import Settings, get_settings
from .base import BaseRepository, RepositoryError

logger = logging.getLogger(__name__)


class RetrievalMethod(Enum):
    """Available retrieval methods."""
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"


class HybridStrategy(Enum):
    """Strategies for combining dense and sparse retrieval results."""
    WEIGHTED_AVERAGE = "weighted_average"
    RANK_FUSION = "rank_fusion"
    INTERLEAVED = "interleaved"
    SCORE_THRESHOLD = "score_threshold"


@dataclass
class HybridRetrievalConfig:
    """Configuration for hybrid retrieval operations."""
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    strategy: HybridStrategy = HybridStrategy.WEIGHTED_AVERAGE
    min_dense_score: float = 0.7
    min_sparse_score: float = 0.1
    fusion_k: int = 60  # For rank fusion (RRF parameter)


class RetrievalRepositoryError(RepositoryError):
    """Base exception for retrieval repository errors."""
    pass


class RetrievalRepository(BaseRepository):
    """
    Unified retrieval repository combining dense and sparse retrieval.
    
    Provides a single interface for:
    - Dense semantic retrieval via embeddings
    - Sparse lexical retrieval via BM25/SPLADE
    - Hybrid retrieval combining both methods
    - Performance tracking and optimization
    
    Follows the established repository pattern with proper abstractions
    and dependency injection for testability and flexibility.
    """
    
    def __init__(
        self,
        dense_service: Optional["DenseRetrievalService"] = None,
        sparse_service: Optional["SparseRetrievalService"] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize retrieval repository.
        
        Args:
            dense_service: Dense retrieval service instance
            sparse_service: Sparse retrieval service instance  
            settings: Configuration settings
        """
        super().__init__()
        self.settings = settings or get_settings()
        
        # Initialize services with dependency injection
        if dense_service is None:
            # Import at runtime to avoid circular import
            from ..services.dense_retrieval_service import create_dense_retrieval_service
            self.dense_service = create_dense_retrieval_service(settings=self.settings)
        else:
            self.dense_service = dense_service
            
        if sparse_service is None:
            # Import at runtime to avoid circular import
            from ..services.sparse_retrieval_service import create_sparse_retrieval_service
            self.sparse_service = create_sparse_retrieval_service(
                retriever_type="bm25",
                settings=self.settings
            )
        else:
            self.sparse_service = sparse_service
        
        # Default hybrid configuration
        self.hybrid_config = HybridRetrievalConfig()
        
        logger.info("Initialized RetrievalRepository with dense and sparse services")
    
    async def initialize(self) -> None:
        """Initialize retrieval services and indices."""
        try:
            logger.info("Initializing retrieval repository services")
            
            # Initialize sparse retrieval index
            await self.sparse_service.initialize_index()
            
            logger.info("Retrieval repository initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval repository: {e}")
            raise RetrievalRepositoryError(f"Initialization failed: {e}") from e
    
    def search(
        self,
        query: str,
        method: RetrievalMethod = RetrievalMethod.HYBRID,
        limit: int = 10,
        min_relevance: float = 0.0,
        document_ids: Optional[List[UUID]] = None,
        chunk_types: Optional[List[str]] = None,
        hybrid_config: Optional[HybridRetrievalConfig] = None,
        **kwargs
    ) -> List["SearchResult"]:
        """
        Perform retrieval search using specified method.
        
        Args:
            query: Search query text
            method: Retrieval method (dense, sparse, or hybrid)
            limit: Maximum number of results
            min_relevance: Minimum relevance threshold
            document_ids: Optional filter by document IDs
            chunk_types: Optional filter by chunk types
            hybrid_config: Configuration for hybrid retrieval
            **kwargs: Additional method-specific parameters
            
        Returns:
            List of SearchResult objects sorted by relevance
            
        Raises:
            RetrievalRepositoryError: If search operation fails
        """
        try:
            if method == RetrievalMethod.DENSE:
                return self._dense_search(
                    query=query,
                    limit=limit,
                    min_relevance=min_relevance,
                    document_ids=document_ids,
                    chunk_types=chunk_types,
                    **kwargs
                )
            
            elif method == RetrievalMethod.SPARSE:
                return self._sparse_search(
                    query=query,
                    limit=limit,
                    min_relevance=min_relevance,
                    document_ids=document_ids,
                    chunk_types=chunk_types,
                    **kwargs
                )
            
            elif method == RetrievalMethod.HYBRID:
                return self._hybrid_search(
                    query=query,
                    limit=limit,
                    min_relevance=min_relevance,
                    document_ids=document_ids,
                    chunk_types=chunk_types,
                    hybrid_config=hybrid_config or self.hybrid_config,
                    **kwargs
                )
            
            else:
                raise ValueError(f"Unknown retrieval method: {method}")
                
        except Exception as e:
            logger.error(f"Retrieval search failed: {e}")
            raise RetrievalRepositoryError(f"Search failed: {e}") from e
    
    def _dense_search(
        self,
        query: str,
        limit: int,
        min_relevance: float,
        document_ids: Optional[List[UUID]],
        chunk_types: Optional[List[str]],
        **kwargs
    ) -> List["SearchResult"]:
        """Perform dense semantic retrieval."""
        logger.debug(f"Performing dense search for query: '{query[:50]}...'")
        
        results = self.dense_service.search_by_text(
            query=query,
            limit=limit,
            min_relevance=min_relevance,
            document_ids=document_ids,
            chunk_types=chunk_types,
            **kwargs
        )
        
        # Add metadata to indicate retrieval method
        for result in results:
            result.metadata['retrieval_method'] = 'dense'
        
        return results
    
    def _sparse_search(
        self,
        query: str,
        limit: int,
        min_relevance: float,
        document_ids: Optional[List[UUID]],
        chunk_types: Optional[List[str]],
        **kwargs
    ) -> List["SearchResult"]:
        """Perform sparse lexical retrieval."""
        logger.debug(f"Performing sparse search for query: '{query[:50]}...'")
        
        results = self.sparse_service.search(
            query=query,
            limit=limit,
            min_relevance=min_relevance,
            document_ids=document_ids,
            chunk_types=chunk_types,
            **kwargs
        )
        
        # Add metadata to indicate retrieval method
        for result in results:
            result.metadata['retrieval_method'] = 'sparse'
        
        return results
    
    def _hybrid_search(
        self,
        query: str,
        limit: int,
        min_relevance: float,
        document_ids: Optional[List[UUID]],
        chunk_types: Optional[List[str]],
        hybrid_config: HybridRetrievalConfig,
        **kwargs
    ) -> List["SearchResult"]:
        """
        Perform hybrid retrieval combining dense and sparse methods.
        
        Uses the configured hybrid strategy to combine results from
        both dense and sparse retrieval for optimal performance.
        """
        logger.debug(
            f"Performing hybrid search with strategy {hybrid_config.strategy.value} "
            f"for query: '{query[:50]}...'"
        )
        
        # Get results from both methods
        dense_results = self._dense_search(
            query=query,
            limit=limit * 2,  # Get more results for fusion
            min_relevance=hybrid_config.min_dense_score,
            document_ids=document_ids,
            chunk_types=chunk_types,
            **kwargs
        )
        
        sparse_results = self._sparse_search(
            query=query,
            limit=limit * 2,  # Get more results for fusion
            min_relevance=hybrid_config.min_sparse_score,
            document_ids=document_ids,
            chunk_types=chunk_types,
            **kwargs
        )
        
        # Combine results using configured strategy
        if hybrid_config.strategy == HybridStrategy.WEIGHTED_AVERAGE:
            combined_results = self._weighted_average_fusion(
                dense_results, sparse_results, hybrid_config
            )
        elif hybrid_config.strategy == HybridStrategy.RANK_FUSION:
            combined_results = self._reciprocal_rank_fusion(
                dense_results, sparse_results, hybrid_config
            )
        elif hybrid_config.strategy == HybridStrategy.INTERLEAVED:
            combined_results = self._interleaved_fusion(
                dense_results, sparse_results, hybrid_config
            )
        elif hybrid_config.strategy == HybridStrategy.SCORE_THRESHOLD:
            combined_results = self._score_threshold_fusion(
                dense_results, sparse_results, hybrid_config
            )
        else:
            raise ValueError(f"Unknown hybrid strategy: {hybrid_config.strategy}")
        
        # Apply final filtering and limit
        filtered_results = [
            result for result in combined_results
            if result.final_score >= min_relevance
        ]
        
        # Sort by final score and apply limit
        filtered_results.sort(key=lambda r: r.final_score, reverse=True)
        final_results = filtered_results[:limit]
        
        # Update ranking positions
        for i, result in enumerate(final_results, 1):
            result.ranking_position = i
            result.metadata['retrieval_method'] = 'hybrid'
            result.metadata['hybrid_strategy'] = hybrid_config.strategy.value
        
        logger.debug(
            f"Hybrid search completed: {len(final_results)} results "
            f"from {len(dense_results)} dense + {len(sparse_results)} sparse"
        )
        
        return final_results
    
    def _weighted_average_fusion(
        self,
        dense_results: List["SearchResult"],
        sparse_results: List["SearchResult"],
        config: HybridRetrievalConfig
    ) -> List["SearchResult"]:
        """
        Combine results using weighted average of scores.
        
        Creates a weighted combination where each result's final score
        is the weighted average of its dense and sparse scores.
        """
        # Import SearchResult at runtime to avoid circular import
        from ..services.dense_retrieval_service import SearchResult
        # Create mapping of chunk_id to results
        dense_map = {str(r.chunk.id): r for r in dense_results}
        sparse_map = {str(r.chunk.id): r for r in sparse_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(dense_map.keys()) | set(sparse_map.keys())
        
        combined_results = []
        
        for chunk_id in all_chunk_ids:
            dense_result = dense_map.get(chunk_id)
            sparse_result = sparse_map.get(chunk_id)
            
            # Calculate weighted score
            if dense_result and sparse_result:
                # Both methods found this chunk
                weighted_score = (
                    dense_result.final_score * config.dense_weight +
                    sparse_result.final_score * config.sparse_weight
                )
                base_result = dense_result  # Use dense result as base
                
            elif dense_result:
                # Only dense method found this chunk
                weighted_score = dense_result.final_score * config.dense_weight
                base_result = dense_result
                
            elif sparse_result:
                # Only sparse method found this chunk
                weighted_score = sparse_result.final_score * config.sparse_weight
                base_result = sparse_result
                
            else:
                continue  # Should not happen
            
            # Create combined result
            combined_result = SearchResult(
                chunk=base_result.chunk,
                relevance_score=base_result.relevance_score,
                query=base_result.query,
                enhanced_score=weighted_score,
                metadata={
                    **base_result.metadata,
                    'dense_score': dense_result.final_score if dense_result else 0.0,
                    'sparse_score': sparse_result.final_score if sparse_result else 0.0,
                    'weighted_score': weighted_score
                }
            )
            
            combined_results.append(combined_result)
        
        return combined_results
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List["SearchResult"],
        sparse_results: List["SearchResult"],
        config: HybridRetrievalConfig
    ) -> List["SearchResult"]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).
        
        RRF Score = Σ(1 / (k + rank)) where k is a constant (typically 60)
        """
        # Import SearchResult at runtime to avoid circular import
        from ..services.dense_retrieval_service import SearchResult
        # Create mapping of chunk_id to rank
        dense_ranks = {str(r.chunk.id): i + 1 for i, r in enumerate(dense_results)}
        sparse_ranks = {str(r.chunk.id): i + 1 for i, r in enumerate(sparse_results)}
        
        # Create mapping for quick lookup
        dense_map = {str(r.chunk.id): r for r in dense_results}
        sparse_map = {str(r.chunk.id): r for r in sparse_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(dense_map.keys()) | set(sparse_map.keys())
        
        combined_results = []
        
        for chunk_id in all_chunk_ids:
            rrf_score = 0.0
            
            # Add RRF contribution from dense results
            if chunk_id in dense_ranks:
                rrf_score += 1.0 / (config.fusion_k + dense_ranks[chunk_id])
            
            # Add RRF contribution from sparse results
            if chunk_id in sparse_ranks:
                rrf_score += 1.0 / (config.fusion_k + sparse_ranks[chunk_id])
            
            # Use the result with higher original score as base
            base_result = None
            if chunk_id in dense_map and chunk_id in sparse_map:
                base_result = (dense_map[chunk_id] 
                              if dense_map[chunk_id].final_score >= sparse_map[chunk_id].final_score
                              else sparse_map[chunk_id])
            elif chunk_id in dense_map:
                base_result = dense_map[chunk_id]
            elif chunk_id in sparse_map:
                base_result = sparse_map[chunk_id]
            
            if base_result:
                combined_result = SearchResult(
                    chunk=base_result.chunk,
                    relevance_score=base_result.relevance_score,
                    query=base_result.query,
                    enhanced_score=rrf_score,
                    metadata={
                        **base_result.metadata,
                        'rrf_score': rrf_score,
                        'dense_rank': dense_ranks.get(chunk_id, 0),
                        'sparse_rank': sparse_ranks.get(chunk_id, 0)
                    }
                )
                
                combined_results.append(combined_result)
        
        return combined_results
    
    def _interleaved_fusion(
        self,
        dense_results: List["SearchResult"],
        sparse_results: List["SearchResult"],
        config: HybridRetrievalConfig
    ) -> List["SearchResult"]:
        """
        Combine results by interleaving dense and sparse results.
        
        Alternates between dense and sparse results while avoiding duplicates.
        """
        combined_results = []
        seen_chunk_ids = set()
        
        dense_idx = 0
        sparse_idx = 0
        use_dense = True  # Start with dense results
        
        while dense_idx < len(dense_results) or sparse_idx < len(sparse_results):
            result = None
            
            if use_dense and dense_idx < len(dense_results):
                # Try to add from dense results
                candidate = dense_results[dense_idx]
                chunk_id = str(candidate.chunk.id)
                
                if chunk_id not in seen_chunk_ids:
                    result = candidate
                    seen_chunk_ids.add(chunk_id)
                
                dense_idx += 1
                
            elif sparse_idx < len(sparse_results):
                # Try to add from sparse results
                candidate = sparse_results[sparse_idx]
                chunk_id = str(candidate.chunk.id)
                
                if chunk_id not in seen_chunk_ids:
                    result = candidate
                    seen_chunk_ids.add(chunk_id)
                
                sparse_idx += 1
            
            # Add result if found
            if result:
                result.metadata['interleaved_position'] = len(combined_results) + 1
                combined_results.append(result)
            
            # Switch between dense and sparse
            use_dense = not use_dense
        
        return combined_results
    
    def _score_threshold_fusion(
        self,
        dense_results: List["SearchResult"],
        sparse_results: List["SearchResult"],
        config: HybridRetrievalConfig
    ) -> List["SearchResult"]:
        """
        Combine results using score-based thresholds.
        
        Prioritizes high-scoring results from either method,
        then combines remaining results using weighted average.
        """
        combined_results = []
        seen_chunk_ids = set()
        
        # First, add high-scoring dense results
        for result in dense_results:
            if result.final_score >= config.min_dense_score:
                chunk_id = str(result.chunk.id)
                if chunk_id not in seen_chunk_ids:
                    result.metadata['threshold_method'] = 'dense_priority'
                    combined_results.append(result)
                    seen_chunk_ids.add(chunk_id)
        
        # Then, add high-scoring sparse results not already included
        for result in sparse_results:
            if result.final_score >= config.min_sparse_score:
                chunk_id = str(result.chunk.id)
                if chunk_id not in seen_chunk_ids:
                    result.metadata['threshold_method'] = 'sparse_priority'
                    combined_results.append(result)
                    seen_chunk_ids.add(chunk_id)
        
        # Finally, add remaining results with weighted average
        remaining_dense = [r for r in dense_results if str(r.chunk.id) not in seen_chunk_ids]
        remaining_sparse = [r for r in sparse_results if str(r.chunk.id) not in seen_chunk_ids]
        
        weighted_results = self._weighted_average_fusion(
            remaining_dense, remaining_sparse, config
        )
        
        for result in weighted_results:
            result.metadata['threshold_method'] = 'weighted_remaining'
            combined_results.append(result)
        
        return combined_results
    
    def set_hybrid_config(self, config: HybridRetrievalConfig) -> None:
        """Set hybrid retrieval configuration."""
        self.hybrid_config = config
        logger.info(f"Updated hybrid retrieval configuration: {config.strategy.value}")
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get metrics from all retrieval services."""
        return {
            'dense_metrics': self.dense_service.get_metrics().get_summary(),
            'sparse_metrics': {
                'algorithm': self.sparse_service.get_algorithm_name(),
                'index_stats': self.sparse_service.get_index_statistics(),
                'retrieval_metrics': self.sparse_service.get_metrics().get_summary()
            }
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics for all services."""
        self.dense_service.reset_metrics()
        self.sparse_service.get_metrics().reset()
        logger.info("All retrieval metrics reset")


# Factory function following established pattern
def create_retrieval_repository(
    dense_service: Optional["DenseRetrievalService"] = None,
    sparse_service: Optional["SparseRetrievalService"] = None,
    settings: Optional[Settings] = None
) -> RetrievalRepository:
    """
    Create retrieval repository with dependency injection.
    
    Args:
        dense_service: Optional dense retrieval service instance
        sparse_service: Optional sparse retrieval service instance
        settings: Optional configuration settings
        
    Returns:
        Configured RetrievalRepository instance
    """
    return RetrievalRepository(
        dense_service=dense_service,
        sparse_service=sparse_service,
        settings=settings
    )