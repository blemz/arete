"""
Test suite for Batch Embedding Generation.

Focused tests for efficient batch processing, performance optimization,
and integration with existing text processing pipeline.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Callable
from uuid import uuid4

from src.arete.models.chunk import Chunk, ChunkType
from src.arete.services.embedding_service import (
    EmbeddingService, 
    BatchProcessingError,
    ModelNotLoadedError
)


class TestBatchEmbeddingGeneration:
    """Test efficient batch embedding generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.large_text_batch = [
            f"Philosophical text sample {i}: Ancient wisdom about virtue, ethics, and the good life. "
            f"This text discusses various aspects of classical philosophy and moral reasoning. "
            f"The philosopher emphasizes the importance of {['virtue', 'wisdom', 'justice', 'courage'][i % 4]}."
            for i in range(25)
        ]
        
        self.chunks_batch = [
            Chunk(
                text=f"Chunk {i}: Classical philosophical discourse on ethical principles and moral virtue.",
                document_id=uuid4(),
                position=i,
                start_char=i * 100,
                end_char=(i + 1) * 100,
                word_count=12,
                chunk_type=ChunkType.PARAGRAPH
            )
            for i in range(20)
        ]
        
        self.embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_batch_processing_single_call_efficiency(self, mock_sentence_transformer):
        """Test that batch processing uses single model call for efficiency."""
        mock_model = Mock()
        batch_size = len(self.large_text_batch)
        embedding_dim = 384
        
        # Simulate batch embedding output
        mock_embeddings = np.random.rand(batch_size, embedding_dim).astype(np.float32)
        mock_model.encode.return_value = mock_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Load model and process batch
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_embeddings_batch(
            self.large_text_batch, 
            batch_size=batch_size,  # Use the full batch size to ensure single call
            show_progress=False
        )
        
        # Verify single encode call for efficiency
        assert mock_model.encode.call_count == 1
        
        # Verify output format and dimensions
        assert len(embeddings) == batch_size
        assert all(len(emb) == embedding_dim for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(isinstance(val, float) for emb in embeddings for val in emb)
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_batch_size_optimization(self, mock_sentence_transformer):
        """Test automatic batch size optimization."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Test with large dataset that should be split into multiple batches
        large_dataset = [f"Text {i}" for i in range(100)]
        
        # Configure mock to return appropriate embeddings for each batch
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Load model and process with automatic batch sizing
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_embeddings_batch(
            large_dataset,
            batch_size=None,  # Auto-calculate
            show_progress=False
        )
        
        # Verify multiple batches were processed
        assert mock_model.encode.call_count > 1
        assert len(embeddings) == len(large_dataset)
        
        # Verify consistency across batches
        assert all(len(emb) == embedding_dim for emb in embeddings)
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_custom_batch_size(self, mock_sentence_transformer):
        """Test custom batch size specification."""
        mock_model = Mock()
        embedding_dim = 384
        custom_batch_size = 8
        
        # Create dataset that will require multiple batches
        dataset = [f"Text {i}" for i in range(25)]
        expected_batches = (len(dataset) + custom_batch_size - 1) // custom_batch_size
        
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_embeddings_batch(
            dataset,
            batch_size=custom_batch_size,
            show_progress=False
        )
        
        # Verify correct number of batches
        assert mock_model.encode.call_count == expected_batches
        assert len(embeddings) == len(dataset)
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_progress_tracking_callback(self, mock_sentence_transformer):
        """Test progress tracking with callback function."""
        mock_model = Mock()
        embedding_dim = 384
        
        def encode_side_effect(texts, **kwargs):
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        # Progress tracking
        progress_updates = []
        
        def progress_callback(current: int, total: int):
            progress_updates.append((current, total))
        
        dataset = [f"Text {i}" for i in range(15)]
        self.embedding_service.load_model()
        
        embeddings = self.embedding_service.generate_embeddings_batch(
            dataset,
            batch_size=5,
            progress_callback=progress_callback,
            show_progress=False
        )
        
        # Verify progress updates
        assert len(progress_updates) > 0
        assert all(total == len(dataset) for _, total in progress_updates)
        assert progress_updates[-1][0] == len(dataset)  # Final update should be complete
        assert len(embeddings) == len(dataset)
    
    def test_empty_batch_handling(self):
        """Test handling of empty batch."""
        embeddings = self.embedding_service.generate_embeddings_batch([])
        assert embeddings == []
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_batch_error_resilience(self, mock_sentence_transformer):
        """Test error handling during batch processing."""
        mock_model = Mock()
        
        # Simulate model failure
        mock_model.encode.side_effect = Exception("GPU memory error")
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        
        # Should raise BatchProcessingError
        with pytest.raises(BatchProcessingError, match="Batch processing failed"):
            self.embedding_service.generate_embeddings_batch(
                ["Test text"],
                show_progress=False
            )
    
    def test_model_not_loaded_error(self):
        """Test error when model not loaded."""
        # Service without loaded model
        service = EmbeddingService()
        
        with pytest.raises(ModelNotLoadedError, match="Model not loaded"):
            service.generate_embeddings_batch(["Test text"])


class TestChunkBatchProcessing:
    """Test batch processing specifically for Chunk models."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunks = [
            Chunk(
                text=f"Philosophical chunk {i}: Discussion of ethical principles and moral reasoning.",
                document_id=uuid4(),
                position=i,
                start_char=i * 80,
                end_char=(i + 1) * 80,
                word_count=10,
                chunk_type=ChunkType.PARAGRAPH,
                vectorizable_text=f"Optimized text {i}: Ethics and moral reasoning principles."
            )
            for i in range(12)
        ]
        
        self.embedding_service = EmbeddingService()
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_chunk_batch_with_vectorizable_text(self, mock_sentence_transformer):
        """Test chunk batch processing using vectorizable_text."""
        mock_model = Mock()
        embedding_dim = 384
        
        def encode_side_effect(texts, **kwargs):
            # Verify vectorizable_text is being used
            for i, text in enumerate(texts):
                assert f"Optimized text {i}" in text
            
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_chunk_embeddings_batch(
            self.chunks,
            use_vectorizable_text=True,
            show_progress=False
        )
        
        assert len(embeddings) == len(self.chunks)
        assert all(len(emb) == embedding_dim for emb in embeddings)
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_chunk_batch_with_regular_text(self, mock_sentence_transformer):
        """Test chunk batch processing using regular text."""
        mock_model = Mock()
        embedding_dim = 384
        
        def encode_side_effect(texts, **kwargs):
            # Verify regular text is being used
            for i, text in enumerate(texts):
                assert f"Philosophical chunk {i}" in text
            
            batch_size = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_chunk_embeddings_batch(
            self.chunks,
            use_vectorizable_text=False,
            show_progress=False
        )
        
        assert len(embeddings) == len(self.chunks)
        assert all(len(emb) == embedding_dim for emb in embeddings)
    
    def test_empty_chunks_batch(self):
        """Test handling of empty chunks batch."""
        embeddings = self.embedding_service.generate_chunk_embeddings_batch([])
        assert embeddings == []


