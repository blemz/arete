"""
Result Diversity Optimization Service for Arete Graph-RAG System.

Provides advanced result diversification to avoid redundant or overly similar results,
improving user experience with diverse perspectives on philosophical topics.

The service implements multiple diversification strategies:
- Maximum Marginal Relevance (MMR)
- Clustering-based diversification
- Semantic distance optimization
- Hybrid approaches combining multiple methods

Designed for philosophical content with domain-specific optimizations for
classical texts and concepts.
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import logging

from src.arete.services.dense_retrieval_service import SearchResult
from src.arete.models.chunk import Chunk
from src.arete.config import Settings

logger = logging.getLogger(__name__)


class DiversityMethod(Enum):
    """Available diversity optimization methods."""
    MMR = "mmr"
    CLUSTERING = "clustering" 
    SEMANTIC_DISTANCE = "semantic_distance"
    HYBRID = "hybrid"


class DiversityError(Exception):
    """Custom exception for diversity service errors."""
    pass


@dataclass
class ClusterInfo:
    """Information about a result cluster."""
    cluster_id: int
    center_embedding: List[float]
    size: int
    coherence: float
    topic_keywords: List[str] = field(default_factory=list)
    representative_text: str = ""
    
    def calculate_similarity(self, other: 'ClusterInfo') -> float:
        """Calculate similarity between clusters based on center embeddings."""
        if len(self.center_embedding) != len(other.center_embedding):
            return 0.0
        
        similarity = cosine_similarity(
            [self.center_embedding], 
            [other.center_embedding]
        )[0][0]
        
        return max(0.0, similarity)


@dataclass
class DiversityResult:
    """Result with diversity optimization information."""
    original_result: SearchResult
    diversity_score: float
    cluster_id: int
    cluster_center_distance: float
    uniqueness_score: float
    topical_diversity: float
    semantic_novelty: float
    
    def get_final_score(self, strategy: str = "balanced", relevance_weight: float = 0.7) -> float:
        """
        Calculate final score combining relevance and diversity.
        
        Args:
            strategy: Scoring strategy ("relevance_only", "diversity_only", "balanced")
            relevance_weight: Weight for relevance score (if balanced)
        
        Returns:
            Combined final score
        """
        if strategy == "relevance_only":
            return self.original_result.relevance_score
        elif strategy == "diversity_only":
            return self.diversity_score
        elif strategy == "balanced":
            diversity_weight = 1.0 - relevance_weight
            return (self.original_result.relevance_score * relevance_weight + 
                   self.diversity_score * diversity_weight)
        else:
            raise ValueError(f"Unknown scoring strategy: {strategy}")


@dataclass
class DiversityConfig:
    """Configuration for diversity optimization."""
    method: DiversityMethod = DiversityMethod.MMR
    lambda_param: float = 0.7  # Balance between relevance and diversity in MMR
    max_results: int = 50
    similarity_threshold: float = 0.85  # Threshold for considering results similar
    cluster_method: str = "kmeans"
    num_clusters: int = 5
    min_cluster_size: int = 2
    diversity_weight: float = 0.3  # Weight for diversity in final scoring
    
    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        self.is_valid()
    
    def is_valid(self) -> bool:
        """Validate configuration parameters."""
        if not (0.0 <= self.lambda_param <= 1.0):
            raise ValueError("lambda_param must be between 0.0 and 1.0")
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        if self.num_clusters <= 0:
            raise ValueError("num_clusters must be positive")
        if self.min_cluster_size < 1:
            raise ValueError("min_cluster_size must be at least 1")
        return True


@dataclass
class DiversityMetrics:
    """Metrics for diversity service performance."""
    total_diversification_requests: int = 0
    total_processing_time: float = 0.0
    total_results_processed: int = 0
    method_usage: Dict[str, int] = field(default_factory=dict)
    clustering_efficiency: float = 0.0
    average_diversity_improvement: float = 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of diversity metrics."""
        if self.total_diversification_requests == 0:
            return {
                'total_diversification_requests': 0,
                'average_processing_time': 0,
                'average_diversity_score': 0,
                'clustering_efficiency': 0,
                'method_usage': {}
            }
        
        return {
            'total_diversification_requests': self.total_diversification_requests,
            'average_processing_time': self.total_processing_time / self.total_diversification_requests,
            'total_results_processed': self.total_results_processed,
            'average_diversity_score': self.average_diversity_improvement / self.total_diversification_requests,
            'clustering_efficiency': self.clustering_efficiency,
            'method_usage': dict(self.method_usage)
        }
    
    def reset(self):
        """Reset all metrics."""
        self.total_diversification_requests = 0
        self.total_processing_time = 0.0
        self.total_results_processed = 0
        self.method_usage.clear()
        self.clustering_efficiency = 0.0
        self.average_diversity_improvement = 0.0


