"""
Embedding Service for Arete Graph-RAG system.

Provides high-performance embedding generation using sentence-transformers
with GPU support, batch processing, and integration with existing components.
"""

import logging
from typing import List, Optional, Union, Dict, Any, Callable
from functools import lru_cache
import numpy as np
from uuid import UUID
import hashlib

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from ..config import Settings, get_settings
from ..models.chunk import Chunk


logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Base exception for embedding service errors."""
    pass


class ModelNotLoadedError(EmbeddingServiceError):
    """Raised when attempting to use embedding service without loaded model."""
    pass


class BatchProcessingError(EmbeddingServiceError):
    """Raised when batch processing fails."""
    pass


class EmbeddingService:
    """
    High-performance embedding generation service.
    
    Features:
    - Configurable sentence-transformer models
    - GPU support with automatic fallback to CPU
    - Efficient batch processing with memory management
    - Integration with Arete Chunk model
    - L2 normalization for cosine similarity
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of sentence-transformer model to use
            device: Device to use ('cuda', 'cpu', or 'auto')
            settings: Configuration settings
        """
        self.settings = settings or get_settings()
        
        # Model configuration
        self.model_name = model_name or self._get_default_model()
        self.device = device or self._get_device_from_settings()
        self.model: Optional[SentenceTransformer] = None
        
        # Performance tracking
        self._embedding_count = 0
        self._batch_count = 0
        
        # Simple embedding cache (text hash -> embedding)
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_hits = 0
        
        logger.info(f"Initialized EmbeddingService with model={self.model_name}, device={self.device}")
    
    def _get_default_model(self) -> str:
        """Get default embedding model from settings."""
        # Use model from settings/environment variable
        return self.settings.embedding_model
    
    def _get_device_from_settings(self) -> str:
        """Get device from settings, with auto-detection fallback."""
        if self.settings.embedding_device == "auto":
            return self._detect_device()
        else:
            return self.settings.embedding_device
    
    def _detect_device(self) -> str:
        """Detect optimal device for embedding generation."""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, using CPU")
            return 'cpu'
        
        if torch.cuda.is_available():
            logger.info("CUDA available, using GPU for embeddings")
            return 'cuda'
        
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS available, using Apple Silicon GPU")
            return 'mps'
        
        logger.info("No GPU available, using CPU for embeddings")
        return 'cpu'
    
    def load_model(self) -> None:
        """Load the sentence-transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise EmbeddingServiceError(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Enable memory efficient attention if available
            if hasattr(self.model, 'enable_memory_efficient_attention'):
                self.model.enable_memory_efficient_attention()
            
            logger.info(f"Model loaded successfully. Dimension: {self.get_embedding_dimension()}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise EmbeddingServiceError(f"Failed to load model: {e}") from e
    
    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self.model is not None:
            logger.info("Unloading embedding model")
            del self.model
            self.model = None
            
            # Clear embedding cache
            self.clear_cache()
            
            # Clear GPU cache if using CUDA
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        cache_hit_rate = self._cache_hits / max(self._embedding_count, 1) if self._embedding_count > 0 else 0.0
        return {
            'model_name': self.model_name,
            'device': self.device,
            'is_loaded': self.is_model_loaded(),
            'embedding_dimension': self.get_embedding_dimension() if self.is_model_loaded() else None,
            'embeddings_generated': self._embedding_count,
            'batches_processed': self._batch_count,
            'cache_size': len(self._embedding_cache),
            'cache_hits': self._cache_hits,
            'cache_hit_rate': cache_hit_rate
        }
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Get the dimension of embeddings produced by current model."""
        if not self.is_model_loaded():
            return None
        
        # Get dimension from model configuration
        return self.model.get_sentence_embedding_dimension()
    
    def generate_embedding(
        self, 
        text: str,
        normalize: bool = True,
        show_progress: bool = False
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            normalize: Whether to L2 normalize the embedding
            show_progress: Whether to show progress for single embedding
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            ModelNotLoadedError: If model is not loaded
            EmbeddingServiceError: If embedding generation fails
        """
        if not self.is_model_loaded():
            raise ModelNotLoadedError("Model not loaded. Call load_model() first.")
        
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            # Return zero vector of appropriate dimension
            dim = self.get_embedding_dimension()
            return [0.0] * dim if dim else []
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Check cache first
            cache_key = self._get_cache_key(processed_text, normalize)
            if cache_key in self._embedding_cache:
                self._cache_hits += 1
                self._embedding_count += 1
                logger.debug(f"Cache hit for text: {processed_text[:50]}...")
                return self._embedding_cache[cache_key]
            
            # Generate embedding
            embedding = self.model.encode(
                processed_text,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_tensor=False  # Return numpy array
            )
            
            self._embedding_count += 1
            
            # Convert to list for JSON serialization
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
            
            # Cache the result
            self._embedding_cache[cache_key] = embedding_list
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingServiceError(f"Embedding generation failed: {e}") from e
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        normalize: bool = True,
        show_progress: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts to embed
            batch_size: Batch size for processing (auto-calculated if None)
            normalize: Whether to L2 normalize embeddings
            show_progress: Whether to show progress bar
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of embedding vectors
            
        Raises:
            ModelNotLoadedError: If model is not loaded
            BatchProcessingError: If batch processing fails
        """
        if not self.is_model_loaded():
            raise ModelNotLoadedError("Model not loaded. Call load_model() first.")
        
        if not texts:
            return []
        
        # Auto-calculate batch size if not provided
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(len(texts))
        
        try:
            # Preprocess all texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(processed_texts), batch_size):
                batch_texts = processed_texts[i:i + batch_size]
                
                # Generate embeddings for batch
                batch_embeddings = self.model.encode(
                    batch_texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=False,  # We handle progress ourselves
                    convert_to_tensor=False
                )
                
                # Convert to list format
                if len(batch_texts) == 1:
                    # Handle single item case
                    batch_embeddings = [batch_embeddings]
                
                embeddings_list = [
                    emb.tolist() if hasattr(emb, 'tolist') else emb 
                    for emb in batch_embeddings
                ]
                all_embeddings.extend(embeddings_list)
                
                # Update progress
                if progress_callback:
                    progress_callback(min(i + batch_size, len(texts)), len(texts))
                
                self._batch_count += 1
            
            self._embedding_count += len(texts)
            
            if show_progress:
                logger.info(f"Generated {len(all_embeddings)} embeddings in {self._batch_count} batches")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise BatchProcessingError(f"Batch processing failed: {e}") from e
    
    def generate_chunk_embedding(
        self,
        chunk: Chunk,
        normalize: bool = True,
        use_vectorizable_text: bool = True
    ) -> List[float]:
        """
        Generate embedding for a Chunk model.
        
        Args:
            chunk: Chunk model to embed
            normalize: Whether to L2 normalize the embedding
            use_vectorizable_text: Whether to use vectorizable_text field
            
        Returns:
            Embedding vector as list of floats
        """
        # Use vectorizable_text if available and requested
        if use_vectorizable_text:
            text = chunk.get_vectorizable_text()
        else:
            text = chunk.text
        
        return self.generate_embedding(text, normalize=normalize)
    
    def generate_chunk_embeddings_batch(
        self,
        chunks: List[Chunk],
        batch_size: Optional[int] = None,
        normalize: bool = True,
        use_vectorizable_text: bool = True,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple Chunk models.
        
        Args:
            chunks: List of Chunk models to embed
            batch_size: Batch size for processing
            normalize: Whether to L2 normalize embeddings
            use_vectorizable_text: Whether to use vectorizable_text fields
            show_progress: Whether to show progress
            
        Returns:
            List of embedding vectors
        """
        # Extract texts from chunks
        texts = []
        for chunk in chunks:
            if use_vectorizable_text:
                texts.append(chunk.get_vectorizable_text())
            else:
                texts.append(chunk.text)
        
        return self.generate_embeddings_batch(
            texts,
            batch_size=batch_size,
            normalize=normalize,
            show_progress=show_progress
        )
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for optimal embedding generation.
        
        Handles multilingual text including Greek, Sanskrit, Latin, and modern languages
        with proper Unicode normalization and classical text considerations.
        
        Args:
            text: Raw input text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Unicode normalization for classical texts (Greek, Sanskrit, etc.)
        import unicodedata
        processed = unicodedata.normalize('NFKC', text)
        
        # Basic preprocessing
        processed = processed.strip()
        
        # Remove excessive whitespace while preserving text structure
        processed = " ".join(processed.split())
        
        # Language-aware length limits
        max_length = self._get_max_length_for_text(processed)
        if len(processed) > max_length:
            # Smart truncation at word/character boundaries
            processed = self._smart_truncate(processed, max_length)
            logger.debug(f"Truncated text to {len(processed)} characters")
        
        return processed
    
    def _get_max_length_for_text(self, text: str) -> int:
        """
        Get maximum length based on text characteristics.
        
        Different scripts and languages may need different limits for optimal embedding.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Maximum character length for the text
        """
        # Detect script types
        has_greek = any(0x0370 <= ord(c) <= 0x03FF for c in text)
        has_sanskrit = any(0x0900 <= ord(c) <= 0x097F for c in text)
        has_complex_scripts = has_greek or has_sanskrit
        
        if has_complex_scripts:
            # Classical scripts may need more conservative limits
            return 6000
        else:
            # Standard limit for Latin scripts
            return 8000
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Intelligently truncate text at appropriate boundaries.
        
        Args:
            text: Text to truncate
            max_length: Maximum allowed length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Try to cut at sentence boundary first
        for delimiter in ['. ', '。', '॥', '·']:  # Various sentence delimiters
            sentences = text[:max_length].split(delimiter)
            if len(sentences) > 1:
                # Keep all but the last incomplete sentence
                truncated = delimiter.join(sentences[:-1]) + delimiter
                if truncated.strip():
                    return truncated.strip()
        
        # Fall back to word boundary
        words = text[:max_length].split()
        if len(words) > 1:
            return ' '.join(words[:-1])
        
        # Last resort: character boundary
        return text[:max_length]
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of languages supported by current model.
        
        Returns:
            List of language codes supported
        """
        # Multilingual models typically support these languages
        if 'multilingual' in self.model_name.lower():
            return [
                'en',  # English
                'el',  # Greek (modern and ancient)
                'hi',  # Hindi/Sanskrit
                'la',  # Latin
                'de',  # German
                'fr',  # French
                'es',  # Spanish
                'it',  # Italian
                'zh',  # Chinese
                'ja',  # Japanese
                'ar',  # Arabic
                'he',  # Hebrew
            ]
        else:
            # Monolingual model
            return ['en']
    
    def detect_text_language(self, text: str) -> str:
        """
        Detect the primary language of input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code (ISO 639-1)
        """
        # Simple script-based detection for classical languages
        if any(0x0370 <= ord(c) <= 0x03FF for c in text):
            return 'el'  # Greek
        elif any(0x0900 <= ord(c) <= 0x097F for c in text):
            return 'hi'  # Sanskrit/Hindi (Devanagari)
        elif any(0x0590 <= ord(c) <= 0x05FF for c in text):
            return 'he'  # Hebrew
        elif any(0x0600 <= ord(c) <= 0x06FF for c in text):
            return 'ar'  # Arabic
        else:
            # Default to English for Latin script
            return 'en'
    
    def is_multilingual_model(self) -> bool:
        """Check if current model supports multiple languages."""
        return 'multilingual' in self.model_name.lower()
    
    def _get_cache_key(self, text: str, normalize: bool) -> str:
        """
        Generate cache key for text and parameters.
        
        Args:
            text: Processed text
            normalize: Whether embeddings are normalized
            
        Returns:
            Cache key string
        """
        # Include model name, text, and normalization in cache key
        key_data = f"{self.model_name}:{text}:{normalize}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        cache_size = len(self._embedding_cache)
        self._embedding_cache.clear()
        logger.info(f"Cleared embedding cache ({cache_size} entries)")
    
    def _calculate_optimal_batch_size(self, total_items: int) -> int:
        """
        Calculate optimal batch size based on available memory and model.
        
        Args:
            total_items: Total number of items to process
            
        Returns:
            Optimal batch size
        """
        # Base batch size from settings
        base_batch_size = self.settings.embedding_batch_size
        
        # Adjust based on device
        if self.device == 'cuda':
            # GPU can handle larger batches
            optimal_size = min(base_batch_size * 2, 64)
        elif self.device == 'mps':
            # Apple Silicon GPU - moderate batch size
            optimal_size = min(base_batch_size, 32)
        else:
            # CPU - smaller batches
            optimal_size = min(base_batch_size // 2, 16)
        
        # Don't exceed total items
        return min(optimal_size, total_items)


# Singleton pattern for model caching
_embedding_service_instance: Optional[EmbeddingService] = None


@lru_cache(maxsize=1)
def get_embedding_service(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    settings: Optional[Settings] = None
) -> EmbeddingService:
    """
    Get cached embedding service instance.
    
    Args:
        model_name: Name of sentence-transformer model
        device: Device to use for embeddings
        settings: Configuration settings
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService(
            model_name=model_name,
            device=device,
            settings=settings
        )
    
    return _embedding_service_instance


def clear_embedding_service_cache() -> None:
    """Clear cached embedding service instance."""
    global _embedding_service_instance
    
    if _embedding_service_instance is not None:
        _embedding_service_instance.unload_model()
        _embedding_service_instance = None
    
    # Clear lru_cache
    get_embedding_service.cache_clear()