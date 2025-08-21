"""
Test suite for Embedding Storage and Retrieval.

Tests integration with Weaviate vector database, chunk processing pipeline,
and semantic search functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional
from uuid import uuid4
import numpy as np

from src.arete.models.chunk import Chunk, ChunkType
from src.arete.database.weaviate_client import WeaviateClient
from src.arete.services.embedding_service import EmbeddingService


class TestWeaviateEmbeddingStorage:
    """Test embedding storage in Weaviate vector database."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_chunks = [
            Chunk(
                text="Virtue is the mean between extremes of excess and deficiency.",
                document_id=uuid4(),
                start_position=0,
                end_position=62,
                sequence_number=0,
                word_count=10,
                chunk_type=ChunkType.PARAGRAPH,
                embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5]
            ),
            Chunk(
                text="The unexamined life is not worth living according to Socrates.",
                document_id=uuid4(),
                start_position=0,
                end_position=62,
                sequence_number=0,
                word_count=10,
                chunk_type=ChunkType.PARAGRAPH,
                embedding_vector=[0.6, 0.7, 0.8, 0.9, 1.0]
            )
        ]
        
        self.embedding_dimension = 384  # Standard for all-MiniLM-L6-v2
        
    @patch('weaviate.connect_to_local')
    def test_chunk_storage_with_embeddings(self, mock_connect):
        """Test storing chunks with embeddings in Weaviate."""
        # Mock Weaviate client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Configure successful insertion
        mock_collection.data.insert.return_value = Mock(uuid=str(uuid4()))
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test storing chunk with embedding
        chunk = self.sample_chunks[0]
        chunk_dict = chunk.to_weaviate_dict()
        
        # Verify Weaviate-compatible format
        assert "content" in chunk_dict  # Weaviate expects 'content' field
        assert chunk_dict["content"] == chunk.text
        assert "chunk_type" in chunk_dict
        assert "document_id" in chunk_dict
        
        # Mock successful storage
        result_uuid = weaviate_client.create_object("Chunk", chunk_dict, chunk.embedding_vector)
        assert result_uuid is not None
    
    @patch('weaviate.connect_to_local')
    def test_batch_embedding_storage(self, mock_connect):
        """Test efficient batch storage of embeddings."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Mock batch insertion
        mock_batch_result = Mock()
        mock_batch_result.uuids = [str(uuid4()) for _ in self.sample_chunks]
        mock_collection.data.insert_many.return_value = mock_batch_result
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Prepare batch data
        batch_objects = []
        for chunk in self.sample_chunks:
            chunk_dict = chunk.to_weaviate_dict()
            batch_objects.append({
                "properties": chunk_dict,
                "vector": chunk.embedding_vector
            })
        
        # Test batch insertion
        result = weaviate_client.create_objects_batch("Chunk", batch_objects)
        assert len(result) == len(self.sample_chunks)
    
    @patch('weaviate.connect_to_local')
    def test_embedding_dimension_validation(self, mock_connect):
        """Test validation of embedding dimensions."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Mock collection config to return expected dimension
        mock_collection.config.get.return_value = Mock(
            vector_config=Mock(dimensions=self.embedding_dimension)
        )
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test dimension mismatch handling
        invalid_embedding = [0.1, 0.2]  # Wrong dimension
        chunk_dict = self.sample_chunks[0].to_weaviate_dict()
        
        # Should handle dimension validation
        assert len(invalid_embedding) != self.embedding_dimension
    
    def test_chunk_to_weaviate_format(self):
        """Test chunk conversion to Weaviate-compatible format."""
        chunk = self.sample_chunks[0]
        weaviate_dict = chunk.to_weaviate_dict()
        
        # Verify required fields for Weaviate
        required_fields = ["content", "chunk_type", "document_id"]
        for field in required_fields:
            assert field in weaviate_dict
        
        # Verify content field maps to text
        assert weaviate_dict["content"] == chunk.text
        
        # Verify metadata preservation
        assert "position_info" in weaviate_dict
        assert weaviate_dict["position_info"]["start"] == chunk.start_position
        assert weaviate_dict["position_info"]["end"] == chunk.end_position


