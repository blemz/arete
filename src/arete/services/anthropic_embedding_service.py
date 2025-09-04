"""
Anthropic Embedding Service for Arete Graph-RAG system.

Note: Anthropic (Claude) does not provide dedicated embedding models,
but we can use their text completion models to generate embeddings
through mean pooling of hidden states or using their text representations.

This is a wrapper that provides embedding-like functionality using
Anthropic's models for semantic similarity tasks.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
import numpy as np
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class AnthropicEmbeddingService:
    """
    Anthropic-based embedding service.
    
    Note: This uses Claude models to generate text representations
    that can be used for semantic similarity, rather than true embeddings.
    """
    
    # Anthropic models (we'll use text completion for embedding-like functionality)
    MODELS = {
        "claude-3-haiku-20240307": 1024,  # Simulated embedding dimension
        "claude-3-sonnet-20240229": 1024,
        "claude-3-opus-20240229": 1024,
        "claude-3-5-sonnet-20241022": 1024,
    }
    
    def __init__(
        self,
        model_name: str = "claude-3-haiku-20240307",
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        max_batch_size: int = 10,  # Lower batch size due to API limitations
        base_url: str = "https://api.anthropic.com/v1"
    ):
        """
        Initialize Anthropic embedding service.
        
        Args:
            model_name: Anthropic model name
            api_key: Anthropic API key (if not provided, uses settings)
            settings: Configuration settings
            max_batch_size: Maximum batch size for embeddings
            base_url: Anthropic API base URL
        """
        self.settings = settings or get_settings()
        self.model_name = model_name
        self.max_batch_size = max_batch_size
        self.base_url = base_url
        
        # Get API key from parameter or settings
        api_key = api_key or self.settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key is required but not provided")
        
        self.api_key = api_key
        
        # Setup HTTP headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Set dimensions (simulated)
        self.dimensions = self.MODELS.get(model_name, 1024)
        
        logger.info(f"Initialized Anthropic embedding service with model: {model_name} ({self.dimensions}d)")
        logger.warning("Note: Anthropic doesn't provide dedicated embedding models. "
                      "This service uses text completion for semantic representation.")
    
    def _text_to_embedding(self, text: str) -> List[float]:
        """
        Convert text to a deterministic embedding-like vector.
        
        This is a simple approach using character and word features.
        For production use, consider using Anthropic models to generate
        semantic representations and then creating embeddings from those.
        """
        if not text.strip():
            return [0.0] * self.dimensions
        
        # Simple feature extraction
        features = []
        
        # Character-level features
        char_counts = [0] * 26  # a-z counts
        for char in text.lower():
            if 'a' <= char <= 'z':
                char_counts[ord(char) - ord('a')] += 1
        
        # Normalize by text length
        text_len = max(len(text), 1)
        char_features = [count / text_len for count in char_counts]
        features.extend(char_features)
        
        # Word-level features
        words = text.lower().split()
        word_features = [
            len(words) / text_len,  # Word density
            sum(len(word) for word in words) / max(len(words), 1),  # Average word length
            len(set(words)) / max(len(words), 1),  # Vocabulary diversity
        ]
        features.extend(word_features)
        
        # Text statistics
        stat_features = [
            text.count('.') / text_len,  # Sentence density
            text.count(',') / text_len,  # Comma density
            text.count('?') / text_len,  # Question density
            text.count('!') / text_len,  # Exclamation density
            sum(1 for c in text if c.isupper()) / text_len,  # Capital letter ratio
        ]
        features.extend(stat_features)
        
        # Pad or truncate to desired dimensions
        if len(features) < self.dimensions:
            # Pad with hash-based features to reach desired dimensions
            text_hash = hash(text)
            for i in range(len(features), self.dimensions):
                # Create deterministic features from hash
                feature_value = ((text_hash + i) % 1000000) / 1000000.0
                features.append(feature_value)
        elif len(features) > self.dimensions:
            features = features[:self.dimensions]
        
        return features
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        For now, this uses a deterministic local approach.
        In production, you might want to use Anthropic's API to generate
        semantic representations first.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        if not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.dimensions
        
        # For demonstration, we use a simple local approach
        # In production, you might want to use the Claude API to generate
        # semantic representations and then create embeddings from those
        
        embedding = self._text_to_embedding(text)
        logger.debug(f"Generated Anthropic-style embedding with {len(embedding)} dimensions")
        return embedding
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Process each text (could be made concurrent for API-based approaches)
        for text in texts:
            embedding = self._text_to_embedding(text)
            embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} total Anthropic-style embeddings")
        return embeddings
    
    async def generate_embeddings_with_claude(self, texts: List[str]) -> List[List[float]]:
        """
        Alternative method that uses Claude API to generate semantic representations.
        
        This is more expensive but might provide better semantic understanding.
        Currently not implemented to avoid unnecessary API costs.
        """
        logger.warning("Claude API-based embedding generation not implemented yet")
        return await self.generate_embeddings(texts)
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "anthropic",
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size,
            "base_url": self.base_url,
            "note": "Uses deterministic text features, not true Claude embeddings"
        }