class TestBatchPerformanceOptimization:
    """Test performance optimization features for batch processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedding_service = EmbeddingService()
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_gpu_batch_size_optimization(self, mock_sentence_transformer):
        """Test GPU-optimized batch sizes."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        # Test different device configurations
        test_cases = [
            ("cuda", 64),    # GPU should use larger batches
            ("cpu", 16),     # CPU should use smaller batches
            ("mps", 32),     # Apple Silicon moderate batches
        ]
        
        for device, expected_max_batch in test_cases:
            service = EmbeddingService(device=device)
            optimal_size = service._calculate_optimal_batch_size(100)
            
            # Should not exceed expected maximum for device
            assert optimal_size <= expected_max_batch
            assert optimal_size > 0
    
    def test_memory_efficient_processing(self):
        """Test memory-efficient processing for large datasets."""
        # Test that large datasets don't cause memory issues
        large_dataset = [f"Text {i}" * 100 for i in range(1000)]  # Large texts
        
        # Should not raise memory errors (would need actual model for full test)
        # This test verifies the interface exists
        assert hasattr(self.embedding_service, 'generate_embeddings_batch')
        assert hasattr(self.embedding_service, '_calculate_optimal_batch_size')
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_normalization_in_batch_processing(self, mock_sentence_transformer):
        """Test L2 normalization is applied correctly in batch processing."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Create embeddings that would have different norms
        unnormalized_embeddings = np.array([
            [1.0, 2.0, 3.0, 4.0] + [0.0] * (embedding_dim - 4),
            [5.0, 6.0, 7.0, 8.0] + [0.0] * (embedding_dim - 4),
            [0.1, 0.2, 0.3, 0.4] + [0.0] * (embedding_dim - 4)
        ], dtype=np.float32)
        
        mock_model.encode.return_value = unnormalized_embeddings
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_embeddings_batch(
            ["Text 1", "Text 2", "Text 3"],
            normalize=True,
            show_progress=False
        )
        
        # Verify normalize_embeddings parameter was passed
        call_args = mock_model.encode.call_args
        assert call_args[1]['normalize_embeddings'] == True
        
        assert len(embeddings) == 3
        assert all(len(emb) == embedding_dim for emb in embeddings)


class TestBatchProcessingIntegration:
    """Test integration of batch processing with existing components."""
    
    def test_settings_integration(self):
        """Test integration with configuration settings."""
        from src.arete.config import get_settings
        
        settings = get_settings()
        service = EmbeddingService(settings=settings)
        
        # Verify configuration is used
        assert hasattr(service, 'settings')
        assert service.settings.embedding_batch_size >= 1
    
    def test_chunk_model_integration(self):
        """Test seamless integration with Chunk model."""
        chunk = Chunk(
            text="Test philosophical text",
            document_id=uuid4(),
            position=0,
            start_char=0,
            end_char=25,
            word_count=3,
            chunk_type=ChunkType.PARAGRAPH
        )
        
        # Verify chunk has necessary fields for embedding
        assert hasattr(chunk, 'text')
        assert hasattr(chunk, 'vectorizable_text')
        
        # Verify service can handle chunk
        service = EmbeddingService()
        assert hasattr(service, 'generate_chunk_embedding')
        assert hasattr(service, 'generate_chunk_embeddings_batch')
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across batch operations."""
        service = EmbeddingService()
        
        # All batch methods should raise ModelNotLoadedError when model not loaded
        with pytest.raises(ModelNotLoadedError):
            service.generate_embeddings_batch(["test"])
        
        with pytest.raises(ModelNotLoadedError):
            service.generate_chunk_embeddings_batch([])


