"""
Sparse Retrieval Service for Arete Graph-RAG system.

Provides sparse retrieval capabilities including BM25 and SPLADE models
for keyword-based and learned sparse retrieval. Complements the dense
retrieval system with lexical matching capabilities for comprehensive
philosophical text search.
"""

import logging
import time
import math
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Set, Union, Counter
from uuid import UUID
from collections import defaultdict, Counter as CollectionsCounter
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from ..models.chunk import Chunk
from ..config import Settings, get_settings
from ..database.client import Neo4jClient
from .dense_retrieval_service import SearchResult, RetrievalMetrics

logger = logging.getLogger(__name__)


class SparseRetrievalError(Exception):
    """Base exception for sparse retrieval errors."""
    pass


class IndexingError(SparseRetrievalError):
    """Raised when document indexing fails."""
    pass


class QueryProcessingError(SparseRetrievalError):
    """Raised when query processing fails."""
    pass


@dataclass
class TermFrequencyDocument:
    """
    Represents a document with term frequency information for sparse retrieval.
    
    Stores the necessary statistics for BM25 scoring including term frequencies,
    document length, and metadata for efficient retrieval operations.
    """
    document_id: str
    chunk_id: str
    term_frequencies: Dict[str, int]
    total_terms: int
    unique_terms: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_term_frequency(self, term: str) -> int:
        """Get frequency of a specific term in this document."""
        return self.term_frequencies.get(term, 0)
    
    def get_normalized_length(self, average_doc_length: float) -> float:
        """Get normalized document length for BM25 calculation."""
        if average_doc_length == 0:
            return 1.0
        return self.total_terms / average_doc_length


@dataclass
class SparseIndex:
    """
    Inverted index structure for sparse retrieval operations.
    
    Maintains term-to-document mappings and document statistics
    required for efficient BM25 and other sparse retrieval algorithms.
    """
    term_document_frequencies: Dict[str, Dict[str, int]] = field(default_factory=dict)
    document_frequencies: Dict[str, int] = field(default_factory=dict)
    documents: Dict[str, TermFrequencyDocument] = field(default_factory=dict)
    total_documents: int = 0
    average_document_length: float = 0.0
    vocabulary: Set[str] = field(default_factory=set)
    
    def add_document(self, doc: TermFrequencyDocument) -> None:
        """Add a document to the index."""
        self.documents[doc.chunk_id] = doc
        
        # Update term-document frequencies
        for term, freq in doc.term_frequencies.items():
            if term not in self.term_document_frequencies:
                self.term_document_frequencies[term] = {}
            self.term_document_frequencies[term][doc.chunk_id] = freq
            
            # Update document frequency for term
            if term not in self.document_frequencies:
                self.document_frequencies[term] = 0
            self.document_frequencies[term] += 1
            
            # Update vocabulary
            self.vocabulary.add(term)
        
        # Update statistics
        self.total_documents += 1
        self._update_average_document_length()
    
    def get_document_frequency(self, term: str) -> int:
        """Get number of documents containing the term."""
        return self.document_frequencies.get(term, 0)
    
    def get_term_documents(self, term: str) -> Dict[str, int]:
        """Get all documents containing the term with their frequencies."""
        return self.term_document_frequencies.get(term, {})
    
    def _update_average_document_length(self) -> None:
        """Update average document length statistics."""
        if self.total_documents == 0:
            self.average_document_length = 0.0
            return
        
        total_length = sum(doc.total_terms for doc in self.documents.values())
        self.average_document_length = total_length / self.total_documents


