"""
Duplicate Detection and Deduplication Service for Arete Graph-RAG System.

Provides comprehensive duplicate detection capabilities including:
- Exact match detection for identical content
- Semantic similarity-based duplicate detection
- Fuzzy string matching for near-duplicates  
- Cross-collection duplicate detection
- Batch processing for large datasets
- Multiple deduplication strategies
- Performance monitoring and optimization

Designed specifically for philosophical texts with domain-aware similarity measures.
"""

import asyncio
import logging
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass
import statistics

from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np

# Text processing and similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib

# Optional dependencies for advanced similarity
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False

from arete.config import Settings, get_settings
from arete.models.base import BaseModel as AreteBaseModel
from arete.models.document import Document
from arete.models.chunk import Chunk
from arete.models.citation import Citation

logger = logging.getLogger(__name__)


class DuplicationStrategy(str, Enum):
    """Strategies for duplicate detection."""
    EXACT_MATCH = "exact_match"
    HASH_COMPARISON = "hash_comparison"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    FUZZY_MATCHING = "fuzzy_matching"
    JACCARD_SIMILARITY = "jaccard_similarity"
    COSINE_SIMILARITY = "cosine_similarity"


class KeepStrategy(str, Enum):
    """Strategies for selecting items to keep during deduplication."""
    KEEP_FIRST = "keep_first"
    KEEP_LAST = "keep_last"
    HIGHEST_QUALITY = "highest_quality"
    MOST_COMPLETE = "most_complete"
    MOST_RECENT = "most_recent"


