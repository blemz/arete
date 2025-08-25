"""
Context Composition Service for Arete Graph-RAG system.

Provides intelligent context composition for LLM consumption with:
- Token limit management (5000 token default)
- Intelligent passage stitching
- Citation tracking and formatting
- Map-Reduce for long philosophical contexts
- Performance optimization with caching
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID

from ..config import Settings, get_settings
from ..services.dense_retrieval_service import SearchResult
from ..models.chunk import Chunk
from ..models.citation import Citation
from .base import ServiceError

logger = logging.getLogger(__name__)


class CompositionStrategy(str, Enum):
    """Available context composition strategies."""
    INTELLIGENT_STITCHING = "intelligent_stitching"
    MAP_REDUCE = "map_reduce"
    SIMPLE_CONCAT = "simple_concat"
    SEMANTIC_GROUPING = "semantic_grouping"


class CitationFormat(str, Enum):
    """Available citation formatting styles."""
    CLASSICAL = "classical"  # "Republic 514a"
    MODERN = "modern"       # "(Plato, Republic, 514a)"
    FOOTNOTE = "footnote"   # "[1] Plato, Republic 514a"


class ContextCompositionError(ServiceError):
    """Base exception for context composition service errors."""
    pass


@dataclass
class ContextCompositionConfig:
    """Configuration for context composition operations."""
    
    # Token management
    max_tokens: int = 5000
    tokens_per_word: float = 1.3  # Rough estimation
    
    # Composition strategy
    strategy: CompositionStrategy = CompositionStrategy.INTELLIGENT_STITCHING
    
    # Content processing
    overlap_threshold: float = 0.3  # Similarity threshold for overlap detection
    coherence_threshold: float = 0.6  # Minimum coherence for passage grouping
    
    # Citation handling
    citation_format: CitationFormat = CitationFormat.CLASSICAL
    include_citations: bool = True
    max_citations: int = 50
    
    # Metadata and context
    include_metadata: bool = True
    preserve_context: bool = True
    add_source_info: bool = True
    
    # Performance
    enable_caching: bool = True
    cache_ttl: int = 3600  # Cache time-to-live in seconds
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not (0.0 <= self.overlap_threshold <= 1.0):
            raise ValueError("overlap_threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.coherence_threshold <= 1.0):
            raise ValueError("coherence_threshold must be between 0.0 and 1.0")


@dataclass
class PassageGroup:
    """A group of coherent text passages."""
    
    chunks: List[Chunk]
    coherence_score: float
    topic: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    token_count: int = field(default=0, init=False)
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.token_count = self._calculate_token_count()
    
    def _calculate_token_count(self) -> int:
        """Calculate approximate token count for all chunks."""
        total_text = " ".join(chunk.text for chunk in self.chunks)
        # Rough estimation: 1.3 tokens per word
        return int(len(total_text.split()) * 1.3)
    
    def get_composed_text(self, separator: str = " ") -> str:
        """Get composed text from all chunks."""
        return separator.join(chunk.text for chunk in self.chunks)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get combined metadata from all chunks."""
        metadata = {}
        for chunk in self.chunks:
            metadata.update(chunk.metadata)
        return metadata


@dataclass
class CitationContext:
    """Context information for a citation."""
    
    citation: Citation
    formatted_citation: str
    context_relevance: float
    position_in_text: Optional[int] = None
    anchor_text: Optional[str] = None


