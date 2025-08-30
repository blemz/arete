"""
Tests for duplicate detection and deduplication service.

Tests the identification and removal of duplicate content including:
- Document-level duplicate detection
- Chunk-level duplicate detection  
- Citation duplicate detection
- Semantic similarity-based detection
- Exact match detection
- Fuzzy matching for near-duplicates
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime, timezone

from arete.services.data_quality.duplicate_detection_service import (
    DuplicateDetectionService,
    DuplicateResult,
    SimilarityMetrics,
    DuplicationStrategy,
    DeduplicationResult
)
from arete.models.document import Document
from arete.models.chunk import Chunk, ChunkType
from arete.models.citation import Citation, CitationType


class TestDuplicateDetectionService:
    """Test suite for duplicate detection service."""
    
    @pytest.fixture
    def detection_service(self):
        """Create duplicate detection service instance."""
        return DuplicateDetectionService()
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            Document(
                title="The Republic",
                author="Plato", 
                content="Justice is the advantage of the stronger...",
                metadata={"source": "perseus"}
            ),
            Document(
                title="Republic", 
                author="Plato",
                content="Justice is the advantage of the stronger...",  # Same content
                metadata={"source": "gutenberg"}
            ),
            Document(
                title="Nicomachean Ethics",
                author="Aristotle",
                content="Every art and every inquiry aims at some good...",
                metadata={"source": "perseus"}
            )
        ]
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for testing."""
        return [
            Chunk(
                text="Virtue is excellence of character developed through habit.",
                chunk_type=ChunkType.PARAGRAPH,
                source_document_id=uuid4(),
                metadata={"page": 1}
            ),
            Chunk(
                text="Virtue is excellence of character developed through habit.",  # Exact duplicate
                chunk_type=ChunkType.PARAGRAPH,
                source_document_id=uuid4(),
                metadata={"page": 2}
            ),
            Chunk(
                text="Excellence of character (virtue) is developed through habituation.",  # Near duplicate
                chunk_type=ChunkType.PARAGRAPH, 
                source_document_id=uuid4(),
                metadata={"page": 3}
            ),
            Chunk(
                text="Justice is each part doing its own work without meddling.",
                chunk_type=ChunkType.PARAGRAPH,
                source_document_id=uuid4(),
                metadata={"page": 4}
            )
        ]
    
    @pytest.fixture
    def sample_citations(self):
        """Sample citations for testing."""
        return [
            Citation(
                text="Justice is each part doing its own work",
                reference="Republic 433a",
                citation_type=CitationType.DIRECT_QUOTE
            ),
            Citation(
                text="Justice is each part doing its own work",  # Exact duplicate
                reference="Rep. 433a",  # Different reference format
                citation_type=CitationType.DIRECT_QUOTE
            ),
            Citation(
                text="Each part should do its own work for justice",  # Paraphrase
                reference="Republic 433a",
                citation_type=CitationType.PARAPHRASE
            )
        ]

    def test_service_initialization(self, detection_service):
        """Test service initializes properly."""
        assert detection_service is not None
        assert hasattr(detection_service, 'similarity_threshold')
        assert hasattr(detection_service, 'strategies')
        
    def test_exact_duplicate_detection_documents(self, detection_service, sample_documents):
        """Test exact duplicate detection for documents."""
        duplicates = detection_service.find_exact_duplicates(
            sample_documents, 
            field='content'
        )
        
        assert len(duplicates) == 1  # One pair of duplicates
        duplicate_group = duplicates[0]
        assert len(duplicate_group.items) == 2
        assert duplicate_group.similarity_score == 1.0
        assert duplicate_group.detection_method == 'exact_match'

    def test_exact_duplicate_detection_chunks(self, detection_service, sample_chunks):
        """Test exact duplicate detection for chunks."""
        duplicates = detection_service.find_exact_duplicates(
            sample_chunks,
            field='text'
        )
        
        assert len(duplicates) == 1
        duplicate_group = duplicates[0]
        assert len(duplicate_group.items) == 2
        assert all(chunk.text == sample_chunks[0].text for chunk in duplicate_group.items)

    @pytest.mark.asyncio
    async def test_semantic_duplicate_detection(self, detection_service, sample_chunks):
        """Test semantic similarity-based duplicate detection."""
        with patch.object(detection_service, '_calculate_semantic_similarity') as mock_similarity:
            # Mock semantic similarity scores
            mock_similarity.side_effect = lambda a, b: 0.85 if "virtue" in a.lower() and "excellence" in b.lower() else 0.3
            
            duplicates = await detection_service.find_semantic_duplicates(
                sample_chunks,
                similarity_threshold=0.8
            )
            
            # Should find the near-duplicate virtue chunks
            assert len(duplicates) >= 1
            
            # Check that semantic duplicates were found
            semantic_duplicate = next(
                (dup for dup in duplicates if dup.detection_method == 'semantic_similarity'),
                None
            )
            assert semantic_duplicate is not None
            assert semantic_duplicate.similarity_score >= 0.8

    def test_fuzzy_matching_detection(self, detection_service, sample_citations):
        """Test fuzzy string matching for near-duplicates."""
        duplicates = detection_service.find_fuzzy_duplicates(
            sample_citations,
            field='text',
            fuzzy_threshold=0.8
        )
        
        # Should find citations with similar text
        assert len(duplicates) >= 1
        
        # Check fuzzy matching detected near-duplicates
        fuzzy_duplicate = duplicates[0]
        assert fuzzy_duplicate.detection_method == 'fuzzy_matching'
        assert 0.8 <= fuzzy_duplicate.similarity_score < 1.0

    @pytest.mark.asyncio
    async def test_comprehensive_duplicate_detection(self, detection_service, sample_documents):
        """Test comprehensive duplicate detection using multiple strategies."""
        results = await detection_service.detect_all_duplicates(
            sample_documents,
            strategies=[
                DuplicationStrategy.EXACT_MATCH,
                DuplicationStrategy.SEMANTIC_SIMILARITY,
                DuplicationStrategy.FUZZY_MATCHING
            ]
        )
        
        assert isinstance(results, list)
        assert len(results) >= 1  # Should find at least the exact duplicates
        
        # Check that different strategies were used
        detection_methods = {result.detection_method for result in results}
        assert 'exact_match' in detection_methods

    def test_similarity_metrics_calculation(self, detection_service):
        """Test calculation of similarity metrics."""
        text1 = "Virtue is excellence of character"
        text2 = "Excellence of character is virtue"
        
        metrics = detection_service.calculate_similarity_metrics(text1, text2)
        
        assert isinstance(metrics, SimilarityMetrics)
        assert 0.0 <= metrics.jaccard_similarity <= 1.0
        assert 0.0 <= metrics.cosine_similarity <= 1.0
        assert 0.0 <= metrics.levenshtein_similarity <= 1.0
        assert 0.0 <= metrics.semantic_similarity <= 1.0

    @pytest.mark.asyncio
    async def test_deduplication_process(self, detection_service, sample_chunks):
        """Test the deduplication process."""
        dedup_result = await detection_service.deduplicate_items(
            sample_chunks,
            keep_strategy='highest_quality'
        )
        
        assert isinstance(dedup_result, DeduplicationResult)
        assert len(dedup_result.kept_items) < len(sample_chunks)
        assert len(dedup_result.removed_items) > 0
        assert len(dedup_result.kept_items) + len(dedup_result.removed_items) == len(sample_chunks)

    def test_deduplication_keep_strategies(self, detection_service, sample_chunks):
        """Test different strategies for keeping items during deduplication."""
        # Test keep first strategy
        result_first = detection_service._apply_keep_strategy(
            [sample_chunks[0], sample_chunks[1]], 
            'keep_first'
        )
        assert result_first == sample_chunks[0]
        
        # Test keep last strategy  
        result_last = detection_service._apply_keep_strategy(
            [sample_chunks[0], sample_chunks[1]], 
            'keep_last'
        )
        assert result_last == sample_chunks[1]

    def test_quality_based_deduplication(self, detection_service, sample_documents):
        """Test quality-based item selection during deduplication."""
        # Documents with different quality indicators
        doc1 = sample_documents[0]  # Original
        doc2 = sample_documents[1]  # Duplicate with different metadata
        
        # Test quality comparison
        better_doc = detection_service._select_higher_quality_item([doc1, doc2])
        
        # Should select based on quality heuristics
        assert better_doc in [doc1, doc2]

    def test_duplicate_result_serialization(self, detection_service, sample_chunks):
        """Test serialization of duplicate results."""
        duplicates = detection_service.find_exact_duplicates(sample_chunks, field='text')
        
        if duplicates:
            duplicate_result = duplicates[0]
            
            # Test serialization
            serialized = duplicate_result.model_dump()
            assert 'similarity_score' in serialized
            assert 'detection_method' in serialized
            assert 'items' in serialized
            
            # Test deserialization
            deserialized = DuplicateResult.model_validate(serialized)
            assert deserialized.similarity_score == duplicate_result.similarity_score

    def test_batch_duplicate_detection(self, detection_service, sample_documents):
        """Test batch processing for large document sets."""
        # Create larger dataset
        large_dataset = sample_documents * 10  # 30 documents
        
        duplicates = detection_service.find_exact_duplicates(
            large_dataset, 
            field='content',
            batch_size=5
        )
        
        # Should still find duplicates efficiently
        assert len(duplicates) >= 1

    @pytest.mark.asyncio
    async def test_cross_collection_duplicate_detection(self, detection_service):
        """Test duplicate detection across different collections."""
        documents = [
            Document(title="Test Doc", author="Author", content="Test content"),
        ]
        chunks = [
            Chunk(text="Test content", chunk_type=ChunkType.PARAGRAPH, source_document_id=uuid4()),
        ]
        
        # Should detect duplicates across different types
        results = await detection_service.detect_cross_collection_duplicates(
            collections={'documents': documents, 'chunks': chunks},
            text_fields={'documents': 'content', 'chunks': 'text'}
        )
        
        assert isinstance(results, dict)
        assert 'cross_collection_duplicates' in results

    def test_duplicate_statistics_calculation(self, detection_service, sample_documents):
        """Test calculation of duplication statistics."""
        duplicates = detection_service.find_exact_duplicates(sample_documents, field='content')
        
        stats = detection_service.calculate_duplication_statistics(
            total_items=len(sample_documents),
            duplicates=duplicates
        )
        
        assert 'total_items' in stats
        assert 'duplicate_groups' in stats
        assert 'duplication_rate' in stats
        assert 'items_affected' in stats
        assert 0.0 <= stats['duplication_rate'] <= 1.0

    def test_custom_similarity_function(self, detection_service):
        """Test registration of custom similarity functions."""
        def custom_philosophical_similarity(text1: str, text2: str) -> float:
            """Custom similarity for philosophical texts."""
            philosophical_terms = ['virtue', 'justice', 'good', 'truth', 'beauty']
            
            terms1 = set(term for term in philosophical_terms if term in text1.lower())
            terms2 = set(term for term in philosophical_terms if term in text2.lower())
            
            if not terms1 and not terms2:
                return 0.0
            
            intersection = len(terms1.intersection(terms2))
            union = len(terms1.union(terms2))
            
            return intersection / union if union > 0 else 0.0
        
        # Register custom function
        detection_service.register_similarity_function(
            'philosophical_similarity', 
            custom_philosophical_similarity
        )
        
        # Test custom similarity
        similarity = detection_service.calculate_custom_similarity(
            "Virtue is excellence",
            "Justice and virtue are good",
            'philosophical_similarity'
        )
        
        assert 0.0 <= similarity <= 1.0

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, detection_service, sample_documents):
        """Test performance monitoring during duplicate detection."""
        with patch.object(detection_service, '_monitor_performance') as mock_monitor:
            mock_monitor.return_value = {'processing_time': 0.5, 'items_processed': len(sample_documents)}
            
            duplicates = detection_service.find_exact_duplicates(sample_documents, field='content')
            
            # Performance should be monitored
            mock_monitor.assert_called()

    def test_error_handling_invalid_input(self, detection_service):
        """Test error handling with invalid inputs."""
        # Empty input
        duplicates = detection_service.find_exact_duplicates([], field='content')
        assert len(duplicates) == 0
        
        # Invalid field
        with pytest.raises(ValueError):
            detection_service.find_exact_duplicates(
                [Document(title="Test", author="Author", content="Content")], 
                field='nonexistent_field'
            )

    def test_memory_efficient_processing(self, detection_service):
        """Test memory-efficient processing for large datasets."""
        # Mock large dataset
        large_dataset = [
            Document(title=f"Doc {i}", author="Author", content=f"Content {i % 5}")  # Some duplicates
            for i in range(100)
        ]
        
        # Should handle large datasets without memory issues
        duplicates = detection_service.find_exact_duplicates(
            large_dataset, 
            field='content',
            batch_size=10,
            memory_efficient=True
        )
        
        assert isinstance(duplicates, list)

    @pytest.mark.asyncio 
    async def test_incremental_duplicate_detection(self, detection_service, sample_documents):
        """Test incremental duplicate detection for streaming data."""
        # Existing items
        existing_items = sample_documents[:2]
        
        # New items to check
        new_items = sample_documents[2:]
        
        # Find duplicates in new items against existing
        duplicates = await detection_service.detect_incremental_duplicates(
            existing_items=existing_items,
            new_items=new_items,
            field='content'
        )
        
        assert isinstance(duplicates, list)