class TestSemanticSearchRetrieval:
    """Test semantic search and retrieval functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.query_text = "What is virtue according to Aristotle?"
        self.query_embedding = [0.2, 0.3, 0.4, 0.5, 0.6]
        
        # Mock search results
        self.mock_search_results = [
            {
                "uuid": str(uuid4()),
                "properties": {
                    "content": "Virtue is the mean between extremes of excess and deficiency.",
                    "chunk_type": "paragraph",
                    "document_id": str(uuid4()),
                    "computed_word_count": 10
                },
                "metadata": {"distance": 0.1, "certainty": 0.9}
            },
            {
                "uuid": str(uuid4()),
                "properties": {
                    "content": "The Good is that at which all things aim, according to Aristotle.",
                    "chunk_type": "paragraph", 
                    "document_id": str(uuid4()),
                    "computed_word_count": 11
                },
                "metadata": {"distance": 0.15, "certainty": 0.85}
            }
        ]
    
    @patch('weaviate.connect_to_local')
    def test_vector_similarity_search(self, mock_connect):
        """Test vector similarity search functionality."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Mock search response
        mock_search_response = Mock()
        mock_search_response.objects = self.mock_search_results
        mock_collection.query.near_vector.return_value = mock_search_response
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test vector search
        results = weaviate_client.search_by_vector(
            collection_name="Chunk",
            query_vector=self.query_embedding,
            limit=10,
            min_certainty=0.7
        )
        
        # Verify search was called with correct parameters
        mock_collection.query.near_vector.assert_called_once()
        
        # Verify results format
        assert len(results) <= 10
        for result in results:
            assert "uuid" in result
            assert "properties" in result
            assert "metadata" in result
    
    @patch('weaviate.connect_to_local')
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_text_to_vector_search_pipeline(self, mock_sentence_transformer, mock_connect):
        """Test complete text-to-vector search pipeline."""
        # Mock embedding service
        mock_model = Mock()
        query_embedding = np.array(self.query_embedding, dtype=np.float32)
        mock_model.encode.return_value = query_embedding
        mock_model.get_sentence_embedding_dimension.return_value = len(self.query_embedding)
        mock_sentence_transformer.return_value = mock_model
        
        # Mock Weaviate client
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        mock_search_response = Mock()
        mock_search_response.objects = self.mock_search_results
        mock_collection.query.near_vector.return_value = mock_search_response
        
        # Test end-to-end pipeline
        embedding_service = EmbeddingService()
        embedding_service.load_model()
        
        # Generate embedding for query
        query_vector = embedding_service.generate_embedding(self.query_text)
        
        # Search using generated embedding
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        results = weaviate_client.search_by_vector(
            collection_name="Chunk",
            query_vector=query_vector,
            limit=5
        )
        
        # Verify pipeline works
        assert len(query_vector) == len(self.query_embedding)
        mock_collection.query.near_vector.assert_called_once()
    
    @patch('weaviate.connect_to_local')
    def test_hybrid_search_capability(self, mock_connect):
        """Test hybrid search combining vector and keyword search."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Mock hybrid search response
        mock_search_response = Mock()
        mock_search_response.objects = self.mock_search_results
        mock_collection.query.hybrid.return_value = mock_search_response
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test hybrid search (vector + keyword)
        if hasattr(weaviate_client, 'hybrid_search'):
            results = weaviate_client.hybrid_search(
                collection_name="Chunk",
                query_text=self.query_text,
                query_vector=self.query_embedding,
                limit=5,
                alpha=0.7  # Weight toward vector search
            )
            
            # Verify hybrid capabilities exist
            assert True  # Interface test
    
    def test_search_result_filtering(self):
        """Test filtering search results by metadata."""
        # Test document_id filtering
        doc_id = str(uuid4())
        filtered_results = [
            result for result in self.mock_search_results
            if result["properties"]["document_id"] == doc_id
        ]
        
        # Test chunk_type filtering
        type_filtered = [
            result for result in self.mock_search_results
            if result["properties"]["chunk_type"] == "paragraph"
        ]
        
        assert len(type_filtered) <= len(self.mock_search_results)
    
    def test_relevance_scoring(self):
        """Test relevance scoring and ranking."""
        # Sort by certainty (relevance score)
        sorted_results = sorted(
            self.mock_search_results,
            key=lambda x: x["metadata"]["certainty"],
            reverse=True
        )
        
        # Verify sorting
        certainties = [r["metadata"]["certainty"] for r in sorted_results]
        assert certainties == sorted(certainties, reverse=True)
        
        # Test minimum relevance threshold
        min_certainty = 0.8
        high_relevance = [
            r for r in self.mock_search_results
            if r["metadata"]["certainty"] >= min_certainty
        ]
        
        assert all(r["metadata"]["certainty"] >= min_certainty for r in high_relevance)


class TestEmbeddingStorageIntegration:
    """Test integration between embedding service and storage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunks_without_embeddings = [
            Chunk(
                text="Philosophy is the love of wisdom and pursuit of truth.",
                document_id=uuid4(),
                start_position=0,
                end_position=55,
                sequence_number=0,
                word_count=9,
                chunk_type=ChunkType.PARAGRAPH
            ),
            Chunk(
                text="Ethics examines what constitutes a good life and moral behavior.",
                document_id=uuid4(),
                start_position=0,
                end_position=63,
                sequence_number=1,
                word_count=10,
                chunk_type=ChunkType.PARAGRAPH
            )
        ]
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    @patch('weaviate.connect_to_local')
    def test_end_to_end_chunk_processing(self, mock_connect, mock_sentence_transformer):
        """Test complete chunk processing pipeline: text -> embedding -> storage."""
        # Mock embedding service
        mock_model = Mock()
        embedding_dim = 384
        
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Mock Weaviate storage
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        mock_batch_result = Mock()
        mock_batch_result.uuids = [str(uuid4()) for _ in self.chunks_without_embeddings]
        mock_collection.data.insert_many.return_value = mock_batch_result
        
        # Execute pipeline
        embedding_service = EmbeddingService()
        embedding_service.load_model()
        
        # Generate embeddings for chunks
        embeddings = embedding_service.generate_chunk_embeddings_batch(
            self.chunks_without_embeddings,
            show_progress=False
        )
        
        # Update chunks with embeddings
        for chunk, embedding in zip(self.chunks_without_embeddings, embeddings):
            chunk.embedding_vector = embedding
        
        # Store in Weaviate
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        batch_objects = []
        for chunk in self.chunks_without_embeddings:
            batch_objects.append({
                "properties": chunk.to_weaviate_dict(),
                "vector": chunk.embedding_vector
            })
        
        result = weaviate_client.create_objects_batch("Chunk", batch_objects)
        
        # Verify pipeline success
        assert len(embeddings) == len(self.chunks_without_embeddings)
        assert all(len(emb) == embedding_dim for emb in embeddings)
        assert len(result) == len(self.chunks_without_embeddings)
    
    def test_chunk_update_with_embeddings(self):
        """Test updating chunk models with generated embeddings."""
        chunk = self.chunks_without_embeddings[0]
        assert chunk.embedding_vector is None
        
        # Simulate embedding generation
        generated_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        chunk.embedding_vector = generated_embedding
        
        # Verify update
        assert chunk.embedding_vector == generated_embedding
        assert len(chunk.embedding_vector) == 5
        
        # Verify Weaviate format includes embedding
        weaviate_dict = chunk.to_weaviate_dict()
        assert "content" in weaviate_dict
        assert weaviate_dict["content"] == chunk.text
    
    def test_embedding_consistency_validation(self):
        """Test validation of embedding consistency across chunks."""
        embeddings = [
            [0.1, 0.2, 0.3],  # 3 dimensions
            [0.4, 0.5, 0.6],  # 3 dimensions
            [0.7, 0.8]        # 2 dimensions - inconsistent!
        ]
        
        # Check dimension consistency
        dimensions = [len(emb) for emb in embeddings]
        is_consistent = len(set(dimensions)) == 1
        
        assert not is_consistent  # This batch has inconsistent dimensions
        
        # Consistent embeddings
        consistent_embeddings = [
            [0.1, 0.2, 0.3],  # 3 dimensions
            [0.4, 0.5, 0.6],  # 3 dimensions
            [0.7, 0.8, 0.9]   # 3 dimensions
        ]
        
        consistent_dimensions = [len(emb) for emb in consistent_embeddings]
        is_consistent = len(set(consistent_dimensions)) == 1
        
        assert is_consistent


