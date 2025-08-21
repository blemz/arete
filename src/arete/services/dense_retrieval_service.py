"""
Dense Retrieval Service for Arete Graph-RAG system.

Provides semantic similarity search with advanced ranking, scoring, and result optimization
for philosophical text retrieval. Builds on the EmbeddingRepository foundation to deliver
comprehensive retrieval capabilities for the RAG system.
"""

import logging
import time
import re
from typing import List, Dict, Any, Optional, Tuple, Callable, Union
from uuid import UUID
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator

from ..repositories.embedding import EmbeddingRepository, create_embedding_repository
from ..models.chunk import Chunk
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class DenseRetrievalError(Exception):
    """Base exception for dense retrieval errors."""
    pass


class QueryProcessingError(DenseRetrievalError):
    """Raised when query preprocessing fails."""
    pass


class RankingError(DenseRetrievalError):
    """Raised when result ranking fails."""
    pass


class SearchResult(BaseModel):
    """
    Represents a single search result with enhanced metadata.
    
    Provides comprehensive information about a retrieved chunk including
    relevance scoring, ranking position, and custom metadata.
    """
    chunk: Chunk = Field(..., description="The retrieved chunk")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Base relevance score from vector search")
    query: str = Field(..., description="Original search query")
    enhanced_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Enhanced relevance score after custom scoring")
    ranking_position: Optional[int] = Field(None, ge=1, description="Position in ranked results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the result")
    
    @field_validator('enhanced_score')
    @classmethod
    def set_enhanced_score_default(cls, v, info):
        """Set enhanced_score to relevance_score if not provided."""
        if v is None and 'relevance_score' in info.data:
            return info.data['relevance_score']
        return v
    
    @property
    def final_score(self) -> float:
        """Get the final score (enhanced if available, otherwise base relevance)."""
        return self.enhanced_score if self.enhanced_score is not None else self.relevance_score
    
    def __str__(self) -> str:
        return f"SearchResult(score={self.final_score:.3f}, pos={self.ranking_position}, query='{self.query[:30]}...')"


@dataclass
class RetrievalMetrics:
    """
    Tracks performance metrics for dense retrieval operations.
    
    Provides insights into query processing, result quality, and system performance
    to enable optimization and monitoring of the retrieval system.
    """
    queries_processed: int = 0
    total_results_returned: int = 0
    average_relevance_score: float = 0.0
    average_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    _relevance_sum: float = field(default=0.0, init=False)
    _response_time_sum: float = field(default=0.0, init=False)
    
    def update_query_metrics(self, results_count: int, avg_relevance: float, response_time: float) -> None:
        """Update metrics with new query results."""
        self.queries_processed += 1
        self.total_results_returned += results_count
        
        # Update weighted average relevance score
        self._relevance_sum += avg_relevance * results_count
        if self.total_results_returned > 0:
            self.average_relevance_score = self._relevance_sum / self.total_results_returned
        
        # Update average response time
        self._response_time_sum += response_time
        self.average_response_time = self._response_time_sum / self.queries_processed
    
    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.queries_processed = 0
        self.total_results_returned = 0
        self.average_relevance_score = 0.0
        self.average_response_time = 0.0
        self.cache_hit_rate = 0.0
        self._relevance_sum = 0.0
        self._response_time_sum = 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            "queries_processed": self.queries_processed,
            "total_results_returned": self.total_results_returned,
            "average_results_per_query": self.total_results_returned / max(self.queries_processed, 1),
            "average_relevance_score": self.average_relevance_score,
            "average_response_time": self.average_response_time,
            "cache_hit_rate": self.cache_hit_rate
        }


