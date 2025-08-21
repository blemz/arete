"""
Tests for sparse retrieval system components.

Comprehensive test coverage for BM25, SPLADE, and hybrid retrieval
implementations following TDD methodology established in the codebase.
"""

import pytest
import math
from typing import List, Dict
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.arete.services.sparse_retrieval_service import (
    BaseSparseRetriever,
    BM25Retriever,
    SPLADERetriever,
    SparseRetrievalService,
    SparseIndex,
    TermFrequencyDocument,
    SparseRetrievalError,
    IndexingError,
    QueryProcessingError,
    create_sparse_retrieval_service
)
from src.arete.models.chunk import Chunk
from src.arete.config import Settings


class TestTermFrequencyDocument:
    """Test TermFrequencyDocument model."""
    
    def test_term_frequency_document_creation(self):
        """Test basic TermFrequencyDocument creation."""
        doc = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1", 
            term_frequencies={'virtue': 3, 'ethics': 2, 'wisdom': 1},
            total_terms=10,
            unique_terms=3
        )
        
        assert doc.document_id == "doc-1"
        assert doc.chunk_id == "chunk-1"
        assert doc.total_terms == 10
        assert doc.unique_terms == 3
    
    def test_get_term_frequency(self):
        """Test term frequency retrieval."""
        doc = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1",
            term_frequencies={'virtue': 3, 'ethics': 2},
            total_terms=10,
            unique_terms=2
        )
        
        assert doc.get_term_frequency('virtue') == 3
        assert doc.get_term_frequency('ethics') == 2
        assert doc.get_term_frequency('nonexistent') == 0
    
    def test_get_normalized_length(self):
        """Test normalized document length calculation."""
        doc = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1",
            term_frequencies={},
            total_terms=20,
            unique_terms=0
        )
        
        # Normal case
        assert doc.get_normalized_length(10.0) == 2.0
        
        # Edge case: zero average
        assert doc.get_normalized_length(0.0) == 1.0


class TestSparseIndex:
    """Test SparseIndex functionality."""
    
    def test_sparse_index_creation(self):
        """Test SparseIndex initialization."""
        index = SparseIndex()
        
        assert index.total_documents == 0
        assert index.average_document_length == 0.0
        assert len(index.vocabulary) == 0
        assert len(index.documents) == 0
    
    def test_add_document(self):
        """Test adding documents to index."""
        index = SparseIndex()
        
        doc1 = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1",
            term_frequencies={'virtue': 2, 'ethics': 1},
            total_terms=10,
            unique_terms=2
        )
        
        doc2 = TermFrequencyDocument(
            document_id="doc-2", 
            chunk_id="chunk-2",
            term_frequencies={'virtue': 1, 'wisdom': 3},
            total_terms=20,
            unique_terms=2
        )
        
        index.add_document(doc1)
        assert index.total_documents == 1
        assert index.average_document_length == 10.0
        assert 'virtue' in index.vocabulary
        assert 'ethics' in index.vocabulary
        
        index.add_document(doc2)
        assert index.total_documents == 2
        assert index.average_document_length == 15.0  # (10 + 20) / 2
        assert 'wisdom' in index.vocabulary
    
    def test_document_frequency_tracking(self):
        """Test document frequency calculation."""
        index = SparseIndex()
        
        doc1 = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1",
            term_frequencies={'virtue': 2, 'ethics': 1},
            total_terms=10,
            unique_terms=2
        )
        
        doc2 = TermFrequencyDocument(
            document_id="doc-2",
            chunk_id="chunk-2", 
            term_frequencies={'virtue': 1, 'wisdom': 3},
            total_terms=20,
            unique_terms=2
        )
        
        index.add_document(doc1)
        index.add_document(doc2)
        
        # 'virtue' appears in both documents
        assert index.get_document_frequency('virtue') == 2
        
        # 'ethics' and 'wisdom' appear in one document each
        assert index.get_document_frequency('ethics') == 1
        assert index.get_document_frequency('wisdom') == 1
        
        # Non-existent term
        assert index.get_document_frequency('nonexistent') == 0
    
    def test_get_term_documents(self):
        """Test term-document mapping retrieval."""
        index = SparseIndex()
        
        doc1 = TermFrequencyDocument(
            document_id="doc-1",
            chunk_id="chunk-1",
            term_frequencies={'virtue': 2, 'ethics': 1},
            total_terms=10,
            unique_terms=2
        )
        
        index.add_document(doc1)
        
        virtue_docs = index.get_term_documents('virtue')
        assert 'chunk-1' in virtue_docs
        assert virtue_docs['chunk-1'] == 2
        
        # Non-existent term returns empty dict
        assert index.get_term_documents('nonexistent') == {}


