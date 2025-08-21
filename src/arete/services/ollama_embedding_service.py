"""
Ollama Embedding Service for Arete Graph-RAG system.

Provides access to state-of-the-art embedding models via Ollama,
including dengcao/Qwen3-Embedding-8B:Q8_0 for maximum quality.
"""

import logging
import requests
from typing import List, Optional, Union, Dict, Any, Callable
import hashlib
import time

from ..config import Settings, get_settings
from ..models.chunk import Chunk

logger = logging.getLogger(__name__)


class OllamaEmbeddingError(Exception):
    """Base exception for Ollama embedding errors."""
    pass


class OllamaConnectionError(OllamaEmbeddingError):
    """Raised when cannot connect to Ollama server."""
    pass


class OllamaModelError(OllamaEmbeddingError):
    """Raised when model is not available or fails."""
    pass


class OllamaEmbeddingService:
    """
    Ollama-based embedding service for state-of-the-art models.
    
    Features:
    - Access to SOTA models like Qwen3-Embedding-8B
    - High-dimensional embeddings (8192 dims for Qwen3)
    - Batch processing support
    - Caching for performance
    - Integration with existing Chunk models
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize Ollama embedding service.
        
        Args:
            model_name: Name of Ollama model to use
            base_url: Ollama server URL
            settings: Configuration settings
        """
        self.settings = settings or get_settings()
        
        # Model configuration
        self.model_name = model_name or self._get_default_model()
        self.base_url = base_url or self.settings.ollama_base_url
        
        # Performance tracking
        self._embedding_count = 0
        self._batch_count = 0
        
        # Simple embedding cache
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_hits = 0
        
        # Model info cache
        self._model_info: Optional[Dict[str, Any]] = None
        
        logger.info(f"Initialized OllamaEmbeddingService with model={self.model_name}, url={self.base_url}")
    
    def _get_default_model(self) -> str:
        """Get default Ollama embedding model."""
        # Use Qwen3-Embedding-8B as default - SOTA performance
        return "dengcao/qwen3-embedding-8b:q8_0"
    
    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def is_model_available(self) -> bool:
        """Check if the specified model is available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            # Check exact match or partial match
            return any(self.model_name in name or name in self.model_name for name in model_names)
            
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    def pull_model_if_needed(self) -> bool:
        """Pull model if not available locally."""
        if self.is_model_available():
            return True
        
        logger.info(f"Pulling model {self.model_name} from Ollama...")
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name},
                timeout=300  # 5 minutes for model download
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if self._model_info is None:
            try:
                response = requests.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model_name},
                    timeout=10
                )
                
                if response.status_code == 200:
                    model_data = response.json()
                    
                    # Extract key information
                    self._model_info = {
                        'model_name': self.model_name,
                        'base_url': self.base_url,
                        'is_available': True,
                        'embeddings_generated': self._embedding_count,
                        'batches_processed': self._batch_count,
                        'cache_size': len(self._embedding_cache),
                        'cache_hits': self._cache_hits,
                        'cache_hit_rate': self._cache_hits / max(self._embedding_count, 1),
                        'model_size': model_data.get('size', 'unknown'),
                        'family': model_data.get('details', {}).get('family', 'unknown'),
                        'format': model_data.get('details', {}).get('format', 'unknown')
                    }
                    
                    # Try to determine embedding dimension for Qwen3
                    if 'qwen3' in self.model_name.lower():
                        self._model_info['embedding_dimension'] = 8192  # Qwen3-Embedding-8B dimension
                    else:
                        self._model_info['embedding_dimension'] = None  # Unknown
                        
                else:
                    self._model_info = {
                        'model_name': self.model_name,
                        'base_url': self.base_url,
                        'is_available': False,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                logger.error(f"Failed to get model info: {e}")
                self._model_info = {
                    'model_name': self.model_name,
                    'base_url': self.base_url,
                    'is_available': False,
                    'error': str(e)
                }
        
        return self._model_info.copy()
    
    def generate_embedding(
        self,
        text: str,
        normalize: bool = True,
        **kwargs
    ) -> List[float]:
        """
        Generate embedding for a single text using Ollama.
        
        Args:
            text: Input text to embed
            normalize: Whether to normalize the embedding (if supported)
            **kwargs: Additional parameters for the model
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            OllamaConnectionError: If cannot connect to Ollama
            OllamaModelError: If model fails or not available
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 8192  # Default dimension for Qwen3
        
        # Check cache first
        cache_key = self._get_cache_key(text, normalize)
        if cache_key in self._embedding_cache:
            self._cache_hits += 1
            self._embedding_count += 1
            logger.debug(f"Cache hit for text: {text[:50]}...")
            return self._embedding_cache[cache_key]
        
        try:
            # Make request to Ollama embeddings endpoint
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text.strip(),
                    **kwargs
                },
                timeout=60  # 1 minute timeout for embedding generation
            )
            
            if response.status_code != 200:
                raise OllamaModelError(f"Ollama returned HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            embedding = data.get("embedding")
            
            if not embedding:
                raise OllamaModelError("No embedding returned from Ollama")
            
            # Normalize if requested (basic L2 normalization)
            if normalize:
                import math
                norm = math.sqrt(sum(x*x for x in embedding))
                if norm > 0:
                    embedding = [x / norm for x in embedding]
            
            # Cache the result
            self._embedding_cache[cache_key] = embedding
            self._embedding_count += 1
            
            logger.debug(f"Generated Ollama embedding: {len(embedding)} dimensions")
            return embedding
            
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except requests.exceptions.Timeout as e:
            raise OllamaModelError(f"Ollama request timed out: {e}")
        except Exception as e:
            logger.error(f"Failed to generate Ollama embedding: {e}")
            raise OllamaModelError(f"Embedding generation failed: {e}")
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        normalize: bool = True,
        show_progress: bool = True,
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Not used for Ollama (processes one at a time)
            normalize: Whether to normalize embeddings
            show_progress: Whether to show progress
            **kwargs: Additional model parameters
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text, normalize=normalize, **kwargs)
                embeddings.append(embedding)
                
                if show_progress and (i + 1) % 5 == 0:
                    logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i}: {e}")
                # Return zero vector of appropriate dimension
                embeddings.append([0.0] * 8192)
        
        self._batch_count += 1
        
        if show_progress:
            logger.info(f"Generated {len(embeddings)} Ollama embeddings")
        
        return embeddings
    
    def generate_chunk_embedding(
        self,
        chunk: Chunk,
        use_vectorizable_text: bool = True,
        normalize: bool = True,
        **kwargs
    ) -> List[float]:
        """
        Generate embedding for a Chunk model using Ollama.
        
        Args:
            chunk: Chunk model to embed
            use_vectorizable_text: Whether to use vectorizable_text
            normalize: Whether to normalize embedding
            **kwargs: Additional model parameters
            
        Returns:
            Embedding vector as list of floats
        """
        if use_vectorizable_text:
            text = chunk.get_vectorizable_text()
        else:
            text = chunk.text
        
        return self.generate_embedding(text, normalize=normalize, **kwargs)
    
    def generate_chunk_embeddings_batch(
        self,
        chunks: List[Chunk],
        use_vectorizable_text: bool = True,
        normalize: bool = True,
        show_progress: bool = True,
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple Chunk models.
        
        Args:
            chunks: List of Chunk models to embed
            use_vectorizable_text: Whether to use vectorizable_text
            normalize: Whether to normalize embeddings
            show_progress: Whether to show progress
            **kwargs: Additional model parameters
            
        Returns:
            List of embedding vectors
        """
        texts = []
        for chunk in chunks:
            if use_vectorizable_text:
                texts.append(chunk.get_vectorizable_text())
            else:
                texts.append(chunk.text)
        
        return self.generate_embeddings_batch(
            texts,
            normalize=normalize,
            show_progress=show_progress,
            **kwargs
        )
    
    def _get_cache_key(self, text: str, normalize: bool) -> str:
        """Generate cache key for text and parameters."""
        key_data = f"{self.model_name}:{text}:{normalize}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        cache_size = len(self._embedding_cache)
        self._embedding_cache.clear()
        logger.info(f"Cleared Ollama embedding cache ({cache_size} entries)")


# Factory function for easy integration
def create_ollama_embedding_service(
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    settings: Optional[Settings] = None
) -> OllamaEmbeddingService:
    """
    Create Ollama embedding service with dependency injection.
    
    Args:
        model_name: Ollama model name
        base_url: Ollama server URL
        settings: Configuration settings
        
    Returns:
        Configured OllamaEmbeddingService instance
    """
    return OllamaEmbeddingService(
        model_name=model_name,
        base_url=base_url,
        settings=settings
    )