class SimilarityMetrics(BaseModel):
    """Comprehensive similarity metrics between two items."""
    
    jaccard_similarity: float = Field(..., ge=0.0, le=1.0, description="Jaccard similarity coefficient")
    cosine_similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    levenshtein_similarity: float = Field(..., ge=0.0, le=1.0, description="Normalized Levenshtein similarity")
    semantic_similarity: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    
    # Metadata
    calculation_method: str = Field(default="combined", description="Method used for calculation")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in similarity assessment")
    
    def calculate_overall_similarity(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted overall similarity score."""
        if weights is None:
            # Default weights favoring semantic and cosine similarity
            weights = {
                'jaccard': 0.2,
                'cosine': 0.3,
                'levenshtein': 0.2,
                'semantic': 0.3
            }
        
        weighted_sum = (
            self.jaccard_similarity * weights.get('jaccard', 0.25) +
            self.cosine_similarity * weights.get('cosine', 0.25) +
            self.levenshtein_similarity * weights.get('levenshtein', 0.25) +
            self.semantic_similarity * weights.get('semantic', 0.25)
        )
        
        return round(weighted_sum, 3)


class DuplicateResult(AreteBaseModel):
    """Result of duplicate detection for a group of items."""
    
    group_id: str = Field(..., description="Unique identifier for duplicate group")
    items: List[Any] = Field(..., description="Items identified as duplicates")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score for the group")
    detection_method: str = Field(..., description="Method used to detect duplicates")
    
    # Detailed similarity metrics
    similarity_metrics: Optional[SimilarityMetrics] = Field(None, description="Detailed similarity metrics")
    
    # Detection metadata
    detection_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: Optional[float] = Field(None, description="Time taken for detection in milliseconds")
    
    # Quality indicators
    confidence_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in duplicate detection")
    false_positive_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated risk of false positive")


class DeduplicationResult(BaseModel):
    """Result of deduplication process."""
    
    kept_items: List[Any] = Field(..., description="Items kept after deduplication")
    removed_items: List[Any] = Field(..., description="Items removed during deduplication")
    
    # Deduplication statistics
    original_count: int = Field(..., description="Original number of items")
    final_count: int = Field(..., description="Final number of items after deduplication")
    removal_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of items removed")
    
    # Strategy used
    keep_strategy: KeepStrategy = Field(..., description="Strategy used for item selection")
    
    # Processing metadata
    processing_time_ms: float = Field(..., description="Time taken for deduplication")
    duplicate_groups_processed: int = Field(..., description="Number of duplicate groups processed")


@dataclass
class DetectionPerformanceMetrics:
    """Performance metrics for duplicate detection."""
    processing_time_seconds: float
    items_processed: int
    duplicates_found: int
    throughput_items_per_second: float
    memory_usage_mb: float
    detection_accuracy: Optional[float] = None


class DuplicateDetectionService:
    """Service for comprehensive duplicate detection and deduplication."""
    
    def __init__(
        self,
        similarity_threshold: float = 0.8,
        settings: Optional[Settings] = None
    ):
        """Initialize duplicate detection service."""
        self.similarity_threshold = similarity_threshold
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Available detection strategies
        self.strategies = {
            DuplicationStrategy.EXACT_MATCH: self._exact_match_detection,
            DuplicationStrategy.HASH_COMPARISON: self._hash_comparison_detection,
            DuplicationStrategy.SEMANTIC_SIMILARITY: self._semantic_similarity_detection,
            DuplicationStrategy.FUZZY_MATCHING: self._fuzzy_matching_detection,
            DuplicationStrategy.JACCARD_SIMILARITY: self._jaccard_similarity_detection,
            DuplicationStrategy.COSINE_SIMILARITY: self._cosine_similarity_detection
        }
        
        # Custom similarity functions
        self.custom_similarity_functions: Dict[str, Callable] = {}
        
        # Performance tracking
        self.performance_metrics: List[DetectionPerformanceMetrics] = []
        
        # Initialize ML models if available
        self._initialize_ml_models()
    
    def _initialize_ml_models(self):
        """Initialize ML models for semantic similarity."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("Initialized sentence transformer model")
            except Exception as e:
                self.logger.warning(f"Failed to initialize sentence transformer: {str(e)}")
                self.sentence_model = None
        else:
            self.sentence_model = None
            self.logger.warning("Sentence transformers not available - semantic similarity will be limited")
    
    def find_exact_duplicates(
        self,
        items: List[Any],
        field: str,
        batch_size: Optional[int] = None
    ) -> List[DuplicateResult]:
        """Find exact duplicates based on field content."""
        if not items:
            return []
        
        start_time = datetime.now()
        content_groups = defaultdict(list)
        
        # Group items by field content
        for item in items:
            try:
                content = getattr(item, field)
                if content:
                    content_groups[content].append(item)
            except AttributeError:
                raise ValueError(f"Field '{field}' not found in item")
        
        # Find groups with multiple items (duplicates)
        duplicate_results = []
        for content, group_items in content_groups.items():
            if len(group_items) > 1:
                result = DuplicateResult(
                    group_id=f"exact_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                    items=group_items,
                    similarity_score=1.0,
                    detection_method="exact_match",
                    confidence_level=1.0,
                    false_positive_risk=0.0,
                    processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
                duplicate_results.append(result)
        
        self.logger.info(f"Found {len(duplicate_results)} exact duplicate groups from {len(items)} items")
        return duplicate_results
    
    async def find_semantic_duplicates(
        self,
        items: List[Any], 
        similarity_threshold: Optional[float] = None,
        field: str = 'text'
    ) -> List[DuplicateResult]:
        """Find semantic duplicates using sentence embeddings."""
        if not items or not self.sentence_model:
            return []
        
        threshold = similarity_threshold or self.similarity_threshold
        start_time = datetime.now()
        
        # Extract text content
        texts = []
        for item in items:
            try:
                text_content = getattr(item, field, '')
                texts.append(str(text_content))
            except AttributeError:
                texts.append('')
        
        # Generate embeddings
        try:
            embeddings = self.sentence_model.encode(texts)
            
            # Calculate pairwise similarities
            similarity_matrix = cosine_similarity(embeddings)
            
            # Find duplicate groups
            duplicate_results = []
            processed_indices = set()
            
            for i in range(len(items)):
                if i in processed_indices:
                    continue
                
                # Find similar items
                similar_indices = []
                for j in range(i + 1, len(items)):
                    if similarity_matrix[i][j] >= threshold:
                        similar_indices.append(j)
                
                # Create duplicate group if similar items found
                if similar_indices:
                    group_items = [items[i]] + [items[j] for j in similar_indices]
                    avg_similarity = float(np.mean([similarity_matrix[i][j] for j in similar_indices]))
                    
                    result = DuplicateResult(
                        group_id=f"semantic_{i}_{datetime.now().strftime('%H%M%S')}",
                        items=group_items,
                        similarity_score=avg_similarity,
                        detection_method="semantic_similarity",
                        confidence_level=avg_similarity,
                        false_positive_risk=max(0, 1 - avg_similarity),
                        processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                    duplicate_results.append(result)
                    
                    # Mark as processed
                    processed_indices.add(i)
                    processed_indices.update(similar_indices)
            
            return duplicate_results
            
        except Exception as e:
            self.logger.error(f"Error in semantic duplicate detection: {str(e)}")
            return []
    
    def find_fuzzy_duplicates(
        self,
        items: List[Any],
        field: str,
        fuzzy_threshold: float = 0.8
    ) -> List[DuplicateResult]:
        """Find fuzzy duplicates using string similarity."""
        if not items:
            return []
        
        start_time = datetime.now()
        duplicate_results = []
        processed_indices = set()
        
        for i in range(len(items)):
            if i in processed_indices:
                continue
            
            text1 = str(getattr(items[i], field, ''))
            similar_items = [items[i]]
            similar_indices = [i]
            
            for j in range(i + 1, len(items)):
                if j in processed_indices:
                    continue
                
                text2 = str(getattr(items[j], field, ''))
                similarity = self._calculate_string_similarity(text1, text2)
                
                if similarity >= fuzzy_threshold:
                    similar_items.append(items[j])
                    similar_indices.append(j)
            
            # Create duplicate group if similar items found
            if len(similar_items) > 1:
                avg_similarity = fuzzy_threshold  # Simplified - could calculate actual average
                
                result = DuplicateResult(
                    group_id=f"fuzzy_{i}_{datetime.now().strftime('%H%M%S')}",
                    items=similar_items,
                    similarity_score=avg_similarity,
                    detection_method="fuzzy_matching",
                    confidence_level=avg_similarity,
                    false_positive_risk=max(0, 1 - avg_similarity),
                    processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
                duplicate_results.append(result)
                
                # Mark as processed
                processed_indices.update(similar_indices)
        
        return duplicate_results
    
    def _calculate_string_similarity(self, text1: str, text2: str) -> float:
        """Calculate string similarity using available methods."""
        if not text1 or not text2:
            return 0.0
        
        # Use Levenshtein if available, otherwise use difflib
        if LEVENSHTEIN_AVAILABLE:
            distance = Levenshtein.distance(text1, text2)
            max_len = max(len(text1), len(text2))
            return 1.0 - (distance / max_len) if max_len > 0 else 1.0
        else:
            return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    async def _calculate_semantic_similarity(self, item1: Any, item2: Any, field: str = 'text') -> float:
        """Calculate semantic similarity between two items."""
        if not self.sentence_model:
            return 0.0
        
        try:
            text1 = str(getattr(item1, field, ''))
            text2 = str(getattr(item2, field, ''))
            
            if not text1 or not text2:
                return 0.0
            
            embeddings = self.sentence_model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0
    
    def calculate_similarity_metrics(self, text1: str, text2: str) -> SimilarityMetrics:
        """Calculate comprehensive similarity metrics between two texts."""
        # Jaccard similarity
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        jaccard = len(set1.intersection(set2)) / len(set1.union(set2)) if set1.union(set2) else 0.0
        
        # Cosine similarity using TF-IDF
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception:
            cosine_sim = 0.0
        
        # Levenshtein similarity
        levenshtein_sim = self._calculate_string_similarity(text1, text2)
        
        # Semantic similarity (if available)
        semantic_sim = 0.0
        if self.sentence_model:
            try:
                embeddings = self.sentence_model.encode([text1, text2])
                semantic_sim = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            except Exception:
                semantic_sim = 0.0
        
        return SimilarityMetrics(
            jaccard_similarity=jaccard,
            cosine_similarity=cosine_sim,
            levenshtein_similarity=levenshtein_sim,
            semantic_similarity=semantic_sim,
            calculation_method="comprehensive",
            confidence_score=max(jaccard, cosine_sim, levenshtein_sim, semantic_sim)
        )
    
    async def detect_all_duplicates(
        self,
        items: List[Any],
        strategies: List[DuplicationStrategy],
        field: str = 'text'
    ) -> List[DuplicateResult]:
        """Detect duplicates using multiple strategies."""
        all_duplicates = []
        
        for strategy in strategies:
            try:
                if strategy == DuplicationStrategy.EXACT_MATCH:
                    duplicates = self.find_exact_duplicates(items, field)
                elif strategy == DuplicationStrategy.SEMANTIC_SIMILARITY:
                    duplicates = await self.find_semantic_duplicates(items, field=field)
                elif strategy == DuplicationStrategy.FUZZY_MATCHING:
                    duplicates = self.find_fuzzy_duplicates(items, field)
                else:
                    self.logger.warning(f"Strategy {strategy} not yet implemented")
                    continue
                
                all_duplicates.extend(duplicates)
                
            except Exception as e:
                self.logger.error(f"Error with strategy {strategy}: {str(e)}")
                continue
        
        # Remove duplicate results (meta-duplicates)
        deduplicated_results = self._deduplicate_results(all_duplicates)
        
        return deduplicated_results
    
    def _deduplicate_results(self, results: List[DuplicateResult]) -> List[DuplicateResult]:
        """Remove duplicate results from multiple detection strategies."""
        if not results:
            return []
        
        # Group results by item sets
        item_signature_to_result = {}
        
        for result in results:
            # Create signature from item IDs
            item_ids = sorted([str(getattr(item, 'id', hash(str(item)))) for item in result.items])
            signature = hashlib.md5('|'.join(item_ids).encode()).hexdigest()
            
            # Keep result with highest similarity score
            if signature not in item_signature_to_result:
                item_signature_to_result[signature] = result
            elif result.similarity_score > item_signature_to_result[signature].similarity_score:
                item_signature_to_result[signature] = result
        
        return list(item_signature_to_result.values())
    
    async def deduplicate_items(
        self,
        items: List[Any],
        keep_strategy: str = 'keep_first',
        detection_strategies: Optional[List[DuplicationStrategy]] = None,
        field: str = 'text'
    ) -> DeduplicationResult:
        """Perform deduplication on items."""
        start_time = datetime.now()
        original_count = len(items)
        
        # Default strategies
        if detection_strategies is None:
            detection_strategies = [
                DuplicationStrategy.EXACT_MATCH,
                DuplicationStrategy.SEMANTIC_SIMILARITY
            ]
        
        # Find duplicates
        duplicates = await self.detect_all_duplicates(items, detection_strategies, field)
        
        # Apply deduplication
        kept_items = list(items)  # Start with all items
        removed_items = []
        
        for duplicate_group in duplicates:
            if len(duplicate_group.items) > 1:
                # Apply keep strategy
                item_to_keep = self._apply_keep_strategy(duplicate_group.items, keep_strategy)
                items_to_remove = [item for item in duplicate_group.items if item != item_to_keep]
                
                # Update lists
                for item in items_to_remove:
                    if item in kept_items:
                        kept_items.remove(item)
                        removed_items.append(item)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        final_count = len(kept_items)
        removal_rate = (original_count - final_count) / original_count if original_count > 0 else 0.0
        
        return DeduplicationResult(
            kept_items=kept_items,
            removed_items=removed_items,
            original_count=original_count,
            final_count=final_count,
            removal_rate=removal_rate,
            keep_strategy=KeepStrategy(keep_strategy),
            processing_time_ms=processing_time,
            duplicate_groups_processed=len(duplicates)
        )
    
    def _apply_keep_strategy(self, items: List[Any], strategy: str) -> Any:
        """Apply keep strategy to select item from duplicate group."""
        if not items:
            return None
        
        if strategy == 'keep_first':
            return items[0]
        elif strategy == 'keep_last':
            return items[-1]
        elif strategy == 'highest_quality':
            return self._select_higher_quality_item(items)
        elif strategy == 'most_complete':
            return self._select_most_complete_item(items)
        elif strategy == 'most_recent':
            return self._select_most_recent_item(items)
        else:
            return items[0]  # Default to first
    
    def _select_higher_quality_item(self, items: List[Any]) -> Any:
        """Select item with highest quality based on heuristics."""
        if not items:
            return None
        
        def quality_score(item) -> float:
            score = 0.0
            
            # Text length (longer often better for documents)
            if hasattr(item, 'content'):
                score += min(len(item.content) / 1000, 1.0) * 0.3
            elif hasattr(item, 'text'):
                score += min(len(item.text) / 500, 1.0) * 0.3
            
            # Metadata completeness
            if hasattr(item, 'metadata') and item.metadata:
                score += min(len(item.metadata) / 5, 1.0) * 0.2
            
            # Source reliability (heuristic based on metadata)
            if hasattr(item, 'metadata') and item.metadata:
                reliable_sources = ['perseus', 'cambridge', 'oxford', 'loeb']
                source = item.metadata.get('source', '').lower()
                if any(reliable in source for reliable in reliable_sources):
                    score += 0.3
            
            # Completeness indicators
            if hasattr(item, 'title') and item.title:
                score += 0.1
            if hasattr(item, 'author') and item.author:
                score += 0.1
            
            return score
        
        return max(items, key=quality_score)
    
    def _select_most_complete_item(self, items: List[Any]) -> Any:
        """Select most complete item based on field population."""
        if not items:
            return None
        
        def completeness_score(item) -> int:
            score = 0
            for attr_name in dir(item):
                if not attr_name.startswith('_'):
                    try:
                        value = getattr(item, attr_name)
                        if value and not callable(value):
                            score += 1
                    except Exception:
                        continue
            return score
        
        return max(items, key=completeness_score)
    
    def _select_most_recent_item(self, items: List[Any]) -> Any:
        """Select most recently created/updated item."""
        if not items:
            return None
        
        def get_timestamp(item):
            # Try different timestamp fields
            for field in ['updated_at', 'created_at', 'timestamp']:
                if hasattr(item, field):
                    timestamp = getattr(item, field)
                    if timestamp:
                        return timestamp
            return datetime.min.replace(tzinfo=timezone.utc)
        
        return max(items, key=get_timestamp)
    
    async def detect_cross_collection_duplicates(
        self,
        collections: Dict[str, List[Any]],
        text_fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """Detect duplicates across different collections."""
        cross_duplicates = []
        
        collection_names = list(collections.keys())
        
        # Compare each pair of collections
        for i, coll1_name in enumerate(collection_names):
            for coll2_name in collection_names[i+1:]:
                coll1_items = collections[coll1_name]
                coll2_items = collections[coll2_name]
                
                field1 = text_fields.get(coll1_name, 'text')
                field2 = text_fields.get(coll2_name, 'text')
                
                # Find duplicates between collections
                for item1 in coll1_items:
                    text1 = str(getattr(item1, field1, ''))
                    
                    for item2 in coll2_items:
                        text2 = str(getattr(item2, field2, ''))
                        
                        if text1 and text2:
                            similarity = await self._calculate_semantic_similarity(item1, item2, field1)
                            
                            if similarity >= self.similarity_threshold:
                                cross_duplicates.append({
                                    'collection1': coll1_name,
                                    'collection2': coll2_name,
                                    'item1': item1,
                                    'item2': item2,
                                    'similarity': similarity
                                })
        
        return {
            'cross_collection_duplicates': cross_duplicates,
            'collections_compared': len(collection_names),
            'total_comparisons': len(cross_duplicates)
        }
    
    def calculate_duplication_statistics(
        self,
        total_items: int,
        duplicates: List[DuplicateResult]
    ) -> Dict[str, Any]:
        """Calculate duplication statistics."""
        if total_items == 0:
            return {
                'total_items': 0,
                'duplicate_groups': 0,
                'duplication_rate': 0.0,
                'items_affected': 0
            }
        
        duplicate_groups = len(duplicates)
        items_affected = sum(len(dup.items) for dup in duplicates)
        duplication_rate = items_affected / total_items
        
        # Additional statistics
        group_sizes = [len(dup.items) for dup in duplicates]
        avg_group_size = statistics.mean(group_sizes) if group_sizes else 0
        max_group_size = max(group_sizes) if group_sizes else 0
        
        similarity_scores = [dup.similarity_score for dup in duplicates]
        avg_similarity = statistics.mean(similarity_scores) if similarity_scores else 0
        
        return {
            'total_items': total_items,
            'duplicate_groups': duplicate_groups,
            'duplication_rate': duplication_rate,
            'items_affected': items_affected,
            'average_group_size': avg_group_size,
            'max_group_size': max_group_size,
            'average_similarity_score': avg_similarity,
            'detection_methods_used': list(set(dup.detection_method for dup in duplicates))
        }
    
    def register_similarity_function(self, name: str, function: Callable) -> None:
        """Register custom similarity function."""
        self.custom_similarity_functions[name] = function
        self.logger.info(f"Registered custom similarity function: {name}")
    
    def calculate_custom_similarity(self, text1: str, text2: str, function_name: str) -> float:
        """Calculate similarity using custom function."""
        if function_name not in self.custom_similarity_functions:
            raise ValueError(f"Unknown similarity function: {function_name}")
        
        function = self.custom_similarity_functions[function_name]
        return function(text1, text2)
    
    async def detect_incremental_duplicates(
        self,
        existing_items: List[Any],
        new_items: List[Any],
        field: str
    ) -> List[DuplicateResult]:
        """Detect duplicates in new items against existing items."""
        all_items = existing_items + new_items
        
        # Find all duplicates
        all_duplicates = await self.detect_all_duplicates(
            all_items,
            [DuplicationStrategy.EXACT_MATCH, DuplicationStrategy.SEMANTIC_SIMILARITY],
            field
        )
        
        # Filter to only duplicates involving new items
        incremental_duplicates = []
        for duplicate in all_duplicates:
            # Check if any new items are in this duplicate group
            has_new_item = any(item in new_items for item in duplicate.items)
            if has_new_item:
                incremental_duplicates.append(duplicate)
        
        return incremental_duplicates
    
    def _monitor_performance(self, operation_name: str, start_time: datetime, items_count: int) -> Dict[str, Any]:
        """Monitor performance of detection operations."""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        throughput = items_count / processing_time if processing_time > 0 else 0
        
        performance_data = {
            'operation': operation_name,
            'processing_time': processing_time,
            'items_processed': items_count,
            'throughput': throughput,
            'timestamp': end_time
        }
        
        self.logger.info(f"Performance - {operation_name}: {processing_time:.2f}s for {items_count} items ({throughput:.1f} items/s)")
        
        return performance_data
    
    # Strategy-specific detection methods (for internal use)
    def _exact_match_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Exact match detection strategy."""
        return self.find_exact_duplicates(items, field)
    
    def _hash_comparison_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Hash-based comparison strategy."""
        # Similar to exact match but using hashes for efficiency
        return self.find_exact_duplicates(items, field)
    
    async def _semantic_similarity_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Semantic similarity detection strategy."""
        return await self.find_semantic_duplicates(items, field=field)
    
    def _fuzzy_matching_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Fuzzy matching detection strategy."""
        return self.find_fuzzy_duplicates(items, field)
    
    def _jaccard_similarity_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Jaccard similarity detection strategy."""
        # Placeholder implementation
        return []
    
    def _cosine_similarity_detection(self, items: List[Any], field: str) -> List[DuplicateResult]:
        """Cosine similarity detection strategy."""
        # Placeholder implementation  
        return []