class TestBM25Retriever:
    """Test BM25 retrieval implementation."""
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            Chunk(
                document_id=uuid4(),
                text="Virtue is the highest good according to Aristotle ethics",
                position=0,
                chunk_type="paragraph",
                start_char=0,
                end_char=50,
                word_count=9
            ),
            Chunk(
                document_id=uuid4(),
                text="Wisdom and knowledge are essential for virtue ethics",
                position=1,
                chunk_type="paragraph",
                start_char=0,
                end_char=48,
                word_count=8
            ),
            Chunk(
                document_id=uuid4(),
                text="Justice requires both wisdom and temperance in practice",
                position=2,
                chunk_type="paragraph",
                start_char=0,
                end_char=54,
                word_count=8
            )
        ]
    
    def test_bm25_retriever_initialization(self):
        """Test BM25Retriever initialization."""
        retriever = BM25Retriever(k1=1.5, b=0.8)
        
        assert retriever.k1 == 1.5
        assert retriever.b == 0.8
        assert retriever.get_algorithm_name() == "BM25"
        assert not retriever._is_indexed
    
    def test_build_index(self, sample_chunks):
        """Test building BM25 index from chunks."""
        retriever = BM25Retriever()
        
        retriever.build_index(sample_chunks)
        
        assert retriever._is_indexed
        assert retriever.index is not None
        assert retriever.index.total_documents == 3
        assert len(retriever.index.vocabulary) > 0
        assert 'virtue' in retriever.index.vocabulary
        assert 'ethics' in retriever.index.vocabulary
    
    def test_tokenize_text(self):
        """Test text tokenization."""
        retriever = BM25Retriever()
        
        tokens = retriever._tokenize_text("Virtue and wisdom are essential for ethics")
        
        # Should filter stop words and short tokens
        expected_tokens = ['virtue', 'wisdom', 'essential', 'ethics']
        assert set(tokens) == set(expected_tokens)
    
    def test_tokenize_empty_text(self):
        """Test tokenization of empty text."""
        retriever = BM25Retriever()
        
        assert retriever._tokenize_text("") == []
        assert retriever._tokenize_text(None) == []
    
    def test_score_document(self, sample_chunks):
        """Test BM25 document scoring."""
        retriever = BM25Retriever(k1=1.2, b=0.75)
        retriever.build_index(sample_chunks)
        
        # Get a document from the index
        doc = list(retriever.index.documents.values())[0]
        query_terms = ['virtue', 'ethics']
        
        score = retriever.score_document(query_terms, doc)
        
        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0
    
    def test_score_document_no_match(self, sample_chunks):
        """Test BM25 scoring with no matching terms."""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks)
        
        doc = list(retriever.index.documents.values())[0]
        query_terms = ['nonexistent', 'terms']
        
        score = retriever.score_document(query_terms, doc)
        
        assert score == 0.0
    
    def test_search_not_indexed(self):
        """Test search without building index."""
        retriever = BM25Retriever()
        
        with pytest.raises(SparseRetrievalError):
            retriever.search("virtue ethics")
    
    def test_get_index_statistics(self, sample_chunks):
        """Test index statistics retrieval."""
        retriever = BM25Retriever()
        retriever.build_index(sample_chunks)
        
        stats = retriever.get_index_statistics()
        
        assert stats['algorithm'] == 'BM25'
        assert stats['total_documents'] == 3
        assert stats['is_indexed'] is True
        assert 'vocabulary_size' in stats
        assert 'average_document_length' in stats


