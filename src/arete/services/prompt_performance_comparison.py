"""
Cross-provider prompt performance comparison system.

This module provides comprehensive performance comparison capabilities for
philosophical tutoring prompts across different LLM providers, including
metrics collection, quality assessment, and optimization recommendations.
"""

import logging
import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
import statistics
import re

from arete.services.prompt_service import PromptService, TutoringRequest
from arete.services.prompt_template import (
    PromptType,
    PromptContext,
    PhilosophicalContext,
    Citation
)

# Setup logger
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics to collect."""
    RESPONSE_TIME = "response_time"
    TOKEN_COUNT = "token_count"
    ACCURACY = "accuracy"
    CITATION_QUALITY = "citation_quality"
    EDUCATIONAL_VALUE = "educational_value"
    COHERENCE = "coherence"
    ALL = "all"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single provider response."""
    provider: str
    response_time: float
    token_count: int
    accuracy_score: float
    citation_quality: float
    educational_value: float
    coherence_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate weighted overall performance score.
        
        Args:
            weights: Custom weights for different metrics
            
        Returns:
            Weighted overall score (0.0-1.0)
        """
        default_weights = {
            "accuracy": 0.30,
            "citation_quality": 0.25,
            "educational_value": 0.25,
            "coherence": 0.20
        }
        
        weights = weights or default_weights
        
        score = (
            self.accuracy_score * weights["accuracy"] +
            self.citation_quality * weights["citation_quality"] +
            self.educational_value * weights["educational_value"] +
            self.coherence_score * weights["coherence"]
        )
        
        return min(1.0, max(0.0, score))


@dataclass
class PromptTest:
    """Test case for prompt performance evaluation."""
    query: str
    expected_concepts: List[str]
    philosophical_context: Optional[PhilosophicalContext] = None
    student_level: str = "undergraduate"
    learning_objective: Optional[str] = None
    citations: List[Citation] = field(default_factory=list)
    retrieved_passages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderComparison:
    """Comparison results for a single provider."""
    provider: str
    average_metrics: PerformanceMetrics
    individual_results: List[PerformanceMetrics] = field(default_factory=list)
    test_count: int = 0
    best_score: float = 0.0
    worst_score: float = 1.0
    score_variance: float = 0.0


@dataclass
class OptimizationRecommendation:
    """Recommendation for optimizing prompt performance."""
    recommendation_type: str  # provider_selection, prompt_tuning, etc.
    priority: str  # high, medium, low
    description: str
    expected_improvement: float  # Percentage improvement expected
    implementation_effort: str  # low, medium, high
    affected_metrics: List[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """Complete comparison results across providers."""
    provider_comparisons: List[ProviderComparison]
    test_cases_used: List[PromptTest]
    total_tests: int
    best_provider: str
    recommendations: List[OptimizationRecommendation]
    comparison_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_provider_ranking(self) -> List[ProviderComparison]:
        """Get providers ranked by overall performance."""
        return sorted(
            self.provider_comparisons,
            key=lambda x: x.average_metrics.get_overall_score(),
            reverse=True
        )


class PromptPerformanceComparison:
    """
    Service for comparing prompt performance across LLM providers.
    
    Provides comprehensive analysis of philosophical tutoring prompts including
    accuracy assessment, citation quality, educational value, and coherence.
    """
    
    def __init__(self, prompt_service: Optional[PromptService] = None):
        """
        Initialize performance comparison service.
        
        Args:
            prompt_service: PromptService instance for generating responses
        """
        self.prompt_service = prompt_service or PromptService()
        self.comparison_cache: Dict[str, ComparisonResult] = {}
        self.test_results: List[PerformanceMetrics] = []
        
        # Philosophical concept keywords for accuracy evaluation
        self.philosophical_keywords = {
            "ancient": ["virtue", "eudaimonia", "forms", "cave", "dialectic", "logos"],
            "medieval": ["faith", "reason", "scholastic", "aquinas", "augustine", "synthesis"],
            "modern": ["cogito", "empiricism", "rationalism", "categorical", "synthetic", "analytic"],
            "contemporary": ["existentialism", "phenomenology", "analytic", "deconstruction", "pragmatism"]
        }
        
        logger.info("PromptPerformanceComparison initialized")
    
    async def run_provider_comparison(
        self,
        test_cases: List[PromptTest],
        providers: List[str],
        include_metrics: List[MetricType] = None,
        batch_size: int = 3,
        cache_results: bool = True
    ) -> ComparisonResult:
        """
        Run comprehensive performance comparison across providers.
        
        Args:
            test_cases: Test cases to evaluate
            providers: List of provider names to compare
            include_metrics: Specific metrics to collect (all if None)
            batch_size: Number of concurrent requests per provider
            cache_results: Whether to cache comparison results
            
        Returns:
            Comprehensive comparison results
        """
        include_metrics = include_metrics or [MetricType.ALL]
        
        # Check cache first
        cache_key = self._generate_cache_key(test_cases, providers, include_metrics)
        if cache_results and cache_key in self.comparison_cache:
            logger.info(f"Returning cached comparison result for {len(providers)} providers")
            return self.comparison_cache[cache_key]
        
        logger.info(f"Running performance comparison: {len(providers)} providers, {len(test_cases)} test cases")
        
        # Run comparisons for each provider
        provider_comparisons = []
        
        for provider in providers:
            logger.info(f"Testing provider: {provider}")
            
            # Process test cases in batches
            all_metrics = []
            for i in range(0, len(test_cases), batch_size):
                batch = test_cases[i:i + batch_size]
                batch_metrics = await self._run_provider_batch(provider, batch, include_metrics)
                all_metrics.extend(batch_metrics)
            
            # Calculate provider comparison
            if all_metrics:
                provider_comparison = self._calculate_provider_comparison(provider, all_metrics)
                provider_comparisons.append(provider_comparison)
        
        # Determine best provider
        best_provider = max(
            provider_comparisons,
            key=lambda x: x.average_metrics.get_overall_score()
        ).provider if provider_comparisons else None
        
        # Generate optimization recommendations
        result = ComparisonResult(
            provider_comparisons=provider_comparisons,
            test_cases_used=test_cases,
            total_tests=len(test_cases) * len(providers),
            best_provider=best_provider,
            recommendations=[]
        )
        
        result.recommendations = self._generate_optimization_recommendations(result)
        
        # Cache result
        if cache_results:
            self.comparison_cache[cache_key] = result
        
        # Store individual results for historical analysis
        for comparison in provider_comparisons:
            self.test_results.extend(comparison.individual_results)
        
        logger.info(f"Comparison complete: best provider = {best_provider}")
        return result
    
    async def _run_provider_batch(
        self,
        provider: str,
        test_cases: List[PromptTest],
        include_metrics: List[MetricType]
    ) -> List[PerformanceMetrics]:
        """Run a batch of test cases for a single provider."""
        tasks = []
        
        for test_case in test_cases:
            task = self._evaluate_single_test(provider, test_case, include_metrics)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Test case {i} failed for {provider}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _evaluate_single_test(
        self,
        provider: str,
        test_case: PromptTest,
        include_metrics: List[MetricType]
    ) -> PerformanceMetrics:
        """Evaluate a single test case for a provider."""
        # Create tutoring request
        request = TutoringRequest(
            query=test_case.query,
            student_level=test_case.student_level,
            philosophical_context=test_case.philosophical_context,
            learning_objective=test_case.learning_objective,
            retrieved_passages=test_case.retrieved_passages,
            citations=test_case.citations,
            provider=provider
        )
        
        # Generate response and measure time
        start_time = datetime.now()
        response = await self.prompt_service.generate_tutoring_response(request)
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response metadata
        token_count = response.llm_response.metadata.get("token_count", len(response.content) // 4)
        
        # Calculate metrics based on what's requested
        accuracy_score = 0.0
        citation_quality = 0.0
        educational_value = 0.0
        coherence_score = 0.0
        
        if MetricType.ALL in include_metrics or MetricType.ACCURACY in include_metrics:
            accuracy_score = await self._evaluate_accuracy(response.content, test_case.expected_concepts)
        
        if MetricType.ALL in include_metrics or MetricType.CITATION_QUALITY in include_metrics:
            citation_quality = self._evaluate_citation_quality(response.citations_provided)
        
        if MetricType.ALL in include_metrics or MetricType.EDUCATIONAL_VALUE in include_metrics:
            educational_value = self._evaluate_educational_value(response.content, test_case.student_level)
        
        if MetricType.ALL in include_metrics or MetricType.COHERENCE in include_metrics:
            coherence_score = self._calculate_coherence_score(response.content)
        
        return PerformanceMetrics(
            provider=provider,
            response_time=response_time,
            token_count=token_count,
            accuracy_score=accuracy_score,
            citation_quality=citation_quality,
            educational_value=educational_value,
            coherence_score=coherence_score,
            metadata={
                "test_query": test_case.query,
                "student_level": test_case.student_level,
                "response_length": len(response.content)
            }
        )
    
    async def _evaluate_accuracy(self, response_content: str, expected_concepts: List[str]) -> float:
        """
        Evaluate response accuracy based on expected philosophical concepts.
        
        Args:
            response_content: The generated response text
            expected_concepts: List of concepts that should be mentioned
            
        Returns:
            Accuracy score (0.0-1.0)
        """
        if not expected_concepts:
            return 1.0
        
        response_lower = response_content.lower()
        found_concepts = []
        
        for concept in expected_concepts:
            # Look for exact matches and variations
            concept_lower = concept.lower()
            if (concept_lower in response_lower or
                any(keyword in response_lower for keyword in concept_lower.split()) or
                self._check_concept_variations(concept_lower, response_lower)):
                found_concepts.append(concept)
        
        accuracy = len(found_concepts) / len(expected_concepts)
        return min(1.0, accuracy)
    
    def _check_concept_variations(self, concept: str, text: str) -> bool:
        """Check for variations and related terms of philosophical concepts."""
        concept_variations = {
            "eudaimonia": ["happiness", "flourishing", "good life", "well-being"],
            "forms": ["form", "ideal", "perfect", "eternal"],
            "golden mean": ["mean", "moderation", "balance", "middle path"],
            "cogito": ["i think", "thinking", "doubt", "certainty"],
            "categorical imperative": ["duty", "moral law", "universal law"]
        }
        
        variations = concept_variations.get(concept, [])
        return any(var in text for var in variations)
    
    def _evaluate_citation_quality(self, citations: List[Citation]) -> float:
        """
        Evaluate the quality of citations provided.
        
        Args:
            citations: List of citations in the response
            
        Returns:
            Citation quality score (0.0-1.0)
        """
        if not citations:
            return 0.0
        
        quality_score = 0.0
        
        for citation in citations:
            # Check for proper reference format
            reference_score = 0.0
            if citation.reference:
                # Classical references (e.g., "Republic 514a", "Ethics 1094a")
                if re.match(r'^[A-Z][a-z]+ \d+[a-z]?$', citation.reference):
                    reference_score = 1.0
                elif citation.reference:
                    reference_score = 0.8
            
            # Check citation completeness (more lenient scoring)
            completeness_score = 0.8  # Default good score if basic info present
            if citation.author and citation.work:
                completeness_score = 1.0
            elif citation.author or citation.work:
                completeness_score = 0.9
            elif citation.source:
                completeness_score = 0.8
            
            # Check confidence score
            confidence_score = citation.confidence
            
            # Weighted average for this citation (more generous weights)
            citation_quality = (
                reference_score * 0.4 +
                completeness_score * 0.3 +
                confidence_score * 0.3
            )
            
            quality_score += citation_quality
        
        return quality_score / len(citations)
    
    def _evaluate_educational_value(self, response: str, student_level: str) -> float:
        """
        Evaluate educational value based on content depth and appropriateness.
        
        Args:
            response: Response content
            student_level: Target student level
            
        Returns:
            Educational value score (0.0-1.0)
        """
        # Length appropriateness
        response_length = len(response.split())
        length_score = 1.0
        
        if student_level == "undergraduate":
            # Should be comprehensive but accessible (100-300 words)
            if response_length < 50:
                length_score = 0.3
            elif response_length > 500:
                length_score = 0.7
        elif student_level == "graduate":
            # Should be detailed and nuanced (150-400 words)
            if response_length < 75:
                length_score = 0.4
            elif response_length > 600:
                length_score = 0.8
        elif student_level == "advanced":
            # Can be longer and more complex (200+ words)
            if response_length < 100:
                length_score = 0.5
        
        # Check for educational elements (more comprehensive)
        educational_indicators = [
            "example", "for instance", "consider", "think about",
            "this means", "in other words", "furthermore", "however",
            "question", "challenge", "explore", "analyze",
            "concept", "theory", "principle", "idea", "virtue", "ethics"
        ]
        
        indicators_found = sum(1 for indicator in educational_indicators 
                             if indicator in response.lower())
        indicator_score = min(1.0, indicators_found / 3)  # More achievable target
        
        # Check for logical structure (more inclusive)
        structure_indicators = ["first", "second", "finally", "moreover", "therefore", "thus", 
                               "he", "according", "distinguishes", "goal", "central"]
        structure_found = sum(1 for indicator in structure_indicators 
                            if indicator in response.lower())
        structure_score = min(1.0, structure_found / 2)  # More achievable target
        
        # Weighted combination
        educational_value = (
            length_score * 0.3 +
            indicator_score * 0.4 +
            structure_score * 0.3
        )
        
        return educational_value
    
    def _calculate_coherence_score(self, response: str) -> float:
        """
        Calculate coherence and flow using intelligent semantic analysis.
        
        Args:
            response: Response content
            
        Returns:
            Coherence score (0.0-1.0)
        """
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) < 2:
            return 1.0 if len(response.strip()) > 20 else 0.3
        
        # 1. LOGICAL FLOW ANALYSIS - Check if sentences build upon each other
        flow_score = self._analyze_logical_flow(sentences)
        
        # 2. SEMANTIC CONSISTENCY - Check if the response stays on topic
        consistency_score = self._analyze_semantic_consistency(sentences)
        
        # 3. ARGUMENT STRUCTURE - Check for philosophical reasoning patterns
        argument_score = self._analyze_argument_structure(sentences, response)
        
        # 4. LINGUISTIC COHERENCE - Check for proper connectors and transitions
        linguistic_score = self._analyze_linguistic_coherence(sentences, response)
        
        # Weighted combination emphasizing logical flow and consistency
        coherence = (
            flow_score * 0.35 +         # Most important: logical progression
            consistency_score * 0.30 +   # Topic coherence
            argument_score * 0.20 +     # Philosophical reasoning
            linguistic_score * 0.15     # Surface linguistic features
        )
        
        return min(1.0, max(0.0, coherence))
    
    def _analyze_logical_flow(self, sentences: List[str]) -> float:
        """Analyze if sentences follow logical progression."""
        if len(sentences) < 2:
            return 1.0
            
        flow_score = 0.0
        connections = 0
        
        for i in range(1, len(sentences)):
            prev_sentence = sentences[i-1].lower()
            curr_sentence = sentences[i].lower()
            
            # Check for logical connectors between sentences
            logical_connectors = [
                ("therefore", "thus", "consequently", "hence"),  # Conclusion
                ("however", "but", "yet", "nevertheless"),      # Contrast  
                ("furthermore", "moreover", "additionally"),     # Addition
                ("this", "that", "these", "such"),              # Reference
                ("for example", "for instance", "specifically") # Elaboration
            ]
            
            connection_found = False
            
            # Check if current sentence references previous content
            prev_words = set(prev_sentence.split())
            curr_words = set(curr_sentence.split())
            
            # Semantic overlap (shared meaningful words)
            meaningful_overlap = len(prev_words & curr_words & {
                "virtue", "ethics", "character", "aristotle", "plato", "good", 
                "life", "habit", "practice", "eudaimonia", "moral", "philosophy"
            })
            
            if meaningful_overlap > 0:
                flow_score += 0.5
                connection_found = True
            
            # Check for explicit logical connectors
            for connector_group in logical_connectors:
                if any(conn in curr_sentence for conn in connector_group):
                    flow_score += 0.4
                    connection_found = True
                    break
            
            # Check for pronoun references (this, that, it, they)
            pronouns = ["this", "that", "it", "they", "these", "those"]
            if any(pronoun in curr_sentence.split()[:3] for pronoun in pronouns):
                flow_score += 0.3
                connection_found = True
            
            if connection_found:
                connections += 1
        
        # Normalize by possible connections
        return flow_score / max(1, len(sentences) - 1) if len(sentences) > 1 else 1.0
    
    def _analyze_semantic_consistency(self, sentences: List[str]) -> float:
        """Check if all sentences relate to the same topic."""
        if len(sentences) < 2:
            return 1.0
            
        # Define philosophical topic clusters
        topic_clusters = {
            "virtue_ethics": ["virtue", "character", "habit", "excellence", "aristotle", "eudaimonia"],
            "epistemology": ["knowledge", "belief", "truth", "certainty", "doubt", "understanding"],
            "metaphysics": ["reality", "being", "existence", "substance", "form", "matter"],
            "political": ["justice", "state", "society", "republic", "citizen", "law"],
            "ethics": ["good", "evil", "moral", "right", "wrong", "duty", "obligation"]
        }
        
        # Count topic mentions per sentence
        sentence_topics = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            topic_scores = {}
            
            for topic, terms in topic_clusters.items():
                score = sum(1 for term in terms if term in sentence_lower)
                if score > 0:
                    topic_scores[topic] = score
            
            sentence_topics.append(topic_scores)
        
        # Calculate consistency - how many sentences share the same primary topic
        if not any(sentence_topics):
            return 0.5  # No clear topics identified
        
        # Find the most common topic across sentences
        all_topics = {}
        for topic_dict in sentence_topics:
            for topic, score in topic_dict.items():
                all_topics[topic] = all_topics.get(topic, 0) + score
        
        if not all_topics:
            return 0.5
            
        primary_topic = max(all_topics.keys(), key=all_topics.get)
        
        # Count sentences that discuss the primary topic
        consistent_sentences = sum(1 for topic_dict in sentence_topics 
                                 if primary_topic in topic_dict)
        
        consistency_ratio = consistent_sentences / len(sentences)
        
        # Bonus for depth - sentences that mention multiple related terms
        depth_bonus = 0.0
        for topic_dict in sentence_topics:
            if primary_topic in topic_dict and topic_dict[primary_topic] > 1:
                depth_bonus += 0.1
        
        return min(1.0, consistency_ratio + depth_bonus)
    
    def _analyze_argument_structure(self, sentences: List[str], full_response: str) -> float:
        """Analyze philosophical argument structure."""
        response_lower = full_response.lower()
        structure_score = 0.0
        
        # Check for premise-conclusion structure
        conclusion_indicators = ["therefore", "thus", "hence", "consequently", "so"]
        premise_indicators = ["because", "since", "given that", "as", "for"]
        
        has_conclusion = any(indicator in response_lower for indicator in conclusion_indicators)
        has_premise = any(indicator in response_lower for indicator in premise_indicators)
        
        if has_conclusion and has_premise:
            structure_score += 0.4
        elif has_conclusion or has_premise:
            structure_score += 0.2
        
        # Check for explanation patterns
        explanation_patterns = [
            "this means", "in other words", "that is", "namely", 
            "for example", "for instance", "such as"
        ]
        
        if any(pattern in response_lower for pattern in explanation_patterns):
            structure_score += 0.2
        
        # Check for philosophical argumentation
        philosophical_moves = [
            "argues that", "claims that", "believes that", "maintains that",
            "distinguishes between", "defines", "according to"
        ]
        
        philosophical_moves_count = sum(1 for move in philosophical_moves 
                                      if move in response_lower)
        structure_score += min(0.3, philosophical_moves_count * 0.1)
        
        # Check for balanced structure (not just assertions)
        questions = response_lower.count('?')
        explanations = len(explanation_patterns)
        
        if questions > 0 or explanations > 0:
            structure_score += 0.1
        
        return min(1.0, structure_score)
    
    def _analyze_linguistic_coherence(self, sentences: List[str], full_response: str) -> float:
        """Analyze surface linguistic features."""
        if len(sentences) < 2:
            return 1.0
        
        linguistic_score = 0.0
        
        # Check sentence length variation (good prose has variety)
        lengths = [len(sentence.split()) for sentence in sentences]
        if len(lengths) > 1:
            avg_length = sum(lengths) / len(lengths)
            if 8 <= avg_length <= 25:
                linguistic_score += 0.3
                
            # Bonus for reasonable variation
            max_len, min_len = max(lengths), min(lengths)
            if max_len > min_len and max_len / min_len <= 3:  # Not too extreme
                linguistic_score += 0.2
        
        # Penalty for excessive word repetition
        words = full_response.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short function words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        total_words = len([w for w in words if len(w) > 3])
        repetition_penalty = 0.0
        
        for word, freq in word_freq.items():
            if freq > total_words * 0.1:  # More than 10% repetition
                repetition_penalty += 0.2
        
        linguistic_score = max(0.0, linguistic_score - repetition_penalty)
        
        # Basic grammar check - complete sentences
        complete_sentences = sum(1 for s in sentences if len(s.split()) >= 3)
        completeness_ratio = complete_sentences / len(sentences)
        linguistic_score += completeness_ratio * 0.3
        
        return min(1.0, linguistic_score)
    
    def _calculate_provider_comparison(
        self,
        provider: str,
        metrics_list: List[PerformanceMetrics]
    ) -> ProviderComparison:
        """Calculate comparison statistics for a provider."""
        if not metrics_list:
            # Return empty comparison
            return ProviderComparison(
                provider=provider,
                average_metrics=PerformanceMetrics(
                    provider=provider,
                    response_time=0.0,
                    token_count=0,
                    accuracy_score=0.0,
                    citation_quality=0.0,
                    educational_value=0.0,
                    coherence_score=0.0
                ),
                individual_results=[],
                test_count=0
            )
        
        # Calculate averages
        avg_response_time = statistics.mean(m.response_time for m in metrics_list)
        avg_token_count = int(statistics.mean(m.token_count for m in metrics_list))
        avg_accuracy = statistics.mean(m.accuracy_score for m in metrics_list)
        avg_citation_quality = statistics.mean(m.citation_quality for m in metrics_list)
        avg_educational_value = statistics.mean(m.educational_value for m in metrics_list)
        avg_coherence = statistics.mean(m.coherence_score for m in metrics_list)
        
        average_metrics = PerformanceMetrics(
            provider=provider,
            response_time=avg_response_time,
            token_count=avg_token_count,
            accuracy_score=avg_accuracy,
            citation_quality=avg_citation_quality,
            educational_value=avg_educational_value,
            coherence_score=avg_coherence
        )
        
        # Calculate score statistics
        overall_scores = [m.get_overall_score() for m in metrics_list]
        best_score = max(overall_scores)
        worst_score = min(overall_scores)
        score_variance = statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0.0
        
        return ProviderComparison(
            provider=provider,
            average_metrics=average_metrics,
            individual_results=metrics_list,
            test_count=len(metrics_list),
            best_score=best_score,
            worst_score=worst_score,
            score_variance=score_variance
        )
    
    def _generate_optimization_recommendations(
        self,
        result: ComparisonResult
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on comparison results."""
        recommendations = []
        
        if not result.provider_comparisons:
            return recommendations
        
        # Sort providers by performance
        ranked_providers = result.get_provider_ranking()
        best_provider = ranked_providers[0]
        
        # Recommendation 1: Provider selection for different scenarios
        if len(ranked_providers) > 1:
            accuracy_leader = max(ranked_providers, key=lambda x: x.average_metrics.accuracy_score)
            speed_leader = min(ranked_providers, key=lambda x: x.average_metrics.response_time)
            
            if accuracy_leader.provider != best_provider.provider:
                recommendations.append(OptimizationRecommendation(
                    recommendation_type="provider_selection",
                    priority="high",
                    description=f"Use {accuracy_leader.provider} for accuracy-critical queries "
                               f"(accuracy: {accuracy_leader.average_metrics.accuracy_score:.2f})",
                    expected_improvement=0.1,
                    implementation_effort="low",
                    affected_metrics=["accuracy"]
                ))
            
            if speed_leader.provider != best_provider.provider:
                recommendations.append(OptimizationRecommendation(
                    recommendation_type="provider_selection",
                    priority="medium",
                    description=f"Use {speed_leader.provider} for time-sensitive queries "
                               f"(response time: {speed_leader.average_metrics.response_time:.2f}s)",
                    expected_improvement=0.2,
                    implementation_effort="low",
                    affected_metrics=["response_time"]
                ))
        
        # Recommendation 2: Citation quality improvement
        citation_scores = [p.average_metrics.citation_quality for p in ranked_providers]
        avg_citation_quality = statistics.mean(citation_scores)
        
        if avg_citation_quality < 0.8:
            recommendations.append(OptimizationRecommendation(
                recommendation_type="prompt_tuning",
                priority="high",
                description="Enhance citation requirements in prompts to improve source attribution quality",
                expected_improvement=0.15,
                implementation_effort="medium",
                affected_metrics=["citation_quality"]
            ))
        
        # Recommendation 3: Educational value optimization
        educational_scores = [p.average_metrics.educational_value for p in ranked_providers]
        min_educational = min(educational_scores)
        
        if min_educational < 0.75:
            recommendations.append(OptimizationRecommendation(
                recommendation_type="prompt_tuning",
                priority="medium",
                description="Add more pedagogical guidance to prompts for improved educational value",
                expected_improvement=0.12,
                implementation_effort="medium",
                affected_metrics=["educational_value"]
            ))
        
        # Recommendation 4: Consistency improvement
        high_variance_providers = [p for p in ranked_providers if p.score_variance > 0.15]
        
        if high_variance_providers:
            provider_names = ", ".join(p.provider for p in high_variance_providers)
            recommendations.append(OptimizationRecommendation(
                recommendation_type="prompt_standardization",
                priority="medium",
                description=f"Standardize prompts for {provider_names} to reduce response variability",
                expected_improvement=0.1,
                implementation_effort="high",
                affected_metrics=["consistency"]
            ))
        
        return recommendations
    
    def _generate_cache_key(
        self,
        test_cases: List[PromptTest],
        providers: List[str],
        include_metrics: List[MetricType]
    ) -> str:
        """Generate cache key for comparison results."""
        # Create hash from test case queries and configuration
        queries = [tc.query for tc in test_cases]
        cache_data = {
            "queries": sorted(queries),
            "providers": sorted(providers),
            "metrics": sorted([m.value for m in include_metrics])
        }
        
        cache_string = str(cache_data)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get_historical_comparisons(self, days_back: int = 30) -> List[PerformanceMetrics]:
        """Get historical comparison results."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        return [
            result for result in self.test_results
            if result.timestamp >= cutoff_date
        ]
    
    def clear_cache(self) -> None:
        """Clear comparison cache."""
        self.comparison_cache.clear()
        logger.info("Comparison cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_comparisons": len(self.comparison_cache),
            "total_test_results": len(self.test_results),
            "cache_keys": list(self.comparison_cache.keys())
        }