@dataclass
class ContextResult:
    """Result of context composition operation."""
    
    # Core content
    composed_text: str
    total_tokens: int
    query: str
    
    # Structure
    passage_groups: List[PassageGroup]
    citations: List[CitationContext]
    
    # Metadata
    strategy_used: CompositionStrategy
    truncated: bool = False
    overlaps_detected: int = 0
    composition_time: float = 0.0
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompositionService:
    """
    Context Composition Service for preparing search results for LLM consumption.
    
    Provides intelligent context composition with token limit management,
    passage stitching, citation integration, and performance optimization.
    """
    
    def __init__(
        self,
        config: Optional[ContextCompositionConfig] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize context composition service.
        
        Args:
            config: Context composition configuration
            settings: Application settings
        """
        self.config = config or ContextCompositionConfig()
        self.settings = settings or get_settings()
        
        # Caching for performance
        self._composition_cache: Dict[str, ContextResult] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        logger.info(
            f"Initialized ContextCompositionService with strategy: {self.config.strategy.value}, "
            f"max_tokens: {self.config.max_tokens}"
        )
    
    def compose_context(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]] = None,
        config: Optional[ContextCompositionConfig] = None
    ) -> ContextResult:
        """
        Compose context from search results for LLM consumption.
        
        Args:
            search_results: List of search results to compose
            query: Original search query
            citations: Optional list of citations to integrate
            config: Optional configuration override
            
        Returns:
            ContextResult with composed context and metadata
            
        Raises:
            ContextCompositionError: If composition fails
        """
        start_time = time.time()
        composition_config = config or self.config
        
        try:
            # Input validation
            self._validate_inputs(search_results, query, composition_config)
            
            # Check cache if enabled
            if composition_config.enable_caching:
                cache_key = self._generate_cache_key(search_results, query, citations, composition_config)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.debug(f"Returning cached composition for query: {query[:50]}...")
                    return cached_result
            
            # Handle empty results
            if not search_results:
                return self._create_empty_result(query, composition_config.strategy)
            
            # Apply composition strategy
            if composition_config.strategy == CompositionStrategy.INTELLIGENT_STITCHING:
                result = self._intelligent_stitching_composition(
                    search_results, query, citations, composition_config
                )
            elif composition_config.strategy == CompositionStrategy.MAP_REDUCE:
                result = self._map_reduce_composition(
                    search_results, query, citations, composition_config
                )
            elif composition_config.strategy == CompositionStrategy.SEMANTIC_GROUPING:
                result = self._semantic_grouping_composition(
                    search_results, query, citations, composition_config
                )
            else:  # SIMPLE_CONCAT
                result = self._simple_concat_composition(
                    search_results, query, citations, composition_config
                )
            
            # Calculate performance metrics
            result.composition_time = time.time() - start_time
            result.performance_metrics = self._calculate_performance_metrics(result)
            
            # Cache result if enabled
            if composition_config.enable_caching and cache_key:
                self._cache_result(cache_key, result)
            
            logger.debug(
                f"Context composition completed: {result.total_tokens} tokens, "
                f"{len(result.passage_groups)} groups, {result.composition_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Context composition failed: {e}")
            raise ContextCompositionError(f"Composition failed: {e}") from e
    
    def compose_context_batch(
        self,
        search_results_list: List[List[SearchResult]],
        queries: List[str],
        config: Optional[ContextCompositionConfig] = None
    ) -> List[ContextResult]:
        """
        Compose context for multiple queries in batch.
        
        Args:
            search_results_list: List of search results for each query
            queries: List of search queries
            config: Optional configuration override
            
        Returns:
            List of ContextResult objects
        """
        if len(search_results_list) != len(queries):
            raise ContextCompositionError(
                "search_results_list and queries must have the same length"
            )
        
        results = []
        for search_results, query in zip(search_results_list, queries):
            try:
                result = self.compose_context(
                    search_results=search_results,
                    query=query,
                    config=config
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Batch composition failed for query '{query}': {e}")
                # Add empty result for failed queries
                results.append(self._create_empty_result(query, config.strategy if config else self.config.strategy))
        
        return results
    
    def count_tokens(self, text: str) -> int:
        """
        Count approximate tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate number of tokens
        """
        if not text or not text.strip():
            return 0
        
        # Simple approximation: tokens ≈ words * 1.3
        word_count = len(text.split())
        return int(word_count * self.config.tokens_per_word)
    
    def _validate_inputs(
        self,
        search_results: List[SearchResult],
        query: str,
        config: ContextCompositionConfig
    ) -> None:
        """Validate input parameters."""
        if not isinstance(query, str):
            raise ContextCompositionError("query must be a string")
        
        if not isinstance(search_results, list):
            raise ContextCompositionError("search_results must be a list")
        
        for result in search_results:
            if not hasattr(result, 'chunk') or not hasattr(result, 'relevance_score'):
                raise ContextCompositionError("Invalid search result format")
        
        if config.max_tokens <= 0:
            raise ContextCompositionError("max_tokens must be positive")
    
    def _intelligent_stitching_composition(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]],
        config: ContextCompositionConfig
    ) -> ContextResult:
        """Compose context using intelligent stitching strategy."""
        logger.debug(f"Applying intelligent stitching for {len(search_results)} results")
        
        # Group results by document and position for coherent stitching
        document_groups = self._group_by_document(search_results)
        
        passage_groups = []
        total_tokens = 0
        overlaps_detected = 0
        
        for doc_id, doc_results in document_groups.items():
            # Sort by position for coherent ordering
            doc_results.sort(key=lambda r: r.chunk.position)
            
            # Detect overlapping chunks
            non_overlapping_results = self._remove_overlaps(doc_results, config.overlap_threshold)
            overlaps_detected += len(doc_results) - len(non_overlapping_results)
            
            # Create coherent passage groups
            coherent_groups = self._create_coherent_groups(non_overlapping_results, config.coherence_threshold)
            
            for group in coherent_groups:
                group_tokens = group.token_count
                
                # Check token limit
                if total_tokens + group_tokens > config.max_tokens:
                    # Try to fit partial content
                    remaining_tokens = config.max_tokens - total_tokens
                    truncated_group = self._truncate_group(group, remaining_tokens)
                    if truncated_group.token_count > 0:
                        passage_groups.append(truncated_group)
                        total_tokens += truncated_group.token_count
                    break
                
                passage_groups.append(group)
                total_tokens += group_tokens
        
        # Compose final text
        composed_text = self._compose_text_from_groups(passage_groups, config)
        
        # Process citations
        citation_contexts = self._process_citations(citations, composed_text, config) if citations else []
        
        # Check if content was truncated due to token limits
        was_truncated = (
            total_tokens >= config.max_tokens or 
            any(self.count_tokens(result.chunk.text) > config.max_tokens for result in search_results if passage_groups == [])
        )
        
        return ContextResult(
            composed_text=composed_text,
            total_tokens=total_tokens,
            query=query,
            passage_groups=passage_groups,
            citations=citation_contexts,
            strategy_used=CompositionStrategy.INTELLIGENT_STITCHING,
            truncated=was_truncated,
            overlaps_detected=overlaps_detected,
            metadata=self._create_metadata(search_results, config)
        )
    
    def _map_reduce_composition(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]],
        config: ContextCompositionConfig
    ) -> ContextResult:
        """Compose context using Map-Reduce strategy for large contexts."""
        logger.debug(f"Applying Map-Reduce strategy for {len(search_results)} results")
        
        # Map phase: Group results into manageable chunks
        chunk_size = max(5, config.max_tokens // 1000)  # Adaptive chunk size
        result_chunks = [
            search_results[i:i + chunk_size]
            for i in range(0, len(search_results), chunk_size)
        ]
        
        # Reduce phase: Compose each chunk and then combine
        passage_groups = []
        total_tokens = 0
        overlaps_detected = 0
        
        for chunk_results in result_chunks:
            # Process chunk with intelligent stitching
            chunk_config = ContextCompositionConfig(
                max_tokens=config.max_tokens // len(result_chunks),
                strategy=CompositionStrategy.INTELLIGENT_STITCHING,
                overlap_threshold=config.overlap_threshold,
                coherence_threshold=config.coherence_threshold
            )
            
            chunk_composition = self._intelligent_stitching_composition(
                chunk_results, query, None, chunk_config
            )
            
            # Add chunk groups to final result
            for group in chunk_composition.passage_groups:
                if total_tokens + group.token_count > config.max_tokens:
                    break
                passage_groups.append(group)
                total_tokens += group.token_count
            
            overlaps_detected += chunk_composition.overlaps_detected
            
            if total_tokens >= config.max_tokens:
                break
        
        # Compose final text
        composed_text = self._compose_text_from_groups(passage_groups, config)
        
        # Process citations
        citation_contexts = self._process_citations(citations, composed_text, config) if citations else []
        
        # Check if content was truncated due to token limits
        was_truncated = (
            total_tokens >= config.max_tokens or 
            any(self.count_tokens(result.chunk.text) > config.max_tokens for result in search_results if passage_groups == [])
        )
        
        return ContextResult(
            composed_text=composed_text,
            total_tokens=total_tokens,
            query=query,
            passage_groups=passage_groups,
            citations=citation_contexts,
            strategy_used=CompositionStrategy.MAP_REDUCE,
            truncated=was_truncated,
            overlaps_detected=overlaps_detected,
            metadata=self._create_metadata(search_results, config)
        )
    
    def _semantic_grouping_composition(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]],
        config: ContextCompositionConfig
    ) -> ContextResult:
        """Compose context using semantic grouping strategy."""
        logger.debug(f"Applying semantic grouping for {len(search_results)} results")
        
        # Group results by semantic similarity
        semantic_groups = self._group_by_semantic_similarity(search_results, config.coherence_threshold)
        
        passage_groups = []
        total_tokens = 0
        
        # Sort groups by average relevance score
        semantic_groups.sort(
            key=lambda group: sum(r.relevance_score for r in group) / len(group),
            reverse=True
        )
        
        for group_results in semantic_groups:
            # Create passage group
            chunks = [result.chunk for result in group_results]
            avg_score = sum(r.relevance_score for r in group_results) / len(group_results)
            
            group = PassageGroup(
                chunks=chunks,
                coherence_score=avg_score,
                topic=self._extract_topic(group_results)
            )
            
            # Check token limit
            if total_tokens + group.token_count > config.max_tokens:
                # Try to fit truncated content
                remaining_tokens = config.max_tokens - total_tokens
                truncated_group = self._truncate_group(group, remaining_tokens)
                if truncated_group.token_count > 0:
                    passage_groups.append(truncated_group)
                    total_tokens += truncated_group.token_count
                break
            
            passage_groups.append(group)
            total_tokens += group.token_count
        
        # Compose final text
        composed_text = self._compose_text_from_groups(passage_groups, config)
        
        # Process citations
        citation_contexts = self._process_citations(citations, composed_text, config) if citations else []
        
        return ContextResult(
            composed_text=composed_text,
            total_tokens=total_tokens,
            query=query,
            passage_groups=passage_groups,
            citations=citation_contexts,
            strategy_used=CompositionStrategy.SEMANTIC_GROUPING,
            truncated=total_tokens >= config.max_tokens,
            metadata=self._create_metadata(search_results, config)
        )
    
    def _simple_concat_composition(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]],
        config: ContextCompositionConfig
    ) -> ContextResult:
        """Compose context using simple concatenation strategy."""
        logger.debug(f"Applying simple concatenation for {len(search_results)} results")
        
        # Sort by relevance score
        sorted_results = sorted(search_results, key=lambda r: r.relevance_score, reverse=True)
        
        passage_groups = []
        total_tokens = 0
        
        for result in sorted_results:
            chunk = result.chunk
            chunk_tokens = self.count_tokens(chunk.text)
            
            # Check token limit
            if total_tokens + chunk_tokens > config.max_tokens:
                # Try to fit truncated content
                remaining_tokens = config.max_tokens - total_tokens
                if remaining_tokens > 50:  # Minimum meaningful content
                    truncated_text = self._truncate_text(chunk.text, remaining_tokens)
                    truncated_chunk = Chunk(
                        text=truncated_text,
                        document_id=chunk.document_id,
                        position=chunk.position,
                        start_char=chunk.start_char,
                        end_char=chunk.start_char + len(truncated_text),
                        chunk_type=chunk.chunk_type
                    )
                    
                    group = PassageGroup(
                        chunks=[truncated_chunk],
                        coherence_score=result.relevance_score
                    )
                    passage_groups.append(group)
                    total_tokens += remaining_tokens
                break
            
            group = PassageGroup(
                chunks=[chunk],
                coherence_score=result.relevance_score
            )
            passage_groups.append(group)
            total_tokens += chunk_tokens
        
        # Compose final text
        composed_text = self._compose_text_from_groups(passage_groups, config)
        
        # Process citations
        citation_contexts = self._process_citations(citations, composed_text, config) if citations else []
        
        return ContextResult(
            composed_text=composed_text,
            total_tokens=total_tokens,
            query=query,
            passage_groups=passage_groups,
            citations=citation_contexts,
            strategy_used=CompositionStrategy.SIMPLE_CONCAT,
            truncated=total_tokens >= config.max_tokens,
            metadata=self._create_metadata(search_results, config)
        )
    
    def _group_by_document(self, search_results: List[SearchResult]) -> Dict[UUID, List[SearchResult]]:
        """Group search results by document ID."""
        groups = {}
        for result in search_results:
            doc_id = result.chunk.document_id
            if doc_id not in groups:
                groups[doc_id] = []
            groups[doc_id].append(result)
        return groups
    
    def _remove_overlaps(self, results: List[SearchResult], threshold: float) -> List[SearchResult]:
        """Remove overlapping chunks based on similarity threshold."""
        if not results:
            return results
        
        non_overlapping = [results[0]]  # Start with first result
        
        for result in results[1:]:
            is_overlapping = False
            
            for existing in non_overlapping:
                similarity = self._calculate_text_similarity(
                    result.chunk.text, 
                    existing.chunk.text
                )
                
                if similarity > threshold:
                    is_overlapping = True
                    # Keep the one with higher relevance score
                    if result.relevance_score > existing.relevance_score:
                        non_overlapping.remove(existing)
                        non_overlapping.append(result)
                    break
            
            if not is_overlapping:
                non_overlapping.append(result)
        
        return non_overlapping
    
    def _create_coherent_groups(self, results: List[SearchResult], threshold: float) -> List[PassageGroup]:
        """Create coherent passage groups from search results."""
        if not results:
            return []
        
        groups = []
        current_group = [results[0]]
        
        for result in results[1:]:
            # Check if this result is coherent with current group
            avg_coherence = sum(
                self._calculate_coherence(result.chunk, chunk.chunk)
                for chunk in current_group
            ) / len(current_group)
            
            if avg_coherence >= threshold:
                current_group.append(result)
            else:
                # Finalize current group and start new one
                if current_group:
                    group = PassageGroup(
                        chunks=[r.chunk for r in current_group],
                        coherence_score=self._calculate_group_coherence(current_group),
                        topic=self._extract_topic(current_group)
                    )
                    groups.append(group)
                
                current_group = [result]
        
        # Add final group
        if current_group:
            group = PassageGroup(
                chunks=[r.chunk for r in current_group],
                coherence_score=self._calculate_group_coherence(current_group),
                topic=self._extract_topic(current_group)
            )
            groups.append(group)
        
        return groups
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simplified implementation)."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_coherence(self, chunk1: Chunk, chunk2: Chunk) -> float:
        """Calculate coherence between two chunks."""
        # Simple implementation based on position proximity and text similarity
        position_coherence = 1.0 / (1.0 + abs(chunk1.position - chunk2.position))
        text_coherence = self._calculate_text_similarity(chunk1.text, chunk2.text)
        
        return (position_coherence + text_coherence) / 2.0
    
    def _calculate_group_coherence(self, results: List[SearchResult]) -> float:
        """Calculate overall coherence score for a group of results."""
        if len(results) <= 1:
            return 1.0
        
        coherence_scores = []
        for i, result1 in enumerate(results):
            for result2 in results[i+1:]:
                score = self._calculate_coherence(result1.chunk, result2.chunk)
                coherence_scores.append(score)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    
    def _group_by_semantic_similarity(self, results: List[SearchResult], threshold: float) -> List[List[SearchResult]]:
        """Group results by semantic similarity (simplified clustering)."""
        if not results:
            return []
        
        groups = []
        remaining_results = results.copy()
        
        while remaining_results:
            # Start new group with first remaining result
            seed = remaining_results.pop(0)
            group = [seed]
            
            # Find similar results
            to_remove = []
            for i, result in enumerate(remaining_results):
                similarity = self._calculate_text_similarity(seed.chunk.text, result.chunk.text)
                if similarity >= threshold:
                    group.append(result)
                    to_remove.append(i)
            
            # Remove added results
            for i in reversed(to_remove):
                remaining_results.pop(i)
            
            groups.append(group)
        
        return groups
    
    def _extract_topic(self, results: List[SearchResult]) -> Optional[str]:
        """Extract topic from a group of search results."""
        # Simple implementation - could be enhanced with NLP
        common_words = set()
        
        for result in results:
            words = set(word.lower() for word in result.chunk.text.split() if len(word) > 3)
            if not common_words:
                common_words = words
            else:
                common_words = common_words.intersection(words)
        
        if common_words:
            return " ".join(sorted(list(common_words))[:3])
        
        return None
    
    def _truncate_group(self, group: PassageGroup, max_tokens: int) -> PassageGroup:
        """Truncate a passage group to fit within token limit."""
        if group.token_count <= max_tokens:
            return group
        
        # Truncate chunks until we fit within limit
        truncated_chunks = []
        current_tokens = 0
        
        for chunk in group.chunks:
            chunk_tokens = self.count_tokens(chunk.text)
            
            if current_tokens + chunk_tokens <= max_tokens:
                truncated_chunks.append(chunk)
                current_tokens += chunk_tokens
            else:
                # Try to fit partial chunk
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 50:  # Minimum meaningful content
                    truncated_text = self._truncate_text(chunk.text, remaining_tokens)
                    truncated_chunk = Chunk(
                        text=truncated_text,
                        document_id=chunk.document_id,
                        position=chunk.position,
                        start_char=chunk.start_char,
                        end_char=chunk.start_char + len(truncated_text),
                        chunk_type=chunk.chunk_type
                    )
                    truncated_chunks.append(truncated_chunk)
                    current_tokens += remaining_tokens
                break
        
        return PassageGroup(
            chunks=truncated_chunks,
            coherence_score=group.coherence_score,
            topic=group.topic
        )
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        words = text.split()
        max_words = int(max_tokens / self.config.tokens_per_word)
        
        if len(words) <= max_words:
            return text
        
        return " ".join(words[:max_words]) + "..."
    
    def _compose_text_from_groups(self, groups: List[PassageGroup], config: ContextCompositionConfig) -> str:
        """Compose final text from passage groups."""
        if not groups:
            return ""
        
        sections = []
        
        for i, group in enumerate(groups):
            group_text = group.get_composed_text()
            
            if config.add_source_info and group.topic:
                sections.append(f"## {group.topic}\n{group_text}")
            else:
                sections.append(group_text)
        
        return "\n\n".join(sections)
    
    def _process_citations(
        self, 
        citations: List[Citation], 
        composed_text: str, 
        config: ContextCompositionConfig
    ) -> List[CitationContext]:
        """Process and format citations for the composed context."""
        if not citations or not config.include_citations:
            return []
        
        citation_contexts = []
        
        for citation in citations[:config.max_citations]:
            # Format citation based on configuration
            formatted = self._format_citation(citation, config.citation_format)
            
            # Calculate relevance to composed text
            relevance = self._calculate_citation_relevance(citation, composed_text)
            
            # Find position in text if possible
            position = self._find_citation_position(citation, composed_text)
            
            context = CitationContext(
                citation=citation,
                formatted_citation=formatted,
                context_relevance=relevance,
                position_in_text=position
            )
            
            citation_contexts.append(context)
        
        # Sort by relevance
        citation_contexts.sort(key=lambda c: c.context_relevance, reverse=True)
        
        return citation_contexts
    
    def _format_citation(self, citation: Citation, format_type: CitationFormat) -> str:
        """Format citation according to specified format."""
        if format_type == CitationFormat.CLASSICAL:
            return citation.source_reference or f"Citation {citation.id}"
        elif format_type == CitationFormat.MODERN:
            # Extract author from metadata or source reference
            ref = citation.source_reference or ""
            if " " in ref:
                parts = ref.split()
                work = parts[0]
                section = " ".join(parts[1:])
                return f"({work}, {section})"
            return f"({ref})"
        elif format_type == CitationFormat.FOOTNOTE:
            return f"[{citation.source_reference or citation.id}]"
        
        return str(citation.source_reference or citation.id)
    
    def _calculate_citation_relevance(self, citation: Citation, text: str) -> float:
        """Calculate relevance of citation to composed text."""
        # Simple implementation based on text overlap
        citation_text = citation.text.lower()
        composed_text = text.lower()
        
        # Count overlapping words
        citation_words = set(citation_text.split())
        text_words = set(composed_text.split())
        
        if not citation_words:
            return 0.0
        
        overlap = citation_words.intersection(text_words)
        return len(overlap) / len(citation_words)
    
    def _find_citation_position(self, citation: Citation, text: str) -> Optional[int]:
        """Find position of citation in composed text."""
        # Look for citation text in composed text
        citation_text = citation.text
        position = text.find(citation_text)
        
        if position != -1:
            return position
        
        # Try first few words
        words = citation_text.split()[:5]
        partial_text = " ".join(words)
        position = text.find(partial_text)
        
        return position if position != -1 else None
    
    def _create_metadata(self, search_results: List[SearchResult], config: ContextCompositionConfig) -> Dict[str, Any]:
        """Create metadata for the composed context."""
        if not config.include_metadata:
            return {}
        
        retrieval_methods = set()
        documents = set()
        avg_relevance = 0.0
        
        for result in search_results:
            retrieval_methods.add(result.metadata.get('retrieval_method', 'unknown'))
            documents.add(str(result.chunk.document_id))
            avg_relevance += result.relevance_score
        
        avg_relevance = avg_relevance / len(search_results) if search_results else 0.0
        
        return {
            'retrieval_methods': list(retrieval_methods),
            'document_count': len(documents),
            'result_count': len(search_results),
            'average_relevance': avg_relevance,
            'composition_stats': {
                'strategy': config.strategy.value,
                'overlap_threshold': config.overlap_threshold,
                'coherence_threshold': config.coherence_threshold
            }
        }
    
    def _calculate_performance_metrics(self, result: ContextResult) -> Dict[str, Any]:
        """Calculate performance metrics for the composition."""
        token_efficiency = result.total_tokens / self.config.max_tokens if self.config.max_tokens > 0 else 0.0
        
        return {
            'token_efficiency': token_efficiency,
            'groups_per_token': len(result.passage_groups) / max(result.total_tokens, 1),
            'citations_per_group': len(result.citations) / max(len(result.passage_groups), 1),
            'composition_speed': result.total_tokens / max(result.composition_time, 0.001)  # tokens per second
        }
    
    def _create_empty_result(self, query: str, strategy: CompositionStrategy) -> ContextResult:
        """Create empty result for edge cases."""
        return ContextResult(
            composed_text="",
            total_tokens=0,
            query=query,
            passage_groups=[],
            citations=[],
            strategy_used=strategy,
            truncated=False,
            overlaps_detected=0
        )
    
    def _generate_cache_key(
        self,
        search_results: List[SearchResult],
        query: str,
        citations: Optional[List[Citation]],
        config: ContextCompositionConfig
    ) -> str:
        """Generate cache key for composition request."""
        # Create deterministic hash of inputs
        key_components = [
            query,
            str(config.max_tokens),
            config.strategy.value,
            str(config.overlap_threshold),
            str(len(search_results))
        ]
        
        # Add result identifiers
        for result in search_results:
            key_components.append(str(result.chunk.id))
            key_components.append(str(result.relevance_score))
        
        # Add citation identifiers if present
        if citations:
            for citation in citations:
                key_components.append(str(citation.id))
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ContextResult]:
        """Get cached composition result if valid."""
        if cache_key not in self._composition_cache:
            return None
        
        # Check cache TTL
        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > self.config.cache_ttl:
            # Remove expired cache entry
            del self._composition_cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._composition_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: ContextResult) -> None:
        """Cache composition result."""
        self._composition_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        # Limit cache size (simple LRU)
        if len(self._composition_cache) > 100:  # Max 100 cached results
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._composition_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    def clear_cache(self) -> None:
        """Clear composition cache."""
        self._composition_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Context composition cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cached_results': len(self._composition_cache),
            'cache_hit_potential': len(self._composition_cache) > 0,
            'oldest_entry_age': time.time() - min(self._cache_timestamps.values()) if self._cache_timestamps else 0
        }


# Factory function following established pattern
def create_context_composition_service(
    config: Optional[ContextCompositionConfig] = None,
    settings: Optional[Settings] = None
) -> ContextCompositionService:
    """
    Create context composition service with optional configuration.
    
    Args:
        config: Optional context composition configuration
        settings: Optional application settings
        
    Returns:
        Configured ContextCompositionService instance
    """
    return ContextCompositionService(config=config, settings=settings)