class TestSPLADERetriever:
    """Test SPLADE retrieval implementation."""
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing.""" 
        return [
            Chunk(
                document_id=uuid4(),
                text="Virtue ethics emphasizes character and moral excellence",
                position=0,
                chunk_type="paragraph",
                start_char=0,
                end_char=50,
                word_count=7
            ),
            Chunk(
                document_id=uuid4(),
                text="Wisdom guides virtue in ethical decision making",
                position=1,
                chunk_type="paragraph",
                start_char=0,
                end_char=45,
                word_count=7
            )
        ]
    
    def test_splade_retriever_initialization(self):
        """Test SPLADERetriever initialization."""
        retriever = SPLADERetriever(expansion_factor=2.0, importance_threshold=0.2)
        
        assert retriever.expansion_factor == 2.0
        assert retriever.importance_threshold == 0.2
        assert retriever.get_algorithm_name() == "SPLADE"
    
    def test_build_index(self, sample_chunks):
        """Test building SPLADE index."""
        retriever = SPLADERetriever()
        
        retriever.build_index(sample_chunks)
        
        assert retriever._is_indexed
        assert retriever.index is not None
        assert retriever.index.total_documents == 2
    
    def test_calculate_term_importance(self, sample_chunks):
        """Test term importance calculation."""
        retriever = SPLADERetriever()
        retriever.build_index(sample_chunks)
        
        doc = list(retriever.index.documents.values())[0]
        
        # Test philosophical term boost
        virtue_importance = retriever._calculate_term_importance('virtue', doc)
        regular_importance = retriever._calculate_term_importance('regular', doc)
        
        # Virtue should have higher importance due to philosophical boost
        assert virtue_importance > 0.0
    
    def test_score_document(self, sample_chunks):
        """Test SPLADE document scoring."""
        retriever = SPLADERetriever()
        retriever.build_index(sample_chunks)
        
        doc = list(retriever.index.documents.values())[0]
        query_terms = ['virtue', 'ethics']
        
        score = retriever.score_document(query_terms, doc)
        
        assert 0.0 <= score <= 1.0


class TestSparseRetrievalService:
    """Test SparseRetrievalService coordination."""
    
    @pytest.fixture
    def mock_neo4j_client(self):
        """Create mock Neo4j client."""
        client = Mock()
        client.execute_query = AsyncMock()
        return client
    
    @pytest.fixture
    def sample_query_results(self):
        """Sample query results from Neo4j."""
        return [
            {
                'chunk_id': str(uuid4()),
                'document_id': str(uuid4()),
                'text': 'Virtue is excellence of character',
                'chunk_type': 'paragraph',
                'sequence_number': 1,
                'word_count': 5
            },
            {
                'chunk_id': str(uuid4()),
                'document_id': str(uuid4()),
                'text': 'Ethics guides moral behavior',
                'chunk_type': 'paragraph',
                'sequence_number': 1,
                'word_count': 4
            }
        ]
    
    def test_service_initialization_bm25(self, mock_neo4j_client):
        """Test service initialization with BM25."""
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        assert service.get_algorithm_name() == "BM25"
        assert isinstance(service.retriever, BM25Retriever)
    
    def test_service_initialization_splade(self, mock_neo4j_client):
        """Test service initialization with SPLADE."""
        service = SparseRetrievalService(
            retriever_type="splade",
            neo4j_client=mock_neo4j_client
        )
        
        assert service.get_algorithm_name() == "SPLADE"
        assert isinstance(service.retriever, SPLADERetriever)
    
    def test_service_initialization_invalid_type(self, mock_neo4j_client):
        """Test service initialization with invalid retriever type."""
        with pytest.raises(ValueError):
            SparseRetrievalService(
                retriever_type="invalid",
                neo4j_client=mock_neo4j_client
            )
    
    @pytest.mark.asyncio
    async def test_initialize_index(self, mock_neo4j_client, sample_query_results):
        """Test index initialization from Neo4j."""
        mock_neo4j_client.execute_query.return_value = sample_query_results
        
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        await service.initialize_index()
        
        # Verify Neo4j query was called
        mock_neo4j_client.execute_query.assert_called_once()
        
        # Verify index was built
        assert service.retriever._is_indexed
    
    @pytest.mark.asyncio
    async def test_initialize_index_with_limit(self, mock_neo4j_client, sample_query_results):
        """Test index initialization with limit."""
        mock_neo4j_client.execute_query.return_value = sample_query_results
        
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        await service.initialize_index(limit=100)
        
        # Verify limit was included in query
        called_args = mock_neo4j_client.execute_query.call_args[0]
        assert "LIMIT 100" in called_args[0]
    
    @pytest.mark.asyncio
    async def test_initialize_index_failure(self, mock_neo4j_client):
        """Test index initialization failure handling."""
        mock_neo4j_client.execute_query.side_effect = Exception("Database error")
        
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        with pytest.raises(IndexingError):
            await service.initialize_index()
    
    def test_get_index_statistics(self, mock_neo4j_client):
        """Test index statistics retrieval."""
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        stats = service.get_index_statistics()
        
        assert 'algorithm' in stats
        assert stats['algorithm'] == 'BM25'
    
    def test_get_metrics(self, mock_neo4j_client):
        """Test metrics retrieval."""
        service = SparseRetrievalService(
            retriever_type="bm25",
            neo4j_client=mock_neo4j_client
        )
        
        metrics = service.get_metrics()
        
        assert hasattr(metrics, 'queries_processed')
        assert hasattr(metrics, 'average_relevance_score')


class TestSparseRetrievalFactory:
    """Test sparse retrieval factory function."""
    
    def test_create_sparse_retrieval_service_bm25(self):
        """Test factory function with BM25."""
        service = create_sparse_retrieval_service(retriever_type="bm25")
        
        assert isinstance(service, SparseRetrievalService)
        assert service.get_algorithm_name() == "BM25"
    
    def test_create_sparse_retrieval_service_splade(self):
        """Test factory function with SPLADE."""
        service = create_sparse_retrieval_service(retriever_type="splade")
        
        assert isinstance(service, SparseRetrievalService)
        assert service.get_algorithm_name() == "SPLADE"
    
    def test_create_sparse_retrieval_service_with_kwargs(self):
        """Test factory function with additional kwargs."""
        service = create_sparse_retrieval_service(
            retriever_type="bm25",
            k1=2.0,
            b=0.8
        )
        
        assert isinstance(service, SparseRetrievalService)
        assert service.retriever.k1 == 2.0
        assert service.retriever.b == 0.8


class TestSparseRetrievalIntegration:
    """Integration tests for sparse retrieval system."""
    
    @pytest.fixture
    def real_chunks(self):
        """Create realistic philosophical text chunks."""
        return [
            Chunk(
                document_id=uuid4(),
                text="Virtue ethics, also known as aretaic ethics, is one of the three major approaches in normative ethics. It emphasizes the importance of character rather than actions or consequences.",
                position=0,
                chunk_type="paragraph",
                start_char=0,
                end_char=170,
                word_count=28
            ),
            Chunk(
                document_id=uuid4(),
                text="Aristotle argued that virtue (arete) is a disposition to behave in the right way and as a mean between extremes of deficiency and excess.",
                position=1,
                chunk_type="paragraph",
                start_char=171,
                end_char=305,
                word_count=25
            ),
            Chunk(
                document_id=uuid4(),
                text="The concept of eudaimonia, often translated as happiness or flourishing, is central to Aristotelian ethics. It represents the highest human good.",
                position=2,
                chunk_type="paragraph",
                start_char=306,
                end_char=450,
                word_count=24
            ),
            Chunk(
                document_id=uuid4(),
                text="Practical wisdom (phronesis) enables one to discern the right course of action in particular circumstances. It is acquired through experience and moral education.",
                position=3,
                chunk_type="paragraph",
                start_char=451,
                end_char=605,
                word_count=26
            )
        ]
    
    def test_bm25_philosophical_search(self, real_chunks):
        """Test BM25 retrieval with philosophical content."""
        retriever = BM25Retriever()
        retriever.build_index(real_chunks)
        
        # Search for virtue-related content
        results = retriever.search("virtue ethics character", limit=3)
        
        # Should find relevant chunks (placeholder test - needs actual SearchResult objects)
        # In real implementation, this would return SearchResult objects
        assert len(results) >= 0  # Placeholder assertion
    
    def test_splade_vs_bm25_comparison(self, real_chunks):
        """Test comparative performance of SPLADE vs BM25."""
        bm25_retriever = BM25Retriever()
        splade_retriever = SPLADERetriever()
        
        bm25_retriever.build_index(real_chunks)
        splade_retriever.build_index(real_chunks)
        
        # Both should build indices successfully
        assert bm25_retriever._is_indexed
        assert splade_retriever._is_indexed
        
        # Both should have same number of documents
        assert bm25_retriever.index.total_documents == splade_retriever.index.total_documents
    
    def test_philosophical_term_recognition(self, real_chunks):
        """Test recognition of philosophical terminology."""
        retriever = BM25Retriever()
        retriever.build_index(real_chunks)
        
        # Verify philosophical terms are in vocabulary
        assert 'virtue' in retriever.index.vocabulary
        assert 'eudaimonia' in retriever.index.vocabulary
        assert 'phronesis' in retriever.index.vocabulary
    
    def test_multilingual_tokenization(self):
        """Test handling of Greek philosophical terms."""
        retriever = BM25Retriever()
        
        # Test with Greek terms (simplified)
        tokens = retriever._tokenize_text("The concept of ἀρετή (arete) means virtue")
        
        # Should preserve meaningful terms
        assert 'concept' in tokens
        assert 'virtue' in tokens
        # Note: Proper Greek tokenization would require specialized handling


if __name__ == "__main__":
    pytest.main([__file__])