class BaseSparseRetriever(ABC):
    """
    Abstract base class for sparse retrieval implementations.
    
    Defines the interface and common functionality for different sparse
    retrieval algorithms including BM25, TF-IDF, and SPLADE variants.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize base sparse retriever.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings or get_settings()
        self.index: Optional[SparseIndex] = None
        self.metrics = RetrievalMetrics()
        self._is_indexed = False
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def score_document(
        self, 
        query_terms: List[str], 
        document: TermFrequencyDocument
    ) -> float:
        """
        Calculate relevance score for a document given query terms.
        
        Args:
            query_terms: List of query terms
            document: Document to score
            
        Returns:
            Relevance score (0.0-1.0)
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Get the name of the retrieval algorithm."""
        pass
    
    def build_index(self, chunks: List[Chunk]) -> None:
        """
        Build sparse index from chunks.
        
        Args:
            chunks: List of chunks to index
        """
        start_time = time.time()
        
        try:
            logger.info(f"Building {self.get_algorithm_name()} index from {len(chunks)} chunks")
            
            self.index = SparseIndex()
            
            for chunk in chunks:
                # Tokenize and count terms
                terms = self._tokenize_text(chunk.text)
                term_frequencies = CollectionsCounter(terms)
                
                # Create document representation
                doc = TermFrequencyDocument(
                    document_id=str(chunk.document_id),
                    chunk_id=str(chunk.id),
                    term_frequencies=dict(term_frequencies),
                    total_terms=len(terms),
                    unique_terms=len(term_frequencies),
                    metadata={
                        'chunk_type': chunk.chunk_type,
                        'sequence_number': chunk.position,  # Use position instead of sequence_number
                        'word_count': chunk.word_count
                    }
                )
                
                # Add to index
                self.index.add_document(doc)
            
            self._is_indexed = True
            build_time = time.time() - start_time
            
            logger.info(
                f"{self.get_algorithm_name()} index built: "
                f"{len(self.index.documents)} documents, "
                f"{len(self.index.vocabulary)} unique terms, "
                f"avg length {self.index.average_document_length:.1f} terms "
                f"in {build_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Index building failed: {e}")
            raise IndexingError(f"Failed to build {self.get_algorithm_name()} index: {e}") from e
    
    def search(
        self,
        query: str,
        limit: int = 10,
        min_relevance: float = 0.0,
        chunk_types: Optional[List[str]] = None,
        document_ids: Optional[List[UUID]] = None
    ) -> List[SearchResult]:
        """
        Perform sparse retrieval search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_relevance: Minimum relevance threshold
            chunk_types: Optional filter by chunk types
            document_ids: Optional filter by document IDs
            
        Returns:
            List of SearchResult objects
        """
        if not self._is_indexed or self.index is None:
            raise SparseRetrievalError(f"{self.get_algorithm_name()} index not built")
        
        start_time = time.time()
        
        try:
            # Process query
            query_terms = self._tokenize_text(query)
            if not query_terms:
                logger.warning(f"Empty query after tokenization: '{query}'")
                return []
            
            # Score all documents
            scored_results = []
            
            for chunk_id, document in self.index.documents.items():
                # Apply filters
                if chunk_types and document.metadata.get('chunk_type') not in chunk_types:
                    continue
                
                if document_ids:
                    doc_uuid = UUID(document.document_id)
                    if doc_uuid not in document_ids:
                        continue
                
                # Calculate relevance score
                score = self.score_document(query_terms, document)
                
                if score >= min_relevance:
                    # Create SearchResult (we'll need to fetch the actual Chunk)
                    # For now, create a placeholder - this would need integration with repository
                    scored_results.append((chunk_id, score))
            
            # Sort by score and apply limit
            scored_results.sort(key=lambda x: x[1], reverse=True)
            scored_results = scored_results[:limit]
            
            # Convert to SearchResult objects
            # Note: This is a simplified implementation
            # In production, would need to fetch actual Chunk objects from repository
            search_results = []
            for i, (chunk_id, score) in enumerate(scored_results, 1):
                # Get document from index 
                document = self.index.documents[chunk_id]
                
                # Create minimal chunk object from stored metadata
                # In production, this would fetch from a proper repository
                chunk = Chunk(
                    id=UUID(chunk_id),
                    document_id=UUID(document.document_id),
                    text="[Placeholder - would fetch from repository]",
                    position=document.metadata.get('sequence_number', 0),
                    chunk_type=document.metadata.get('chunk_type', 'paragraph'),
                    start_char=0,
                    end_char=100,
                    word_count=document.metadata.get('word_count', 0)
                )
                
                result = SearchResult(
                    chunk=chunk,
                    relevance_score=score,
                    query=query,
                    ranking_position=i,
                    metadata={
                        'algorithm': self.get_algorithm_name(),
                        'chunk_id': chunk_id,
                        'sparse_score': score
                    }
                )
                
                search_results.append(result)
            
            # Update metrics
            response_time = time.time() - start_time
            avg_relevance = sum(score for _, score in scored_results) / max(len(scored_results), 1)
            self.metrics.update_query_metrics(
                results_count=len(scored_results),
                avg_relevance=avg_relevance,
                response_time=response_time
            )
            
            logger.debug(
                f"{self.get_algorithm_name()} search completed: "
                f"{len(scored_results)} results for query '{query[:50]}...' "
                f"in {response_time:.3f}s"
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"{self.get_algorithm_name()} search failed: {e}")
            raise SparseRetrievalError(f"Search failed: {e}") from e
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text for sparse retrieval.
        
        Basic tokenization with philosophical text considerations.
        Can be overridden by subclasses for specialized tokenization.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Handle Greek text preservation (simplified)
        # In production, would use more sophisticated multilingual tokenization
        
        # Basic word tokenization
        tokens = re.findall(r'\b\w+\b', text)
        
        # Filter out very short tokens and common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        tokens = [token for token in tokens if len(token) > 2 and token not in stop_words]
        
        return tokens
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        if not self.index:
            return {}
        
        return {
            'algorithm': self.get_algorithm_name(),
            'total_documents': self.index.total_documents,
            'vocabulary_size': len(self.index.vocabulary),
            'average_document_length': self.index.average_document_length,
            'is_indexed': self._is_indexed
        }


class BM25Retriever(BaseSparseRetriever):
    """
    BM25 (Best Matching 25) sparse retrieval implementation.
    
    Implements the BM25 ranking function with configurable parameters
    for high-quality keyword-based retrieval on philosophical texts.
    
    BM25 is particularly effective for:
    - Exact term matching
    - Handling term frequency saturation
    - Document length normalization
    - Philosophical terminology precision
    """
    
    def __init__(
        self,
        k1: float = 1.2,
        b: float = 0.75,
        settings: Optional[Settings] = None
    ):
        """
        Initialize BM25 retriever with tunable parameters.
        
        Args:
            k1: Controls term frequency normalization (typically 1.2-2.0)
            b: Controls document length normalization (typically 0.75)
            settings: Configuration settings
        """
        super().__init__(settings)
        self.k1 = k1
        self.b = b
        
        logger.info(f"Initialized BM25Retriever (k1={k1}, b={b})")
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        return "BM25"
    
    def score_document(
        self,
        query_terms: List[str],
        document: TermFrequencyDocument
    ) -> float:
        """
        Calculate BM25 score for document given query terms.
        
        BM25 Formula:
        score = Σ(IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl)))
        
        Where:
        - IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5))
        - f(qi,D) = frequency of term qi in document D
        - |D| = length of document D in words
        - avgdl = average document length in collection
        - k1, b = tuning parameters
        
        Args:
            query_terms: List of query terms
            document: Document to score
            
        Returns:
            BM25 relevance score
        """
        if not self.index:
            return 0.0
        
        total_score = 0.0
        doc_length = document.total_terms
        avg_doc_length = self.index.average_document_length
        
        for term in query_terms:
            # Get term frequency in document
            tf = document.get_term_frequency(term)
            if tf == 0:
                continue
            
            # Calculate IDF
            df = self.index.get_document_frequency(term)
            if df == 0:
                continue
            
            idf = math.log((self.index.total_documents - df + 0.5) / (df + 0.5))
            
            # Calculate BM25 term score
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / max(avg_doc_length, 1)))
            
            term_score = idf * (numerator / denominator)
            total_score += term_score
        
        # Normalize score to 0-1 range (simple normalization)
        # In practice, you might use more sophisticated normalization
        normalized_score = min(1.0, max(0.0, total_score / max(len(query_terms), 1)))
        
        return normalized_score


class SPLADERetriever(BaseSparseRetriever):
    """
    SPLADE (Sparse Lexical and Expansion) retrieval implementation.
    
    SPLADE uses learned sparse representations that combine:
    - Lexical matching like BM25
    - Query/document expansion via learned importance weights
    - Neural relevance modeling
    
    This is a simplified implementation - production SPLADE requires
    trained transformer models for generating sparse representations.
    """
    
    def __init__(
        self,
        expansion_factor: float = 1.5,
        importance_threshold: float = 0.1,
        settings: Optional[Settings] = None
    ):
        """
        Initialize SPLADE retriever.
        
        Note: This is a simplified implementation. Production SPLADE
        requires trained models for generating learned sparse vectors.
        
        Args:
            expansion_factor: Factor for term expansion scoring
            importance_threshold: Minimum importance threshold for terms
            settings: Configuration settings
        """
        super().__init__(settings)
        self.expansion_factor = expansion_factor
        self.importance_threshold = importance_threshold
        
        logger.info(f"Initialized SPLADERetriever (simplified implementation)")
        logger.warning(
            "This is a simplified SPLADE implementation. "
            "Production SPLADE requires trained transformer models."
        )
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        return "SPLADE"
    
    def score_document(
        self,
        query_terms: List[str],
        document: TermFrequencyDocument
    ) -> float:
        """
        Calculate simplified SPLADE score for document.
        
        This simplified version combines:
        - BM25-style term matching
        - Simple term importance weighting
        - Pseudo-expansion based on term co-occurrence
        
        Args:
            query_terms: List of query terms
            document: Document to score
            
        Returns:
            SPLADE-inspired relevance score
        """
        if not self.index:
            return 0.0
        
        base_score = 0.0
        expansion_score = 0.0
        
        # Calculate base lexical matching score (BM25-like)
        for term in query_terms:
            tf = document.get_term_frequency(term)
            if tf == 0:
                continue
            
            # Simplified IDF calculation
            df = self.index.get_document_frequency(term)
            if df == 0:
                continue
            
            idf = math.log(self.index.total_documents / df)
            
            # Term importance (simplified - would use learned weights in production)
            term_importance = self._calculate_term_importance(term, document)
            
            if term_importance >= self.importance_threshold:
                base_score += idf * tf * term_importance
        
        # Calculate expansion score (simplified term co-occurrence)
        expansion_score = self._calculate_expansion_score(query_terms, document)
        
        # Combine scores
        total_score = base_score + (expansion_score * self.expansion_factor)
        
        # Normalize to 0-1 range
        normalized_score = min(1.0, max(0.0, total_score / max(len(query_terms) * 10, 1)))
        
        return normalized_score
    
    def _calculate_term_importance(self, term: str, document: TermFrequencyDocument) -> float:
        """
        Calculate simplified term importance.
        
        In production SPLADE, this would use learned importance weights
        from trained transformer models.
        """
        if not self.index:
            return 0.0
        
        # Simple heuristic: rarer terms are more important
        df = self.index.get_document_frequency(term)
        if df == 0:
            return 0.0
        
        # Inverse document frequency as importance proxy
        importance = 1.0 / (1.0 + math.log(df))
        
        # Boost philosophical terms
        philosophical_terms = {
            'virtue', 'ethics', 'justice', 'wisdom', 'knowledge', 'truth',
            'eudaimonia', 'arete', 'phronesis', 'sophia', 'episteme'
        }
        
        if term.lower() in philosophical_terms:
            importance *= 1.5
        
        return min(1.0, importance)
    
    def _calculate_expansion_score(
        self,
        query_terms: List[str],
        document: TermFrequencyDocument
    ) -> float:
        """
        Calculate simplified expansion score based on term co-occurrence.
        
        In production SPLADE, this would use learned expansion from
        trained models to find semantically related terms.
        """
        expansion_score = 0.0
        
        # Simple co-occurrence based expansion
        for doc_term, freq in document.term_frequencies.items():
            if doc_term not in query_terms:
                # Check if this term co-occurs with query terms frequently
                cooccurrence_score = self._calculate_cooccurrence(query_terms, doc_term)
                if cooccurrence_score > 0.1:
                    expansion_score += cooccurrence_score * freq
        
        return expansion_score
    
    def _calculate_cooccurrence(self, query_terms: List[str], candidate_term: str) -> float:
        """
        Calculate simplified co-occurrence score between query terms and candidate.
        
        This is a placeholder for more sophisticated co-occurrence analysis.
        """
        # Simple heuristic: check if terms appear together in documents
        if not self.index:
            return 0.0
        
        cooccurrence_count = 0
        total_checked = 0
        
        for term in query_terms:
            term_docs = self.index.get_term_documents(term)
            candidate_docs = self.index.get_term_documents(candidate_term)
            
            common_docs = set(term_docs.keys()) & set(candidate_docs.keys())
            if term_docs and candidate_docs:
                total_checked += 1
                if common_docs:
                    cooccurrence_count += len(common_docs) / max(len(term_docs), 1)
        
        if total_checked == 0:
            return 0.0
        
        return cooccurrence_count / total_checked


class SparseRetrievalService:
    """
    Main service for sparse retrieval operations.
    
    Coordinates different sparse retrieval algorithms (BM25, SPLADE)
    and provides a unified interface for sparse retrieval in the
    Arete Graph-RAG system.
    """
    
    def __init__(
        self,
        retriever_type: str = "bm25",
        neo4j_client: Optional[Neo4jClient] = None,
        settings: Optional[Settings] = None,
        **retriever_kwargs
    ):
        """
        Initialize sparse retrieval service.
        
        Args:
            retriever_type: Type of sparse retriever ("bm25" or "splade")
            neo4j_client: Neo4j client for chunk retrieval
            settings: Configuration settings
            **retriever_kwargs: Additional arguments for retriever initialization
        """
        self.settings = settings or get_settings()
        self.neo4j_client = neo4j_client
        
        # Initialize retriever
        self.retriever = self._create_retriever(retriever_type, **retriever_kwargs)
        
        logger.info(f"Initialized SparseRetrievalService with {retriever_type} retriever")
    
    def _create_retriever(self, retriever_type: str, **kwargs) -> BaseSparseRetriever:
        """Create sparse retriever instance."""
        if retriever_type.lower() == "bm25":
            return BM25Retriever(settings=self.settings, **kwargs)
        elif retriever_type.lower() == "splade":
            return SPLADERetriever(settings=self.settings, **kwargs)
        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")
    
    async def initialize_index(self, limit: Optional[int] = None) -> None:
        """
        Initialize sparse retrieval index from chunks in Neo4j.
        
        Args:
            limit: Optional limit on number of chunks to index
            
        Raises:
            IndexingError: If Neo4j client is not available or query fails
        """
        if self.neo4j_client is None:
            raise IndexingError("Neo4j client is required for index initialization")
            
        try:
            logger.info("Building sparse retrieval index from Neo4j chunks")
            
            # Fetch chunks from Neo4j
            query = """
            MATCH (c:Chunk)
            RETURN c.chunk_id as chunk_id,
                   c.document_id as document_id,
                   c.text as text,
                   c.chunk_type as chunk_type,
                   c.sequence_number as sequence_number,
                   c.word_count as word_count
            ORDER BY c.created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            results = await self.neo4j_client.execute_query(query)
            
            # Convert to Chunk objects
            chunks = []
            for record in results:
                chunk = Chunk(
                    chunk_id=UUID(record['chunk_id']),
                    document_id=UUID(record['document_id']),
                    text=record['text'],
                    chunk_type=record['chunk_type'],
                    sequence_number=record['sequence_number'],
                    word_count=record['word_count'],
                    start_char=0,  # Not stored in this query
                    end_char=len(record['text'])
                )
                chunks.append(chunk)
            
            # Build index
            self.retriever.build_index(chunks)
            
            logger.info(f"Sparse retrieval index built with {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to initialize sparse retrieval index: {e}")
            raise IndexingError(f"Index initialization failed: {e}") from e
    
    def search(
        self,
        query: str,
        limit: int = 10,
        min_relevance: float = 0.0,
        chunk_types: Optional[List[str]] = None,
        document_ids: Optional[List[UUID]] = None
    ) -> List[SearchResult]:
        """
        Perform sparse retrieval search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_relevance: Minimum relevance threshold
            chunk_types: Optional filter by chunk types
            document_ids: Optional filter by document IDs
            
        Returns:
            List of SearchResult objects
        """
        return self.retriever.search(
            query=query,
            limit=limit,
            min_relevance=min_relevance,
            chunk_types=chunk_types,
            document_ids=document_ids
        )
    
    def get_algorithm_name(self) -> str:
        """Get the current retrieval algorithm name."""
        return self.retriever.get_algorithm_name()
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return self.retriever.get_index_statistics()
    
    def get_metrics(self) -> RetrievalMetrics:
        """Get retrieval metrics."""
        return self.retriever.metrics


# Factory function following established pattern
def create_sparse_retrieval_service(
    retriever_type: str = "bm25",
    neo4j_client: Optional[Neo4jClient] = None,
    settings: Optional[Settings] = None,
    **retriever_kwargs
) -> SparseRetrievalService:
    """
    Create sparse retrieval service with dependency injection.
    
    Args:
        retriever_type: Type of sparse retriever ("bm25" or "splade")  
        neo4j_client: Optional Neo4j client instance (required for index initialization)
        settings: Optional configuration settings
        **retriever_kwargs: Additional retriever arguments
        
    Returns:
        Configured SparseRetrievalService instance
        
    Note:
        If neo4j_client is None, index initialization will fail.
        This is intentional to enforce proper dependency injection.
    """
    return SparseRetrievalService(
        retriever_type=retriever_type,
        neo4j_client=neo4j_client,
        settings=settings,
        **retriever_kwargs
    )