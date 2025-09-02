"""
RAG Pipeline Service for Arete Graph-RAG system.

This service orchestrates the complete RAG pipeline:
1. Query processing and expansion
2. Multi-modal retrieval (sparse + dense + graph)
3. Result re-ranking and diversification  
4. Context composition with intelligent stitching
5. Response generation with citation integration
6. Educational accuracy validation

Provides end-to-end philosophical tutoring capabilities.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from arete.config import Settings, get_settings
from arete.services.dense_retrieval_service import DenseRetrievalService, SearchResult
from arete.services.sparse_retrieval_service import SparseRetrievalService
from arete.services.graph_traversal_service import GraphTraversalService
from arete.services.reranking_service import RerankingService
from arete.services.diversity_service import DiversityService
from arete.services.context_composition_service import ContextCompositionService, ContextResult
from arete.services.response_generation_service import ResponseGenerationService, ResponseResult
from arete.repositories.retrieval import RetrievalRepository
from .base import ServiceError

logger = logging.getLogger(__name__)


class RAGPipelineError(ServiceError):
    """Base exception for RAG pipeline errors."""
    pass


class PipelineStage(str, Enum):
    """Available RAG pipeline stages."""
    QUERY_PROCESSING = "query_processing"
    RETRIEVAL = "retrieval"
    RERANKING = "reranking"
    DIVERSIFICATION = "diversification"
    CONTEXT_COMPOSITION = "context_composition"
    RESPONSE_GENERATION = "response_generation"
    VALIDATION = "validation"


@dataclass
class RAGPipelineConfig:
    """Configuration for RAG pipeline operations."""
    
    # Retrieval settings
    max_retrieval_results: int = 50
    sparse_weight: float = 0.3
    dense_weight: float = 0.5
    graph_weight: float = 0.2
    
    # Re-ranking and diversification
    enable_reranking: bool = True
    enable_diversification: bool = True
    max_reranked_results: int = 20
    max_diversified_results: int = 15
    
    # Context composition
    max_context_tokens: int = 4000
    composition_strategy: str = "intelligent_stitching"
    
    # Response generation
    max_response_tokens: int = 2000
    temperature: float = 0.7
    enable_validation: bool = True
    
    # Performance optimization
    enable_caching: bool = True
    cache_ttl: int = 3600
    
    # Educational focus
    philosophical_domain_boost: float = 1.2
    citation_accuracy_threshold: float = 0.8


@dataclass 
class PipelineMetrics:
    """Performance metrics for pipeline execution."""
    
    total_time: float = 0.0
    retrieval_time: float = 0.0
    reranking_time: float = 0.0
    diversification_time: float = 0.0
    context_composition_time: float = 0.0
    response_generation_time: float = 0.0
    validation_time: float = 0.0
    
    # Result counts
    retrieved_results: int = 0
    reranked_results: int = 0
    diversified_results: int = 0
    final_citations: int = 0
    
    # Quality metrics
    average_relevance_score: float = 0.0
    citation_coverage: float = 0.0
    validation_score: float = 0.0


@dataclass
class RAGPipelineResult:
    """Complete result from RAG pipeline execution."""
    
    # Core results
    query: str
    response: ResponseResult
    
    # Pipeline metadata
    config_used: RAGPipelineConfig
    metrics: PipelineMetrics
    stage_completed: PipelineStage
    
    # Intermediate results (for debugging/analysis)
    retrieval_results: List[SearchResult] = field(default_factory=list)
    reranked_results: List[SearchResult] = field(default_factory=list) 
    diversified_results: List[SearchResult] = field(default_factory=list)
    context_result: Optional[ContextResult] = None
    
    # Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RAGPipelineService:
    """
    Complete RAG Pipeline Service for philosophical tutoring.
    
    Orchestrates the full retrieval-augmented generation pipeline from
    query to validated educational response with proper citations.
    """
    
    def __init__(
        self,
        dense_retrieval_service: Optional[DenseRetrievalService] = None,
        sparse_retrieval_service: Optional[SparseRetrievalService] = None,
        graph_traversal_service: Optional[GraphTraversalService] = None,
        reranking_service: Optional[RerankingService] = None,
        diversity_service: Optional[DiversityService] = None,
        context_composition_service: Optional[ContextCompositionService] = None,
        response_generation_service: Optional[ResponseGenerationService] = None,
        retrieval_repository: Optional[RetrievalRepository] = None,
        config: Optional[RAGPipelineConfig] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize RAG pipeline service.
        
        Args:
            dense_retrieval_service: Service for dense vector retrieval
            sparse_retrieval_service: Service for sparse retrieval (BM25, SPLADE)
            graph_traversal_service: Service for graph-based retrieval
            reranking_service: Service for result re-ranking
            diversity_service: Service for result diversification
            context_composition_service: Service for context composition
            response_generation_service: Service for response generation
            retrieval_repository: Repository for hybrid retrieval coordination
            config: Pipeline configuration
            settings: Application settings
        """
        self.config = config or RAGPipelineConfig()
        self.settings = settings or get_settings()
        
        # Initialize services (create defaults if not provided)
        self.dense_retrieval = dense_retrieval_service
        self.sparse_retrieval = sparse_retrieval_service  
        self.graph_traversal = graph_traversal_service
        self.reranking_service = reranking_service
        self.diversity_service = diversity_service
        self.context_composition = context_composition_service
        self.response_generation = response_generation_service
        self.retrieval_repository = retrieval_repository
        
        # Pipeline caching
        self._pipeline_cache: Dict[str, RAGPipelineResult] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        logger.info(
            f"Initialized RAGPipelineService with config: "
            f"max_retrieval={self.config.max_retrieval_results}, "
            f"max_response_tokens={self.config.max_response_tokens}"
        )
    
    async def execute_pipeline(
        self,
        query: str,
        config: Optional[RAGPipelineConfig] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RAGPipelineResult:
        """
        Execute the complete RAG pipeline for a query.
        
        Args:
            query: User query to process
            config: Optional pipeline configuration override
            user_context: Optional user context (student level, preferences, etc.)
            
        Returns:
            Complete pipeline result with response and metadata
            
        Raises:
            RAGPipelineError: If pipeline execution fails
        """
        start_time = time.time()
        pipeline_config = config or self.config
        metrics = PipelineMetrics()
        
        try:
            # Check cache if enabled
            if pipeline_config.enable_caching:
                cache_key = self._generate_cache_key(query, pipeline_config, user_context)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.debug(f"Returning cached pipeline result for query: {query[:50]}...")
                    return cached_result
            
            logger.info(f"Executing RAG pipeline for query: {query[:100]}...")
            
            # Stage 1: Query Processing and Retrieval
            stage_start = time.time()
            retrieval_results = await self._execute_retrieval_stage(
                query, pipeline_config, user_context
            )
            metrics.retrieval_time = time.time() - stage_start
            metrics.retrieved_results = len(retrieval_results)
            
            if not retrieval_results:
                logger.warning(f"No retrieval results found for query: {query}")
                return self._create_empty_result(
                    query, pipeline_config, metrics, PipelineStage.RETRIEVAL,
                    errors=["No relevant documents found"]
                )
            
            # Stage 2: Re-ranking
            reranked_results = retrieval_results
            if pipeline_config.enable_reranking and self.reranking_service:
                stage_start = time.time()
                reranked_results = await self._execute_reranking_stage(
                    query, retrieval_results, pipeline_config
                )
                metrics.reranking_time = time.time() - stage_start
                metrics.reranked_results = len(reranked_results)
            
            # Stage 3: Diversification
            diversified_results = reranked_results
            if pipeline_config.enable_diversification and self.diversity_service:
                stage_start = time.time()
                diversified_results = await self._execute_diversification_stage(
                    query, reranked_results, pipeline_config
                )
                metrics.diversification_time = time.time() - stage_start
                metrics.diversified_results = len(diversified_results)
            
            # Stage 4: Context Composition
            stage_start = time.time()
            context_result = await self._execute_context_composition_stage(
                query, diversified_results, pipeline_config
            )
            metrics.context_composition_time = time.time() - stage_start
            
            # Stage 5: Response Generation
            stage_start = time.time()
            response_result = await self._execute_response_generation_stage(
                query, context_result, pipeline_config
            )
            metrics.response_generation_time = time.time() - stage_start
            metrics.final_citations = len(response_result.citations)
            
            # Calculate final metrics
            metrics.total_time = time.time() - start_time
            metrics.average_relevance_score = self._calculate_average_relevance(diversified_results)
            metrics.citation_coverage = len(response_result.citations) / max(len(context_result.citations), 1)
            metrics.validation_score = response_result.validation.accuracy_score
            
            # Create final result
            pipeline_result = RAGPipelineResult(
                query=query,
                response=response_result,
                config_used=pipeline_config,
                metrics=metrics,
                stage_completed=PipelineStage.VALIDATION,
                retrieval_results=retrieval_results,
                reranked_results=reranked_results,
                diversified_results=diversified_results,
                context_result=context_result
            )
            
            # Cache result if enabled
            if pipeline_config.enable_caching and cache_key:
                self._cache_result(cache_key, pipeline_result)
            
            logger.info(
                f"RAG pipeline completed successfully: {metrics.total_time:.3f}s total, "
                f"{len(diversified_results)} results, {len(response_result.citations)} citations"
            )
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"RAG pipeline execution failed: {e}")
            raise RAGPipelineError(f"Pipeline execution failed: {e}") from e
    
    async def execute_pipeline_batch(
        self,
        queries: List[str],
        config: Optional[RAGPipelineConfig] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[RAGPipelineResult]:
        """
        Execute pipeline for multiple queries in batch.
        
        Args:
            queries: List of queries to process
            config: Optional pipeline configuration
            user_context: Optional user context
            
        Returns:
            List of pipeline results
        """
        import asyncio
        
        tasks = [
            self.execute_pipeline(query, config, user_context)
            for query in queries
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch pipeline failed for query '{queries[i]}': {result}")
                    # Create error result
                    error_result = self._create_empty_result(
                        queries[i], config or self.config, PipelineMetrics(),
                        PipelineStage.QUERY_PROCESSING, errors=[str(result)]
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch pipeline execution failed: {e}")
            raise RAGPipelineError(f"Batch execution failed: {e}") from e
    
    async def _execute_retrieval_stage(
        self,
        query: str,
        config: RAGPipelineConfig,
        user_context: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Execute multi-modal retrieval stage."""
        logger.debug(f"Executing retrieval stage for query: {query[:50]}...")
        
        # Use retrieval repository for coordinated hybrid retrieval if available
        if self.retrieval_repository:
            return await self.retrieval_repository.hybrid_search(
                query=query,
                limit=config.max_retrieval_results,
                sparse_weight=config.sparse_weight,
                dense_weight=config.dense_weight,
                graph_weight=config.graph_weight
            )
        
        # Fallback to individual services
        all_results = []
        
        # Dense retrieval
        if self.dense_retrieval:
            try:
                dense_results = await self.dense_retrieval.search(
                    query, limit=config.max_retrieval_results // 3
                )
                all_results.extend(dense_results)
            except Exception as e:
                logger.warning(f"Dense retrieval failed: {e}")
        
        # Sparse retrieval  
        if self.sparse_retrieval:
            try:
                sparse_results = await self.sparse_retrieval.search(
                    query, limit=config.max_retrieval_results // 3
                )
                all_results.extend(sparse_results)
            except Exception as e:
                logger.warning(f"Sparse retrieval failed: {e}")
        
        # Graph traversal
        if self.graph_traversal:
            try:
                graph_results = await self.graph_traversal.traverse(
                    query, limit=config.max_retrieval_results // 3
                )
                # Convert graph results to SearchResult format
                # This would need to be implemented based on graph service interface
                pass
            except Exception as e:
                logger.warning(f"Graph traversal failed: {e}")
        
        # Remove duplicates and limit results
        unique_results = self._deduplicate_results(all_results)
        return unique_results[:config.max_retrieval_results]
    
    async def _execute_reranking_stage(
        self,
        query: str,
        results: List[SearchResult],
        config: RAGPipelineConfig
    ) -> List[SearchResult]:
        """Execute re-ranking stage."""
        logger.debug(f"Executing re-ranking stage for {len(results)} results")
        
        try:
            reranked_results = await self.reranking_service.rerank_results(
                query=query,
                results=results,
                max_results=config.max_reranked_results,
                domain_boost=config.philosophical_domain_boost
            )
            
            logger.debug(f"Re-ranked {len(results)} -> {len(reranked_results)} results")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            # Return original results if re-ranking fails
            return results[:config.max_reranked_results]
    
    async def _execute_diversification_stage(
        self,
        query: str,
        results: List[SearchResult], 
        config: RAGPipelineConfig
    ) -> List[SearchResult]:
        """Execute diversification stage."""
        logger.debug(f"Executing diversification stage for {len(results)} results")
        
        try:
            diversified_results = await self.diversity_service.diversify_results(
                query=query,
                results=results,
                max_results=config.max_diversified_results,
                similarity_threshold=0.7  # Could be added to config
            )
            
            logger.debug(f"Diversified {len(results)} -> {len(diversified_results)} results")
            return diversified_results
            
        except Exception as e:
            logger.error(f"Diversification failed: {e}")
            # Return original results if diversification fails
            return results[:config.max_diversified_results]
    
    async def _execute_context_composition_stage(
        self,
        query: str,
        results: List[SearchResult],
        config: RAGPipelineConfig
    ) -> ContextResult:
        """Execute context composition stage."""
        logger.debug(f"Executing context composition for {len(results)} results")
        
        if not self.context_composition:
            raise RAGPipelineError("Context composition service not available")
        
        try:
            from arete.services.context_composition_service import (
                ContextCompositionConfig, CompositionStrategy
            )
            
            composition_config = ContextCompositionConfig(
                max_tokens=config.max_context_tokens,
                strategy=CompositionStrategy(config.composition_strategy),
                enable_caching=config.enable_caching
            )
            
            context_result = self.context_composition.compose_context(
                search_results=results,
                query=query,
                config=composition_config
            )
            
            logger.debug(
                f"Composed context: {context_result.total_tokens} tokens, "
                f"{len(context_result.citations)} citations"
            )
            
            return context_result
            
        except Exception as e:
            logger.error(f"Context composition failed: {e}")
            raise RAGPipelineError(f"Context composition failed: {e}") from e
    
    async def _execute_response_generation_stage(
        self,
        query: str,
        context_result: ContextResult,
        config: RAGPipelineConfig
    ) -> ResponseResult:
        """Execute response generation stage."""
        logger.debug(f"Executing response generation for query: {query[:50]}...")
        
        if not self.response_generation:
            raise RAGPipelineError("Response generation service not available")
        
        try:
            from arete.services.response_generation_service import ResponseGenerationConfig
            
            generation_config = ResponseGenerationConfig(
                max_response_tokens=config.max_response_tokens,
                temperature=config.temperature,
                enable_validation=config.enable_validation,
                enable_caching=config.enable_caching
            )
            
            response_result = await self.response_generation.generate_response(
                context_result=context_result,
                query=query,
                config=generation_config
            )
            
            logger.debug(
                f"Generated response: {len(response_result.response_text)} chars, "
                f"{len(response_result.citations)} citations, "
                f"validation score: {response_result.validation.accuracy_score:.3f}"
            )
            
            return response_result
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise RAGPipelineError(f"Response generation failed: {e}") from e
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on chunk ID."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            chunk_id = result.chunk.id
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_average_relevance(self, results: List[SearchResult]) -> float:
        """Calculate average relevance score."""
        if not results:
            return 0.0
        
        total_score = sum(result.relevance_score for result in results)
        return total_score / len(results)
    
    def _create_empty_result(
        self,
        query: str,
        config: RAGPipelineConfig,
        metrics: PipelineMetrics,
        stage_completed: PipelineStage,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> RAGPipelineResult:
        """Create empty result for error cases."""
        from arete.services.response_generation_service import (
            ResponseResult, ResponseValidation
        )
        
        empty_response = ResponseResult(
            response_text="I apologize, but I couldn't find relevant information to answer your question.",
            query=query,
            citations=[],
            validation=ResponseValidation(
                is_valid=False,
                accuracy_score=0.0,
                citation_coverage=0.0,
                issues=errors or []
            )
        )
        
        return RAGPipelineResult(
            query=query,
            response=empty_response,
            config_used=config,
            metrics=metrics,
            stage_completed=stage_completed,
            errors=errors or [],
            warnings=warnings or []
        )
    
    def _generate_cache_key(
        self,
        query: str,
        config: RAGPipelineConfig,
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for pipeline request."""
        import hashlib
        
        key_components = [
            query,
            str(config.max_retrieval_results),
            str(config.max_response_tokens),
            str(config.temperature),
            config.composition_strategy,
            str(config.enable_reranking),
            str(config.enable_diversification)
        ]
        
        if user_context:
            key_components.append(str(sorted(user_context.items())))
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[RAGPipelineResult]:
        """Get cached pipeline result if valid."""
        if cache_key not in self._pipeline_cache:
            return None
        
        # Check cache TTL
        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > self.config.cache_ttl:
            # Remove expired cache entry
            del self._pipeline_cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._pipeline_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: RAGPipelineResult) -> None:
        """Cache pipeline result."""
        self._pipeline_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        # Limit cache size (simple LRU)
        if len(self._pipeline_cache) > 20:  # Max 20 cached results
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._pipeline_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    def clear_cache(self) -> None:
        """Clear pipeline cache."""
        self._pipeline_cache.clear()
        self._cache_timestamps.clear()
        logger.info("RAG pipeline cache cleared")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            'config': {
                'max_retrieval_results': self.config.max_retrieval_results,
                'max_response_tokens': self.config.max_response_tokens,
                'enable_reranking': self.config.enable_reranking,
                'enable_diversification': self.config.enable_diversification,
                'composition_strategy': self.config.composition_strategy
            },
            'cache_stats': {
                'cached_results': len(self._pipeline_cache),
                'cache_hit_potential': len(self._pipeline_cache) > 0,
                'oldest_entry_age': (
                    time.time() - min(self._cache_timestamps.values())
                    if self._cache_timestamps else 0
                )
            },
            'services_available': {
                'dense_retrieval': self.dense_retrieval is not None,
                'sparse_retrieval': self.sparse_retrieval is not None,
                'graph_traversal': self.graph_traversal is not None,
                'reranking': self.reranking_service is not None,
                'diversity': self.diversity_service is not None,
                'context_composition': self.context_composition is not None,
                'response_generation': self.response_generation is not None,
                'retrieval_repository': self.retrieval_repository is not None
            }
        }


# Factory function following established pattern
def create_rag_pipeline_service(
    config: Optional[RAGPipelineConfig] = None,
    settings: Optional[Settings] = None,
    **service_kwargs
) -> RAGPipelineService:
    """
    Create RAG pipeline service with optional configuration and services.
    
    Args:
        config: Optional pipeline configuration
        settings: Optional application settings
        **service_kwargs: Service instances to inject
        
    Returns:
        Configured RAGPipelineService instance
    """
    return RAGPipelineService(
        config=config,
        settings=settings,
        **service_kwargs
    )