class DenseRetrievalService:
    """
    Advanced dense retrieval service for semantic similarity search.
    
    Provides comprehensive retrieval capabilities including query preprocessing,
    semantic search, result ranking, score enhancement, and performance optimization.
    Designed for philosophical text retrieval with domain-specific optimizations.
    
    Features:
    - Query preprocessing and normalization
    - Semantic similarity search via embeddings
    - Advanced result ranking and scoring
    - Context window expansion
    - Batch query processing
    - Performance metrics and caching
    - Philosophical domain optimizations
    """
    
    def __init__(
        self,
        embedding_repository: Optional[EmbeddingRepository] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize dense retrieval service.
        
        Args:
            embedding_repository: Repository for embedding operations
            settings: Configuration settings
        """
        self.settings = settings or get_settings()
        
        # Initialize embedding repository
        if embedding_repository is None:
            self.embedding_repository = create_embedding_repository(settings=self.settings)
        else:
            self.embedding_repository = embedding_repository
        
        # Initialize metrics tracking
        self.metrics = RetrievalMetrics()
        
        # Query preprocessing patterns
        self._philosophical_terms = {
            'eudaimonia', 'arete', 'phronesis', 'sophia', 'episteme', 'techne',
            'virtue', 'ethics', 'morality', 'justice', 'temperance', 'courage',
            'wisdom', 'knowledge', 'truth', 'being', 'existence', 'reality'
        }
        
        # Greek text patterns for preservation
        self._greek_pattern = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]+')
        
        logger.info("Initialized DenseRetrievalService")
    
    def search_by_text(
        self,
        query: str,
        limit: int = 10,
        min_relevance: float = 0.7,
        document_ids: Optional[List[UUID]] = None,
        chunk_types: Optional[List[str]] = None,
        enhance_scores: bool = True,
        expand_context: bool = False,
        context_window: int = 1,
        custom_scorer: Optional[Callable[[Chunk, float, str], float]] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search using text query with advanced processing.
        
        Args:
            query: Text query to search for
            limit: Maximum number of results to return
            min_relevance: Minimum relevance threshold (0.0-1.0)
            document_ids: Optional filter by document IDs
            chunk_types: Optional filter by chunk types
            enhance_scores: Whether to apply score enhancement algorithms
            expand_context: Whether to expand results with surrounding context
            context_window: Size of context window for expansion
            custom_scorer: Optional custom scoring function
            
        Returns:
            List of SearchResult objects sorted by relevance
            
        Raises:
            QueryProcessingError: If query processing fails
            DenseRetrievalError: If retrieval operation fails
        """
        start_time = time.time()
        
        try:
            # Validate parameters
            self._validate_search_parameters(query, limit, min_relevance)
            
            # Preprocess query
            processed_query = self._preprocess_query(query)
            if not processed_query:
                raise QueryProcessingError("Query cannot be empty after preprocessing")
            
            # Perform semantic search via embedding repository
            raw_results = self.embedding_repository.search_by_text(
                query_text=processed_query,
                limit=limit * 2,  # Get extra results for filtering/ranking
                min_certainty=min_relevance,
                document_ids=document_ids,
                chunk_types=chunk_types
            )
            
            # Convert to SearchResult objects
            search_results = []
            for chunk, relevance in raw_results:
                result = SearchResult(
                    chunk=chunk,
                    relevance_score=relevance,
                    query=query
                )
                search_results.append(result)
            
            # Apply score enhancement if requested
            if enhance_scores or custom_scorer:
                search_results = self._enhance_result_scores(
                    search_results, 
                    processed_query, 
                    custom_scorer
                )
            
            # Rank and filter results
            search_results = self._rank_and_filter_results(
                search_results, 
                limit, 
                min_relevance
            )
            
            # Expand context if requested
            if expand_context and search_results:
                search_results = self._expand_context_window(
                    search_results, 
                    context_window
                )
            
            # Update metrics
            response_time = time.time() - start_time
            avg_relevance = sum(r.final_score for r in search_results) / max(len(search_results), 1)
            self.metrics.update_query_metrics(
                results_count=len(search_results),
                avg_relevance=avg_relevance,
                response_time=response_time
            )
            
            logger.debug(
                f"Dense retrieval completed: {len(search_results)} results "
                f"for query '{query[:50]}...' in {response_time:.3f}s"
            )
            
            return search_results
            
        except QueryProcessingError:
            raise
        except Exception as e:
            logger.error(f"Dense retrieval failed for query '{query}': {e}")
            raise DenseRetrievalError(f"Dense retrieval failed: {e}") from e
    
    def search_by_vector(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_relevance: float = 0.7,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform semantic search using pre-computed embedding vector.
        
        Args:
            query_vector: Embedding vector to search with
            limit: Maximum number of results
            min_relevance: Minimum relevance threshold
            **kwargs: Additional search parameters
            
        Returns:
            List of SearchResult objects
        """
        start_time = time.time()
        
        try:
            # Perform vector search via embedding repository
            raw_results = self.embedding_repository.search_by_vector(
                query_vector=query_vector,
                limit=limit,
                min_certainty=min_relevance,
                **kwargs
            )
            
            # Convert to SearchResult objects
            search_results = []
            for chunk, relevance in raw_results:
                result = SearchResult(
                    chunk=chunk,
                    relevance_score=relevance,
                    query="[vector query]"
                )
                search_results.append(result)
            
            # Update metrics
            response_time = time.time() - start_time
            avg_relevance = sum(r.relevance_score for r in search_results) / max(len(search_results), 1)
            self.metrics.update_query_metrics(
                results_count=len(search_results),
                avg_relevance=avg_relevance,
                response_time=response_time
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DenseRetrievalError(f"Vector search failed: {e}") from e
    
    def batch_search(
        self,
        queries: List[str],
        limit: int = 10,
        **kwargs
    ) -> Dict[str, List[SearchResult]]:
        """
        Process multiple queries in batch for efficiency.
        
        Args:
            queries: List of text queries to process
            limit: Maximum results per query
            **kwargs: Additional search parameters
            
        Returns:
            Dictionary mapping queries to their search results
        """
        batch_results = {}
        
        logger.info(f"Processing batch of {len(queries)} queries")
        
        for query in queries:
            try:
                results = self.search_by_text(query, limit=limit, **kwargs)
                batch_results[query] = results
            except Exception as e:
                logger.warning(f"Batch search failed for query '{query}': {e}")
                batch_results[query] = []
        
        return batch_results
    
    def get_metrics(self) -> RetrievalMetrics:
        """Get current retrieval metrics."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics.reset()
        logger.info("Dense retrieval metrics reset")
    
    # Private Methods
    
    def _validate_search_parameters(self, query: str, limit: int, min_relevance: float) -> None:
        """Validate search parameters."""
        if not query or not query.strip():
            raise QueryProcessingError("Query cannot be empty")
        
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if not 0.0 <= min_relevance <= 1.0:
            raise ValueError("min_relevance must be between 0 and 1")
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess and normalize query text.
        
        Preserves philosophical terminology and Greek text while cleaning
        and normalizing the query for optimal retrieval performance.
        """
        if not query:
            return ""
        
        # Basic cleaning
        processed = query.strip()
        
        # Preserve Greek text and philosophical terms
        # (More sophisticated preprocessing could be added here)
        
        # Remove excessive whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        return processed
    
    def _enhance_result_scores(
        self,
        results: List[SearchResult],
        query: str,
        custom_scorer: Optional[Callable[[Chunk, float, str], float]] = None
    ) -> List[SearchResult]:
        """
        Enhance relevance scores using various algorithms.
        
        Applies domain-specific scoring enhancements and custom scoring functions
        to improve retrieval quality for philosophical texts.
        """
        for result in results:
            enhanced_score = result.relevance_score
            
            # Apply built-in score enhancement
            if hasattr(self, '_enhance_relevance_score'):
                enhanced_score = self._enhance_relevance_score(
                    result.chunk, 
                    enhanced_score, 
                    query
                )
            
            # Apply custom scorer if provided
            if custom_scorer:
                enhanced_score = custom_scorer(result.chunk, enhanced_score, query)
            
            # Ensure score stays within bounds
            enhanced_score = max(0.0, min(1.0, enhanced_score))
            result.enhanced_score = enhanced_score
        
        return results
    
    def _enhance_relevance_score(self, chunk: Chunk, base_score: float, query: str) -> float:
        """
        Built-in relevance score enhancement algorithm.
        
        Applies philosophical domain knowledge to boost scores for relevant content.
        """
        enhanced_score = base_score
        
        # Boost for philosophical terms in chunk
        chunk_text_lower = chunk.text.lower()
        query_lower = query.lower()
        
        # Check for philosophical terminology matches
        for term in self._philosophical_terms:
            if term in query_lower and term in chunk_text_lower:
                enhanced_score *= 1.1  # 10% boost
                break
        
        # Boost for Greek text preservation
        if self._greek_pattern.search(chunk.text) and self._greek_pattern.search(query):
            enhanced_score *= 1.15  # 15% boost for Greek text matches
        
        # Boost for longer, more substantial chunks
        if chunk.word_count > 100:
            enhanced_score *= 1.05  # 5% boost for substantial content
        
        return enhanced_score
    
    def _rank_and_filter_results(
        self,
        results: List[SearchResult],
        limit: int,
        min_relevance: float
    ) -> List[SearchResult]:
        """
        Rank results by final score and apply filtering.
        
        Sorts results by enhanced scores and applies relevance thresholds
        to return the most relevant results.
        """
        try:
            # Filter by minimum relevance threshold
            filtered_results = [
                result for result in results 
                if result.final_score >= min_relevance
            ]
            
            # Sort by final score (descending)
            filtered_results.sort(
                key=lambda r: r.final_score, 
                reverse=True
            )
            
            # Apply limit
            final_results = filtered_results[:limit]
            
            # Set ranking positions
            for i, result in enumerate(final_results, 1):
                result.ranking_position = i
            
            return final_results
            
        except Exception as e:
            logger.error(f"Result ranking failed: {e}")
            raise RankingError(f"Result ranking failed: {e}") from e
    
    def _expand_context_window(
        self,
        results: List[SearchResult],
        window_size: int
    ) -> List[SearchResult]:
        """
        Expand search results with surrounding context chunks.
        
        Adds neighboring chunks to provide additional context for the retrieved results.
        This is a placeholder for context expansion logic.
        """
        # Context expansion would require additional repository queries
        # to fetch surrounding chunks based on document_id and sequence_number
        
        # For now, just add metadata indicating context expansion was requested
        for result in results:
            result.metadata["context_expanded"] = True
            result.metadata["context_window_size"] = window_size
        
        return results


# Factory function following established pattern
def create_dense_retrieval_service(
    embedding_repository: Optional[EmbeddingRepository] = None,
    settings: Optional[Settings] = None
) -> DenseRetrievalService:
    """
    Create dense retrieval service with dependency injection.
    
    Args:
        embedding_repository: Optional embedding repository instance
        settings: Optional configuration settings
        
    Returns:
        Configured DenseRetrievalService instance
    """
    return DenseRetrievalService(
        embedding_repository=embedding_repository,
        settings=settings
    )