class TestSimilarityMetrics:
    """Test suite for similarity metrics calculations."""
    
    def test_metrics_initialization(self):
        """Test similarity metrics initialization."""
        metrics = SimilarityMetrics(
            jaccard_similarity=0.8,
            cosine_similarity=0.85,
            levenshtein_similarity=0.9,
            semantic_similarity=0.82
        )
        
        assert metrics.jaccard_similarity == 0.8
        assert metrics.cosine_similarity == 0.85
        assert metrics.levenshtein_similarity == 0.9
        assert metrics.semantic_similarity == 0.82
    
    def test_overall_similarity_calculation(self):
        """Test overall similarity score calculation."""
        metrics = SimilarityMetrics(
            jaccard_similarity=0.8,
            cosine_similarity=0.85, 
            levenshtein_similarity=0.9,
            semantic_similarity=0.82
        )
        
        overall = metrics.calculate_overall_similarity()
        assert 0.0 <= overall <= 1.0
        assert overall > 0.8  # Should be high given high individual scores
    
    def test_metrics_validation(self):
        """Test validation of similarity metric values."""
        # Valid metrics
        valid_metrics = SimilarityMetrics(
            jaccard_similarity=0.5,
            cosine_similarity=0.7,
            levenshtein_similarity=0.6,
            semantic_similarity=0.8
        )
        assert valid_metrics.jaccard_similarity == 0.5
        
        # Invalid metrics (should be constrained to 0-1 range)
        with pytest.raises(ValueError):
            SimilarityMetrics(
                jaccard_similarity=1.5,  # Invalid
                cosine_similarity=0.7,
                levenshtein_similarity=0.6,
                semantic_similarity=0.8
            )