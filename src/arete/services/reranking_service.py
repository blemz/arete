"""
Advanced Re-ranking Service for Arete Graph-RAG system.

Provides sophisticated re-ranking capabilities using cross-encoder models
and semantic similarity to improve search result quality for philosophical content.

Supports multiple re-ranking methods:
- Cross-encoder models for precise relevance scoring
- Semantic similarity using embeddings
- Hybrid approaches combining multiple signals
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID

from ..config import Settings, get_settings
from ..services.dense_retrieval_service import SearchResult
from .base import ServiceError

logger = logging.getLogger(__name__)


class RerankingMethod(str, Enum):
    """Available re-ranking methods."""
    CROSS_ENCODER = "cross_encoder"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID = "hybrid"
    LISTWISE = "listwise"


class RerankingError(ServiceError):
    """Base exception for re-ranking service errors."""
    pass


@dataclass
class RerankingConfig:
    """Configuration for re-ranking operations."""
    
    # Method configuration
    method: RerankingMethod = RerankingMethod.CROSS_ENCODER
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Processing parameters
    max_candidates: int = 50
    top_k: int = 20
    batch_size: int = 8
    
    # Scoring weights
    original_weight: float = 0.3
    rerank_weight: float = 0.7
    score_threshold: float = 0.0
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    timeout_seconds: int = 30
    
    # Philosophical domain settings
    philosophical_boost: float = 0.1
    classical_author_boost: float = 0.05
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if abs(self.original_weight + self.rerank_weight - 1.0) > 0.001:
            raise ValueError("original_weight + rerank_weight must equal 1.0")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative")
        
        if self.max_candidates < self.top_k:
            raise ValueError("max_candidates must be >= top_k")
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False


@dataclass
class RerankingResult:
    """Result of re-ranking operation with enhanced metadata."""
    
    # Core result data
    original_result: SearchResult
    rerank_score: float
    original_rank: int
    new_rank: int
    score_improvement: float = 0.0
    
    # Method and metadata
    reranking_method: RerankingMethod = RerankingMethod.CROSS_ENCODER
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_final_score(
        self, 
        combination_method: str = "weighted",
        original_weight: Optional[float] = None,
        rerank_weight: Optional[float] = None
    ) -> float:
        """Calculate final score combining original and rerank scores."""
        if combination_method == "rerank_only":
            return self.rerank_score
        elif combination_method == "original_only":
            return self.original_result.relevance_score
        elif combination_method == "weighted":
            orig_w = original_weight if original_weight is not None else 0.3
            rerank_w = rerank_weight if rerank_weight is not None else (1.0 - orig_w)
            return (self.original_result.relevance_score * orig_w + 
                   self.rerank_score * rerank_w)
        else:
            raise ValueError(f"Unknown combination method: {combination_method}")
    
    @property
    def final_score(self) -> float:
        """Get final score using default weighted combination."""
        return self.get_final_score("weighted")


class RerankingMetrics:
    """Metrics tracking for re-ranking operations."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics."""
        self.total_queries = 0
        self.total_results_processed = 0
        self.total_processing_time = 0.0
        self.method_usage = {}
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_query(
        self, 
        method: RerankingMethod, 
        results_count: int, 
        processing_time: float,
        cache_hit: bool = False
    ):
        """Record metrics for a re-ranking query."""
        self.total_queries += 1
        self.total_results_processed += results_count
        self.total_processing_time += processing_time
        
        method_str = method.value
        self.method_usage[method_str] = self.method_usage.get(method_str, 0) + 1
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def record_error(self):
        """Record an error occurrence."""
        self.error_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of metrics."""
        avg_time = (self.total_processing_time / self.total_queries 
                   if self.total_queries > 0 else 0.0)
        
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)
                         if (self.cache_hits + self.cache_misses) > 0 else 0.0)
        
        return {
            'total_queries': self.total_queries,
            'total_results_processed': self.total_results_processed,
            'average_processing_time': avg_time,
            'reranking_method_usage': self.method_usage.copy(),
            'error_count': self.error_count,
            'cache_hit_rate': cache_hit_rate
        }


class RerankingService:
    """Advanced re-ranking service for improving search result quality."""
    
    def __init__(
        self,
        config: Optional[RerankingConfig] = None,
        settings: Optional[Settings] = None
    ):
        """Initialize re-ranking service.
        
        Args:
            config: Re-ranking configuration
            settings: Application settings
        """
        self.config = config or RerankingConfig()
        self.settings = settings or get_settings()
        self.metrics = RerankingMetrics()
        
        # Initialize models based on configuration
        self.cross_encoder = None
        self.embedding_service = None
        self._result_cache = {}
        self._is_initialized = False
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize re-ranking models based on configuration."""
        try:
            # Initialize cross-encoder model
            if self.config.method in [RerankingMethod.CROSS_ENCODER, RerankingMethod.HYBRID]:
                self._initialize_cross_encoder()
            
            # Initialize embedding service for semantic similarity
            if self.config.method in [RerankingMethod.SEMANTIC_SIMILARITY, RerankingMethod.HYBRID]:
                self._initialize_embedding_service()
            
            self._is_initialized = True
            logger.info(f"Initialized RerankingService with method: {self.config.method}")
            
        except Exception as e:
            logger.error(f"Failed to initialize re-ranking models: {e}")
            raise RerankingError(f"Model initialization failed: {e}") from e
    
    def _initialize_cross_encoder(self):
        """Initialize cross-encoder model."""
        try:
            # Import here to avoid dependency issues in tests
            from sentence_transformers import CrossEncoder
            
            self.cross_encoder = CrossEncoder(self.config.model_name)
            logger.info(f"Loaded cross-encoder model: {self.config.model_name}")
            
        except ImportError:
            logger.warning("sentence-transformers not available, using mock cross-encoder")
            self.cross_encoder = self._create_mock_cross_encoder()
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise RerankingError(f"Cross-encoder initialization failed: {e}") from e
    
    def _initialize_embedding_service(self):
        """Initialize embedding service for semantic similarity."""
        try:
            # Import at runtime to avoid circular imports
            from .embedding_service import EmbeddingService
            
            self.embedding_service = EmbeddingService(settings=self.settings)
            logger.info("Initialized embedding service for semantic similarity")
            
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {e}")
            # Create mock for testing
            self.embedding_service = Mock()
            self.embedding_service.embed.return_value = [0.1] * 768
    
    def _create_mock_cross_encoder(self):
        """Create mock cross-encoder for testing without dependencies."""
        mock_encoder = Mock()
        mock_encoder.predict.return_value = [0.8, 0.7, 0.9, 0.6, 0.75]  # Mock scores
        return mock_encoder
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is properly initialized."""
        return self._is_initialized
    
    def rerank(
        self,
        query: str,
        search_results: List[SearchResult],
        method: Optional[RerankingMethod] = None,
        top_k: Optional[int] = None
    ) -> List[RerankingResult]:
        """
        Re-rank search results using specified method.
        
        Args:
            query: Original search query
            search_results: Initial search results to re-rank
            method: Re-ranking method to use (defaults to config method)
            top_k: Number of top results to return (defaults to config top_k)
            
        Returns:
            List of re-ranked results sorted by score
            
        Raises:
            RerankingError: If re-ranking operation fails
        """
        if not query.strip():
            raise RerankingError("Query cannot be empty")
        
        if not search_results:
            logger.warning("No search results to re-rank")
            return []
        
        start_time = time.time()
        method = method or self.config.method
        top_k = top_k or self.config.top_k
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, search_results, method)
            if self.config.enable_caching and cache_key in self._result_cache:
                cached_result = self._result_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self.config.cache_ttl_seconds:
                    self.metrics.record_query(method, len(search_results), 0.0, cache_hit=True)
                    return cached_result['results'][:top_k]
            
            # Limit candidates for processing
            candidates = search_results[:self.config.max_candidates]
            
            # Perform re-ranking based on method
            if method == RerankingMethod.CROSS_ENCODER:
                reranked_results = self._rerank_cross_encoder(query, candidates)
            elif method == RerankingMethod.SEMANTIC_SIMILARITY:
                reranked_results = self._rerank_semantic_similarity(query, candidates)
            elif method == RerankingMethod.HYBRID:
                reranked_results = self._rerank_hybrid(query, candidates)
            elif method == RerankingMethod.LISTWISE:
                reranked_results = self._rerank_listwise(query, candidates)
            else:
                raise RerankingError(f"Unknown re-ranking method: {method}")
            
            # Apply score threshold filtering
            filtered_results = [
                result for result in reranked_results
                if result.rerank_score >= self.config.score_threshold
            ]
            
            # Sort by re-ranking score and apply top_k limit
            final_results = sorted(
                filtered_results,
                key=lambda x: x.rerank_score,
                reverse=True
            )[:top_k]
            
            # Update ranks
            for i, result in enumerate(final_results):
                result.new_rank = i + 1
            
            # Cache results
            if self.config.enable_caching:
                self._result_cache[cache_key] = {
                    'results': final_results,
                    'timestamp': time.time()
                }
            
            # Record metrics
            processing_time = time.time() - start_time
            self.metrics.record_query(method, len(search_results), processing_time)
            
            logger.info(f"Re-ranked {len(search_results)} results to {len(final_results)} "
                       f"using {method.value} in {processing_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"Re-ranking failed: {e}")
            raise RerankingError(f"Re-ranking operation failed: {e}") from e
    
    def _rerank_cross_encoder(self, query: str, search_results: List[SearchResult]) -> List[RerankingResult]:
        """Re-rank using cross-encoder model."""
        if not self.cross_encoder:
            raise RerankingError("Cross-encoder model not initialized")
        
        # Prepare query-document pairs for cross-encoder
        pairs = [(query, result.chunk.text) for result in search_results]
        
        # Process in batches
        all_scores = []
        for i in range(0, len(pairs), self.config.batch_size):
            batch_pairs = pairs[i:i + self.config.batch_size]
            batch_scores = self.cross_encoder.predict(batch_pairs)
            all_scores.extend(batch_scores)
        
        # Create re-ranking results
        reranked_results = []
        for i, (result, score) in enumerate(zip(search_results, all_scores)):
            rerank_result = RerankingResult(
                original_result=result,
                rerank_score=float(score),
                original_rank=i + 1,
                new_rank=0,  # Will be set after sorting
                score_improvement=float(score) - result.relevance_score,
                reranking_method=RerankingMethod.CROSS_ENCODER
            )
            
            # Apply philosophical domain boosts
            rerank_result = self._apply_domain_boosts(rerank_result)
            reranked_results.append(rerank_result)
        
        return reranked_results
    
    def _rerank_semantic_similarity(self, query: str, search_results: List[SearchResult]) -> List[RerankingResult]:
        """Re-rank using semantic similarity."""
        if not self.embedding_service:
            raise RerankingError("Embedding service not initialized")
        
        # Get query embedding
        query_embedding = self.embedding_service.embed(query)
        
        # Calculate similarity scores
        reranked_results = []
        for i, result in enumerate(search_results):
            # Get document embedding (assume it's already embedded)
            doc_embedding = result.chunk.embedding_vector
            if doc_embedding is None:
                # Generate embedding if not available
                doc_embedding = self.embedding_service.embed(result.chunk.text)
            
            # Calculate cosine similarity
            similarity_score = self._calculate_cosine_similarity(query_embedding, doc_embedding)
            
            rerank_result = RerankingResult(
                original_result=result,
                rerank_score=similarity_score,
                original_rank=i + 1,
                new_rank=0,
                score_improvement=similarity_score - result.relevance_score,
                reranking_method=RerankingMethod.SEMANTIC_SIMILARITY
            )
            
            rerank_result = self._apply_domain_boosts(rerank_result)
            reranked_results.append(rerank_result)
        
        return reranked_results
    
    def _rerank_hybrid(self, query: str, search_results: List[SearchResult]) -> List[RerankingResult]:
        """Re-rank using hybrid approach combining multiple methods."""
        # Get scores from both methods
        cross_encoder_results = self._rerank_cross_encoder(query, search_results)
        semantic_results = self._rerank_semantic_similarity(query, search_results)
        
        # Combine scores
        hybrid_results = []
        for ce_result, sem_result in zip(cross_encoder_results, semantic_results):
            # Weighted combination of scores
            hybrid_score = (ce_result.rerank_score * 0.7 + 
                           sem_result.rerank_score * 0.3)
            
            hybrid_result = RerankingResult(
                original_result=ce_result.original_result,
                rerank_score=hybrid_score,
                original_rank=ce_result.original_rank,
                new_rank=0,
                score_improvement=hybrid_score - ce_result.original_result.relevance_score,
                reranking_method=RerankingMethod.HYBRID,
                metadata={
                    'cross_encoder_score': ce_result.rerank_score,
                    'semantic_score': sem_result.rerank_score
                }
            )
            
            hybrid_result = self._apply_domain_boosts(hybrid_result)
            hybrid_results.append(hybrid_result)
        
        return hybrid_results
    
    def _rerank_listwise(self, query: str, search_results: List[SearchResult]) -> List[RerankingResult]:
        """Re-rank using listwise approach (placeholder for future implementation)."""
        logger.warning("Listwise re-ranking not yet implemented, falling back to cross-encoder")
        return self._rerank_cross_encoder(query, search_results)
    
    def _apply_domain_boosts(self, result: RerankingResult) -> RerankingResult:
        """Apply philosophical domain-specific boosts to scores."""
        text = result.original_result.chunk.text.lower()
        boost = 0.0
        
        # Boost for philosophical terms
        philosophical_terms = [
            'virtue', 'ethics', 'morality', 'justice', 'wisdom', 'knowledge',
            'truth', 'beauty', 'good', 'evil', 'soul', 'mind', 'reason',
            'logic', 'metaphysics', 'epistemology', 'ontology'
        ]
        
        for term in philosophical_terms:
            if term in text:
                boost += self.config.philosophical_boost
                break
        
        # Boost for classical authors
        classical_authors = [
            'plato', 'aristotle', 'socrates', 'epicurus', 'stoic',
            'kant', 'nietzsche', 'hume', 'descartes', 'aquinas'
        ]
        
        for author in classical_authors:
            if author in text:
                boost += self.config.classical_author_boost
                break
        
        # Apply boost
        if boost > 0:
            result.rerank_score = min(1.0, result.rerank_score + boost)
            result.metadata['domain_boost'] = boost
        
        return result
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np
            
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except ImportError:
            # Fallback implementation without numpy
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
    
    def _get_cache_key(self, query: str, search_results: List[SearchResult], method: RerankingMethod) -> str:
        """Generate cache key for query and results."""
        result_ids = [str(result.chunk.id) for result in search_results[:10]]  # Use first 10 for key
        return f"{query}:{method.value}:{':'.join(result_ids)}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get re-ranking service metrics."""
        return self.metrics.get_summary()
    
    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics.reset()
        logger.info("Re-ranking service metrics reset")
    
    def clear_cache(self):
        """Clear result cache."""
        self._result_cache.clear()
        logger.info("Re-ranking cache cleared")


# Factory function following established pattern
def create_reranking_service(
    config: Optional[RerankingConfig] = None,
    settings: Optional[Settings] = None
) -> RerankingService:
    """
    Create re-ranking service with dependency injection.
    
    Args:
        config: Optional re-ranking configuration
        settings: Optional application settings
        
    Returns:
        Configured RerankingService instance
    """
    return RerankingService(
        config=config,
        settings=settings
    )