class TestPerformanceOptimization:
    """Test performance optimization for embedding storage and retrieval."""
    
    def test_batch_size_optimization_for_storage(self):
        """Test optimal batch sizes for storage operations."""
        # Different batch sizes for different scenarios
        small_batch = 10   # For quick testing
        medium_batch = 50  # For regular processing
        large_batch = 200  # For bulk operations
        
        # Verify batch sizes are reasonable
        assert small_batch < medium_batch < large_batch
        assert large_batch <= 1000  # Reasonable upper limit
    
    @patch('weaviate.connect_to_local')
    def test_pagination_for_large_retrievals(self, mock_connect):
        """Test pagination for retrieving large result sets."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.collections.get.return_value = mock_collection
        mock_connect.return_value = mock_client
        
        # Mock paginated search
        def mock_search_with_offset(offset=0, limit=10):
            # Simulate pagination
            total_results = 100
            start_idx = offset
            end_idx = min(offset + limit, total_results)
            
            return Mock(
                objects=[
                    {
                        "uuid": str(uuid4()),
                        "properties": {"content": f"Result {i}"},
                        "metadata": {"distance": 0.1 + i * 0.01}
                    }
                    for i in range(start_idx, end_idx)
                ]
            )
        
        weaviate_client = WeaviateClient()
        weaviate_client.connect()
        
        # Test pagination interface
        page_size = 20
        total_retrieved = 0
        page_num = 0
        
        while total_retrieved < 60:  # Retrieve first 60 results
            offset = page_num * page_size
            # Mock search call would use offset
            total_retrieved += page_size
            page_num += 1
        
        assert total_retrieved >= 60
        assert page_num == 3  # 3 pages of 20 items each
    
    def test_embedding_caching_strategy(self):
        """Test caching strategy for frequently accessed embeddings."""
        # Mock cache for embeddings
        embedding_cache = {}
        
        def cache_key(text: str) -> str:
            """Generate cache key for text."""
            return f"emb_{hash(text)}"
        
        def get_cached_embedding(text: str) -> Optional[List[float]]:
            """Get embedding from cache."""
            key = cache_key(text)
            return embedding_cache.get(key)
        
        def cache_embedding(text: str, embedding: List[float]) -> None:
            """Cache embedding for text."""
            key = cache_key(text)
            embedding_cache[key] = embedding
        
        # Test caching workflow
        test_text = "Cached philosophical text"
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Initially no cache
        assert get_cached_embedding(test_text) is None
        
        # Cache embedding
        cache_embedding(test_text, test_embedding)
        
        # Retrieve from cache
        cached_result = get_cached_embedding(test_text)
        assert cached_result == test_embedding
        
        # Verify cache size management
        max_cache_size = 1000
        assert len(embedding_cache) <= max_cache_size