class DiversityService:
    """
    Service for optimizing result diversity to avoid redundancy.
    
    Implements multiple diversification algorithms to ensure search results
    provide varied perspectives and avoid repetitive content.
    """
    
    def __init__(
        self, 
        config: DiversityConfig,
        settings: Settings
    ):
        """
        Initialize diversity service.
        
        Args:
            config: Diversity configuration
            settings: Application settings
        """
        self.config = config
        self.settings = settings
        self.metrics = DiversityMetrics()
        self.cache: Dict[str, List[DiversityResult]] = {}
        self.is_initialized = True
        
        # Validate configuration
        self.config.is_valid()
        
        # Philosophical domain terms for topical analysis
        self.philosophical_concepts = {
            "virtue", "justice", "wisdom", "courage", "temperance",
            "knowledge", "truth", "beauty", "good", "evil",
            "soul", "mind", "body", "reason", "emotion",
            "ethics", "morality", "politics", "metaphysics", "logic"
        }
        
        self.classical_authors = {
            "socrates", "plato", "aristotle", "epicurus", "stoic",
            "marcus aurelius", "seneca", "epictetus", "cicero",
            "augustine", "aquinas", "descartes", "kant", "hegel"
        }
        
        logger.info(f"DiversityService initialized with method: {config.method}")
    
    def diversify(
        self, 
        search_results: List[SearchResult],
        method: Optional[DiversityMethod] = None
    ) -> List[DiversityResult]:
        """
        Diversify search results to reduce redundancy.
        
        Args:
            search_results: List of search results to diversify
            method: Diversification method to use (overrides config)
        
        Returns:
            List of diversified results with diversity metadata
        """
        if not search_results:
            return []
        
        method = method or self.config.method
        start_time = time.time()
        
        try:
            # Check cache
            cache_key = self._generate_cache_key(search_results, method)
            if cache_key in self.cache:
                logger.debug(f"Using cached diversification results")
                return self.cache[cache_key]
            
            # Validate method
            if isinstance(method, str):
                try:
                    method = DiversityMethod(method)
                except ValueError:
                    raise DiversityError(f"Unknown diversification method: {method}")
            elif not isinstance(method, DiversityMethod):
                raise DiversityError(f"Invalid method type: {type(method)}")
            
            # Apply diversification method
            if method == DiversityMethod.MMR:
                diversified_results = self._mmr_diversification(search_results)
            elif method == DiversityMethod.CLUSTERING:
                diversified_results = self._clustering_diversification(search_results)
            elif method == DiversityMethod.SEMANTIC_DISTANCE:
                diversified_results = self._semantic_distance_diversification(search_results)
            elif method == DiversityMethod.HYBRID:
                diversified_results = self._hybrid_diversification(search_results)
            else:
                raise DiversityError(f"Unknown diversification method: {method}")
            
            # Cache results
            self.cache[cache_key] = diversified_results
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(method.value, len(search_results), processing_time, diversified_results)
            
            logger.info(f"Diversified {len(search_results)} results to {len(diversified_results)} using {method.value}")
            return diversified_results
            
        except Exception as e:
            logger.error(f"Error in diversification: {e}")
            raise DiversityError(f"Diversification failed: {e}")
    
    def _mmr_diversification(self, results: List[SearchResult]) -> List[DiversityResult]:
        """Apply Maximum Marginal Relevance diversification."""
        if len(results) <= 1:
            if results:
                return [self._create_diversity_result(results[0], 0, 1.0, 0.0, 1.0, 1.0, 1.0)]
            return []
        
        selected = []
        remaining = results[:]
        embeddings = [result.chunk.embedding_vector for result in results]
        
        # Select first result (highest relevance)
        best_result = max(remaining, key=lambda x: x.relevance_score)
        remaining.remove(best_result)
        selected.append(best_result)
        
        # Iteratively select diverse results
        while remaining and len(selected) < self.config.max_results:
            best_score = -1
            best_result = None
            best_diversity = 0.0
            
            for candidate in remaining:
                # Calculate relevance score
                relevance = candidate.relevance_score
                
                # Calculate diversity (minimum similarity to selected)
                candidate_embedding = candidate.chunk.embedding_vector
                max_similarity = 0.0
                
                for selected_result in selected:
                    selected_embedding = selected_result.chunk.embedding_vector
                    similarity = self._calculate_cosine_similarity(candidate_embedding, selected_embedding)
                    max_similarity = max(max_similarity, similarity)
                
                diversity = 1.0 - max_similarity
                
                # MMR score
                mmr_score = self.config.lambda_param * relevance + (1 - self.config.lambda_param) * diversity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_result = candidate
                    best_diversity = diversity
            
            if best_result and best_diversity > (1.0 - self.config.similarity_threshold):
                selected.append(best_result)
                remaining.remove(best_result)
            else:
                break
        
        # Convert to DiversityResults
        diversity_results = []
        for i, result in enumerate(selected):
            diversity_score = self._calculate_overall_diversity_score(result, selected)
            diversity_results.append(
                self._create_diversity_result(
                    result, i, diversity_score, 0.0, 
                    diversity_score, diversity_score, diversity_score
                )
            )
        
        return diversity_results
    
    def _clustering_diversification(self, results: List[SearchResult]) -> List[DiversityResult]:
        """Apply clustering-based diversification."""
        if len(results) <= self.config.num_clusters:
            # Not enough results to cluster effectively
            return [
                self._create_diversity_result(result, i, 0.8, 0.2, 0.8, 0.8, 0.8)
                for i, result in enumerate(results[:self.config.max_results])
            ]
        
        # Extract embeddings
        embeddings = np.array([result.chunk.embedding_vector for result in results])
        
        # Perform clustering
        n_clusters = min(self.config.num_clusters, len(results))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Create cluster info
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = ClusterInfo(
                    cluster_id=label,
                    center_embedding=kmeans.cluster_centers_[label].tolist(),
                    size=0,
                    coherence=0.0,
                    topic_keywords=[],
                    representative_text=""
                )
            clusters[label].size += 1
        
        # Select representatives from each cluster
        diversity_results = []
        for cluster_id, cluster_info in clusters.items():
            cluster_results = [results[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            if len(cluster_results) >= self.config.min_cluster_size:
                # Select best result from cluster (highest relevance)
                best_result = max(cluster_results, key=lambda x: x.relevance_score)
                
                # Calculate cluster distance
                result_embedding = np.array(best_result.chunk.embedding_vector)
                center_embedding = np.array(cluster_info.center_embedding)
                distance = np.linalg.norm(result_embedding - center_embedding)
                
                diversity_score = 0.9 - (distance * 0.3)  # Convert distance to diversity score
                diversity_results.append(
                    self._create_diversity_result(
                        best_result, cluster_id, diversity_score, distance,
                        diversity_score, diversity_score, diversity_score
                    )
                )
        
        # Sort by relevance and limit results
        diversity_results.sort(key=lambda x: x.original_result.relevance_score, reverse=True)
        return diversity_results[:self.config.max_results]
    
    def _semantic_distance_diversification(self, results: List[SearchResult]) -> List[DiversityResult]:
        """Apply semantic distance-based diversification."""
        if len(results) <= 1:
            if results:
                return [self._create_diversity_result(results[0], 0, 1.0, 0.0, 1.0, 1.0, 1.0)]
            return []
        
        selected = []
        embeddings = [result.chunk.embedding_vector for result in results]
        
        # Start with highest relevance result
        best_result = max(results, key=lambda x: x.relevance_score)
        selected.append(best_result)
        remaining_indices = [i for i, r in enumerate(results) if r != best_result]
        
        while remaining_indices and len(selected) < self.config.max_results:
            best_distance = -1
            best_idx = None
            best_novelty = 0.0
            
            for idx in remaining_indices:
                candidate = results[idx]
                candidate_embedding = embeddings[idx]
                
                # Calculate minimum distance to selected results
                min_distance = float('inf')
                for selected_result in selected:
                    selected_embedding = selected_result.chunk.embedding_vector
                    distance = 1.0 - self._calculate_cosine_similarity(candidate_embedding, selected_embedding)
                    min_distance = min(min_distance, distance)
                
                semantic_novelty = min_distance
                
                # Combine with relevance
                combined_score = (candidate.relevance_score * 0.5 + semantic_novelty * 0.5)
                
                if combined_score > best_distance:
                    best_distance = combined_score
                    best_idx = idx
                    best_novelty = semantic_novelty
            
            if best_idx is not None and best_novelty > (1.0 - self.config.similarity_threshold):
                selected.append(results[best_idx])
                remaining_indices.remove(best_idx)
            else:
                break
        
        # Convert to DiversityResults
        diversity_results = []
        for i, result in enumerate(selected):
            diversity_score = self._calculate_overall_diversity_score(result, selected)
            semantic_novelty = self._calculate_semantic_novelty(result, selected)
            
            diversity_results.append(
                self._create_diversity_result(
                    result, i, diversity_score, 0.0, 
                    diversity_score, diversity_score, semantic_novelty
                )
            )
        
        return diversity_results
    
    def _hybrid_diversification(self, results: List[SearchResult]) -> List[DiversityResult]:
        """Apply hybrid diversification combining multiple methods."""
        # Get results from different methods
        mmr_results = self._mmr_diversification(results)
        clustering_results = self._clustering_diversification(results)
        semantic_results = self._semantic_distance_diversification(results)
        
        # Combine and deduplicate
        all_results = {}  # Use dict to avoid duplicates
        
        for result_list in [mmr_results, clustering_results, semantic_results]:
            for diversity_result in result_list:
                result_text = diversity_result.original_result.chunk.text
                if result_text not in all_results:
                    all_results[result_text] = diversity_result
                else:
                    # Keep result with better diversity score
                    existing = all_results[result_text]
                    if diversity_result.diversity_score > existing.diversity_score:
                        all_results[result_text] = diversity_result
        
        combined_results = list(all_results.values())
        
        # Recalculate diversity scores for hybrid method
        for i, result in enumerate(combined_results):
            topical_diversity = self._calculate_topical_diversity(result.original_result, results)
            semantic_novelty = self._calculate_semantic_novelty(result.original_result, 
                                                              [r.original_result for r in combined_results])
            
            # Update diversity metrics for hybrid
            result.topical_diversity = topical_diversity
            result.semantic_novelty = semantic_novelty
            result.diversity_score = (topical_diversity + semantic_novelty) / 2
        
        # Sort by final balanced score and limit
        combined_results.sort(key=lambda x: x.get_final_score("balanced"), reverse=True)
        return combined_results[:self.config.max_results]
    
    def _calculate_overall_diversity_score(self, target_result: SearchResult, selected_results: List[SearchResult]) -> float:
        """Calculate overall diversity score for a result against selected results."""
        if len(selected_results) <= 1:
            return 1.0
        
        similarities = []
        target_embedding = target_result.chunk.embedding_vector
        
        for selected_result in selected_results:
            if selected_result != target_result:
                selected_embedding = selected_result.chunk.embedding_vector
                similarity = self._calculate_cosine_similarity(target_embedding, selected_embedding)
                similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Diversity is inverse of average similarity
        avg_similarity = sum(similarities) / len(similarities)
        return max(0.0, 1.0 - avg_similarity)
    
    def _calculate_topical_diversity(self, result: SearchResult, all_results: List[SearchResult]) -> float:
        """Calculate topical diversity based on concept coverage."""
        result_text = result.chunk.text.lower()
        result_concepts = set()
        
        # Extract concepts from result text
        for concept in self.philosophical_concepts:
            if concept in result_text:
                result_concepts.add(concept)
        
        # Extract concepts from other results (excluding current)
        other_concepts = set()
        for other_result in all_results:
            if other_result != result:
                other_text = other_result.chunk.text.lower()
                for concept in self.philosophical_concepts:
                    if concept in other_text:
                        other_concepts.add(concept)
        
        if not result_concepts:
            return 0.5  # Neutral score if no concepts detected
        
        # Calculate concept uniqueness
        unique_concepts = result_concepts - other_concepts
        if not result_concepts:
            return 0.5
            
        concept_diversity = len(unique_concepts) / len(result_concepts)
        
        return min(1.0, concept_diversity + 0.5)  # Boost base score
    
    def _calculate_semantic_novelty(self, target_result: SearchResult, other_results: List[SearchResult]) -> float:
        """Calculate semantic novelty score."""
        if not other_results or target_result in other_results and len(other_results) == 1:
            return 1.0
        
        target_embedding = target_result.chunk.embedding_vector
        max_similarity = 0.0
        
        for other_result in other_results:
            if other_result != target_result:
                other_embedding = other_result.chunk.embedding_vector
                similarity = self._calculate_cosine_similarity(target_embedding, other_embedding)
                max_similarity = max(max_similarity, similarity)
        
        return max(0.0, 1.0 - max_similarity)
    
    def _extract_topics(self, results: List[SearchResult]) -> Dict[str, float]:
        """Extract topics from search results."""
        topic_counts = {}
        
        for result in results:
            text = result.chunk.text.lower()
            
            # Count philosophical concepts
            for concept in self.philosophical_concepts:
                if concept in text:
                    topic_counts[concept] = topic_counts.get(concept, 0) + 1
            
            # Count classical authors
            for author in self.classical_authors:
                if author in text:
                    topic_counts[author] = topic_counts.get(author, 0) + 1
        
        # Normalize counts
        total_mentions = sum(topic_counts.values())
        if total_mentions > 0:
            for topic in topic_counts:
                topic_counts[topic] = topic_counts[topic] / total_mentions
        
        return topic_counts
    
    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)  # Ensure non-negative
    
    def _create_diversity_result(
        self, 
        result: SearchResult, 
        cluster_id: int,
        diversity_score: float,
        cluster_center_distance: float,
        uniqueness_score: float,
        topical_diversity: float,
        semantic_novelty: float
    ) -> DiversityResult:
        """Create a DiversityResult object."""
        return DiversityResult(
            original_result=result,
            diversity_score=diversity_score,
            cluster_id=cluster_id,
            cluster_center_distance=cluster_center_distance,
            uniqueness_score=uniqueness_score,
            topical_diversity=topical_diversity,
            semantic_novelty=semantic_novelty
        )
    
    def _generate_cache_key(self, results: List[SearchResult], method: DiversityMethod) -> str:
        """Generate cache key for results and method."""
        # Create hash from result texts and method
        texts = [result.chunk.text for result in results]
        combined = f"{method.value}:{':'.join(texts)}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _update_metrics(
        self, 
        method: str, 
        num_results: int, 
        processing_time: float,
        diversified_results: List[DiversityResult]
    ):
        """Update service metrics."""
        self.metrics.total_diversification_requests += 1
        self.metrics.total_processing_time += processing_time
        self.metrics.total_results_processed += num_results
        
        # Update method usage
        if method not in self.metrics.method_usage:
            self.metrics.method_usage[method] = 0
        self.metrics.method_usage[method] += 1
        
        # Calculate average diversity improvement
        if diversified_results:
            avg_diversity = sum(r.diversity_score for r in diversified_results) / len(diversified_results)
            self.metrics.average_diversity_improvement += avg_diversity
        
        # Calculate clustering efficiency (for clustering methods)
        if method == "clustering" and diversified_results:
            unique_clusters = len(set(r.cluster_id for r in diversified_results))
            self.metrics.clustering_efficiency = unique_clusters / max(1, len(diversified_results))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        return self.metrics.get_summary()
    
    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics.reset()


def create_diversity_service(settings: Settings, config: Optional[DiversityConfig] = None) -> DiversityService:
    """
    Factory function to create a configured DiversityService.
    
    Args:
        settings: Application settings
        config: Optional diversity configuration (uses defaults if not provided)
    
    Returns:
        Configured DiversityService instance
    """
    if config is None:
        config = DiversityConfig()
    
    return DiversityService(config=config, settings=settings)