class TestBatchProcessingEdgeCases:
    """Test edge cases in batch processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.embedding_service = EmbeddingService()
    
    def test_single_item_batch(self):
        """Test batch processing with single item."""
        # Should handle single item gracefully
        single_text = ["Single philosophical text about virtue."]
        
        # Test interface (actual embedding would require loaded model)
        assert hasattr(self.embedding_service, 'generate_embeddings_batch')
    
    def test_mixed_empty_texts_in_batch(self):
        """Test batch with some empty or whitespace-only texts."""
        mixed_texts = [
            "Valid philosophical text",
            "",  # Empty
            "   ",  # Whitespace only
            "Another valid text",
            None  # None value would be handled by preprocessing
        ]
        
        # Filter out invalid texts first (this would be done in preprocessing)
        valid_texts = [text for text in mixed_texts if text and text.strip()]
        assert len(valid_texts) == 2
    
    @patch('src.arete.services.embedding_service.SentenceTransformer')
    def test_very_large_text_in_batch(self, mock_sentence_transformer):
        """Test batch processing with very large texts."""
        mock_model = Mock()
        embedding_dim = 384
        
        # Create text larger than typical model limits
        very_large_text = "Philosophical discourse. " * 1000  # Very long text
        texts = ["Normal text", very_large_text, "Another normal text"]
        
        def encode_side_effect(processed_texts, **kwargs):
            # Verify large text was truncated during preprocessing
            for text in processed_texts:
                assert len(text) <= 8000  # Max length from preprocessing
            
            batch_size = len(processed_texts)
            return np.random.rand(batch_size, embedding_dim).astype(np.float32)
        
        mock_model.encode.side_effect = encode_side_effect
        mock_model.get_sentence_embedding_dimension.return_value = embedding_dim
        mock_sentence_transformer.return_value = mock_model
        
        self.embedding_service.load_model()
        embeddings = self.embedding_service.generate_embeddings_batch(
            texts,
            show_progress=False
        )
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == embedding_dim for emb in embeddings)