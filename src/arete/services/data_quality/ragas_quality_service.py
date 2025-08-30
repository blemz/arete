"""
RAGAS-based Quality Assessment Service for Arete Graph-RAG System.

This service integrates the RAGAS (Retrieval-Augmented Generation Assessment)
framework to provide comprehensive evaluation of RAG system quality including:
- Faithfulness: How grounded the answer is in the given context
- Answer Relevancy: How relevant the answer is to the question
- Context Precision: How precise the retrieved context is
- Context Recall: How complete the retrieved context is
- Citation Accuracy: How accurate the citations are to source material
- Philosophical Domain Metrics: Domain-specific quality assessments

The service is designed specifically for philosophical tutoring applications
with classical texts from Plato, Aristotle, Augustine, Aquinas, etc.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, field
import statistics

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, field_validator

try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness, 
        answer_relevancy, 
        context_precision, 
        context_recall,
        context_relevancy
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    # Mock classes for testing without RAGAS installed
    class MockMetric:
        pass
    faithfulness = answer_relevancy = context_precision = context_recall = context_relevancy = MockMetric()
    
    def evaluate(*args, **kwargs):
        return pd.DataFrame({
            'faithfulness': [0.8],
            'answer_relevancy': [0.85], 
            'context_precision': [0.75],
            'context_recall': [0.82]
        })

from arete.config import Settings, get_settings
from arete.models.base import BaseModel as AreteBaseModel
from arete.models.citation import Citation
from arete.models.chunk import Chunk

logger = logging.getLogger(__name__)


class QualityMetricType(str, Enum):
    """Types of quality metrics available."""
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy" 
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    CITATION_ACCURACY = "citation_accuracy"
    ARGUMENT_COHERENCE = "argument_coherence"
    CONCEPTUAL_CLARITY = "conceptual_clarity"
    TEXTUAL_FIDELITY = "textual_fidelity"
    DIALOGICAL_QUALITY = "dialogical_quality"


class QualityThresholds(BaseModel):
    """Quality thresholds for assessment validation."""
    
    faithfulness_min: float = Field(default=0.7, ge=0.0, le=1.0)
    answer_relevancy_min: float = Field(default=0.7, ge=0.0, le=1.0)
    context_precision_min: float = Field(default=0.6, ge=0.0, le=1.0)
    context_recall_min: float = Field(default=0.6, ge=0.0, le=1.0)
    citation_accuracy_min: float = Field(default=0.8, ge=0.0, le=1.0)
    overall_quality_min: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Philosophical domain-specific thresholds
    argument_coherence_min: float = Field(default=0.75, ge=0.0, le=1.0)
    conceptual_clarity_min: float = Field(default=0.7, ge=0.0, le=1.0)
    textual_fidelity_min: float = Field(default=0.8, ge=0.0, le=1.0)
    dialogical_quality_min: float = Field(default=0.65, ge=0.0, le=1.0)


class EvaluationResult(AreteBaseModel):
    """Results from a quality evaluation assessment."""
    
    query_id: str = Field(..., description="Unique identifier for the evaluated query")
    question: str = Field(..., description="The question that was evaluated")
    
    # Core RAGAS metrics
    faithfulness_score: float = Field(..., ge=0.0, le=1.0, description="Faithfulness to source material")
    answer_relevancy_score: float = Field(..., ge=0.0, le=1.0, description="Relevance of answer to question")
    context_precision_score: float = Field(..., ge=0.0, le=1.0, description="Precision of retrieved context")
    context_recall_score: float = Field(..., ge=0.0, le=1.0, description="Completeness of retrieved context")
    
    # Extended metrics
    citation_accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy of citations")
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality composite score")
    
    # Philosophical domain metrics
    argument_coherence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    conceptual_clarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    textual_fidelity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    dialogical_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Evaluation metadata
    evaluation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_duration_ms: Optional[float] = Field(None, description="Time taken for evaluation in milliseconds")
    
    def calculate_overall_score(self) -> float:
        """Calculate overall quality score from individual metrics."""
        # Weighted average of core metrics
        core_metrics = [
            (self.faithfulness_score, 0.3),
            (self.answer_relevancy_score, 0.25), 
            (self.context_precision_score, 0.2),
            (self.context_recall_score, 0.25)
        ]
        
        weighted_sum = sum(score * weight for score, weight in core_metrics)
        
        # Add citation bonus if available
        if self.citation_accuracy_score is not None:
            weighted_sum = weighted_sum * 0.9 + self.citation_accuracy_score * 0.1
            
        return round(weighted_sum, 3)


class QualityMetrics(BaseModel):
    """Configuration for quality metrics calculation."""
    
    enabled_metrics: List[QualityMetricType] = Field(
        default=[
            QualityMetricType.FAITHFULNESS,
            QualityMetricType.ANSWER_RELEVANCY,
            QualityMetricType.CONTEXT_PRECISION, 
            QualityMetricType.CONTEXT_RECALL,
            QualityMetricType.CITATION_ACCURACY
        ]
    )
    
    # Metric weights for overall score calculation
    metric_weights: Dict[QualityMetricType, float] = Field(
        default={
            QualityMetricType.FAITHFULNESS: 0.3,
            QualityMetricType.ANSWER_RELEVANCY: 0.25,
            QualityMetricType.CONTEXT_PRECISION: 0.2,
            QualityMetricType.CONTEXT_RECALL: 0.25
        }
    )
    
    # Custom metric functions
    custom_metrics: Dict[str, Callable] = Field(default_factory=dict, exclude=True)


@dataclass
class QualityTrendAnalysis:
    """Analysis of quality trends over time."""
    metric_trends: Dict[str, float]  # Slope of trend line for each metric
    overall_improvement: bool
    quality_stability: float  # Variance in quality scores
    recommendations: List[str]
    analysis_period_days: int


class PhilosophicalEvaluationDataset:
    """Manager for philosophical evaluation datasets."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_dataset(
        self,
        questions: List[str],
        contexts: List[List[str]],
        answers: List[str],
        ground_truths: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Create evaluation dataset from components."""
        if len(questions) != len(contexts) or len(questions) != len(answers):
            raise ValueError("Questions, contexts, and answers must have same length")
            
        dataset_dict = {
            'question': questions,
            'contexts': contexts,
            'answer': answers
        }
        
        if ground_truths:
            dataset_dict['ground_truth'] = ground_truths
            
        return pd.DataFrame(dataset_dict)
    
    def validate_dataset(self, dataset: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate dataset structure and content."""
        errors = []
        
        required_columns = ['question', 'contexts', 'answer']
        for col in required_columns:
            if col not in dataset.columns:
                errors.append(f"Missing required column: {col}")
        
        if len(dataset) == 0:
            errors.append("Dataset is empty")
            
        # Validate data types and content
        for idx, row in dataset.iterrows():
            if pd.isna(row.get('question')) or not row.get('question'):
                errors.append(f"Empty question at row {idx}")
            
            if not isinstance(row.get('contexts'), list) or len(row.get('contexts', [])) == 0:
                errors.append(f"Invalid or empty contexts at row {idx}")
                
            if pd.isna(row.get('answer')) or not row.get('answer'):
                errors.append(f"Empty answer at row {idx}")
        
        return len(errors) == 0, errors
    
    def augment_dataset(self, dataset: pd.DataFrame, augmentation_factor: int = 2) -> pd.DataFrame:
        """Augment dataset with variations (placeholder implementation)."""
        # In a real implementation, this could:
        # - Paraphrase questions
        # - Add synonyms
        # - Create variations of contexts
        # For now, just repeat the dataset
        return pd.concat([dataset] * augmentation_factor, ignore_index=True)


class RAGASQualityService:
    """Service for RAGAS-based quality assessment of RAG systems."""
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        thresholds: Optional[QualityThresholds] = None,
        metrics_config: Optional[QualityMetrics] = None
    ):
        """Initialize RAGAS quality service."""
        self.settings = settings or get_settings()
        self.thresholds = thresholds or QualityThresholds()
        self.metrics = metrics_config or QualityMetrics()
        self.logger = logging.getLogger(__name__)
        
        # Warn if RAGAS is not available
        if not RAGAS_AVAILABLE:
            self.logger.warning("RAGAS library not available. Install with: pip install ragas")
        
        # Initialize custom metrics
        self._initialize_philosophical_metrics()
    
    def _initialize_philosophical_metrics(self):
        """Initialize philosophical domain-specific metrics."""
        
        def argument_coherence_metric(response: str, contexts: List[str]) -> float:
            """Evaluate logical coherence of philosophical arguments."""
            coherence_indicators = [
                "therefore", "thus", "hence", "consequently", 
                "because", "since", "follows that", "implies"
            ]
            response_lower = response.lower()
            coherence_score = sum(1 for indicator in coherence_indicators 
                                if indicator in response_lower)
            return min(coherence_score / 3.0, 1.0)  # Normalize to 0-1
        
        def conceptual_clarity_metric(response: str, contexts: List[str]) -> float:
            """Evaluate clarity of philosophical concepts."""
            clarity_indicators = [
                "define", "definition", "means", "refers to", 
                "understand as", "concept of", "notion of"
            ]
            response_lower = response.lower()
            clarity_score = sum(1 for indicator in clarity_indicators 
                              if indicator in response_lower)
            return min(clarity_score / 2.0, 1.0)
        
        def textual_fidelity_metric(response: str, contexts: List[str]) -> float:
            """Evaluate fidelity to original philosophical texts."""
            if not contexts:
                return 0.0
                
            # Simple overlap measure (in practice, would use more sophisticated methods)
            response_words = set(response.lower().split())
            context_words = set()
            for context in contexts:
                context_words.update(context.lower().split())
            
            if not context_words:
                return 0.0
                
            overlap = len(response_words.intersection(context_words))
            return min(overlap / len(response_words), 1.0)
        
        def dialogical_quality_metric(response: str, contexts: List[str]) -> float:
            """Evaluate engagement with alternative perspectives."""
            dialogue_indicators = [
                "however", "although", "on the other hand", "critics argue",
                "alternatively", "some might say", "objection", "counterargument"
            ]
            response_lower = response.lower()
            dialogue_score = sum(1 for indicator in dialogue_indicators 
                                if indicator in response_lower)
            return min(dialogue_score / 2.0, 1.0)
        
        # Register philosophical metrics
        self.metrics.custom_metrics.update({
            "argument_coherence": argument_coherence_metric,
            "conceptual_clarity": conceptual_clarity_metric,
            "textual_fidelity": textual_fidelity_metric,
            "dialogical_quality": dialogical_quality_metric
        })
    
    def get_quality_thresholds(self) -> QualityThresholds:
        """Get configured quality thresholds."""
        return self.thresholds
    
    def get_available_metrics(self) -> List[str]:
        """Get list of available quality metrics."""
        standard_metrics = [metric.value for metric in self.metrics.enabled_metrics]
        custom_metrics = list(self.metrics.custom_metrics.keys())
        return standard_metrics + custom_metrics
    
    def register_custom_metric(self, name: str, metric_function: Callable) -> None:
        """Register a custom quality metric."""
        self.metrics.custom_metrics[name] = metric_function
        self.logger.info(f"Registered custom metric: {name}")
    
    async def evaluate_single_query(
        self,
        question: str,
        contexts: List[str],
        answer: str,
        ground_truth: Optional[str] = None,
        query_id: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate quality of a single query-answer pair."""
        start_time = datetime.now()
        
        if not query_id:
            query_id = str(uuid4())
        
        try:
            # Prepare data for RAGAS evaluation
            eval_data = {
                'question': [question],
                'contexts': [contexts], 
                'answer': [answer]
            }
            
            if ground_truth:
                eval_data['ground_truth'] = [ground_truth]
            
            eval_dataset = pd.DataFrame(eval_data)
            
            # Run RAGAS evaluation
            ragas_metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
            result = evaluate(eval_dataset, metrics=ragas_metrics)
            
            # Extract scores
            faithfulness_score = float(result['faithfulness'].iloc[0])
            answer_relevancy_score = float(result['answer_relevancy'].iloc[0])
            context_precision_score = float(result['context_precision'].iloc[0])
            context_recall_score = float(result['context_recall'].iloc[0])
            
            # Calculate philosophical domain metrics
            philosophical_scores = self.evaluate_philosophical_quality({
                "response": answer,
                "contexts": contexts
            })
            
            # Create evaluation result
            evaluation_result = EvaluationResult(
                query_id=query_id,
                question=question,
                faithfulness_score=faithfulness_score,
                answer_relevancy_score=answer_relevancy_score,
                context_precision_score=context_precision_score,
                context_recall_score=context_recall_score,
                argument_coherence_score=philosophical_scores.get('argument_coherence_score'),
                conceptual_clarity_score=philosophical_scores.get('conceptual_clarity_score'),
                textual_fidelity_score=philosophical_scores.get('textual_fidelity_score'),
                dialogical_quality_score=philosophical_scores.get('dialogical_quality_score'),
                evaluation_duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
            # Calculate overall score
            evaluation_result.overall_quality_score = evaluation_result.calculate_overall_score()
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"Error evaluating query {query_id}: {str(e)}")
            raise
    
    async def evaluate_batch(
        self, 
        evaluation_data: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """Evaluate quality of multiple query-answer pairs."""
        results = []
        
        for i, data in enumerate(evaluation_data):
            try:
                result = await self.evaluate_single_query(
                    question=data["question"],
                    contexts=data["contexts"],
                    answer=data["answer"],
                    ground_truth=data.get("ground_truth"),
                    query_id=data.get("query_id", f"batch_{i}")
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error evaluating batch item {i}: {str(e)}")
                continue
        
        return results
    
    def evaluate_citation_accuracy(
        self, 
        citations: List[Citation], 
        source_texts: List[str]
    ) -> float:
        """Evaluate accuracy of citations against source texts."""
        if not citations or not source_texts:
            raise ValueError("Citations and source texts cannot be empty")
        
        if not isinstance(citations, list) or not isinstance(source_texts, list):
            raise TypeError("Citations and source_texts must be lists")
        
        accurate_citations = 0
        total_citations = len(citations)
        
        for citation in citations:
            citation_text = citation.text.lower()
            
            # Check if citation text appears in any source text
            for source_text in source_texts:
                if citation_text in source_text.lower():
                    accurate_citations += 1
                    break
        
        return accurate_citations / total_citations if total_citations > 0 else 0.0
    
    def evaluate_philosophical_quality(
        self, 
        philosophical_content: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate philosophical domain-specific quality metrics."""
        response = philosophical_content.get("response", "")
        contexts = philosophical_content.get("contexts", [])
        
        scores = {}
        
        for metric_name, metric_function in self.metrics.custom_metrics.items():
            try:
                score = metric_function(response, contexts)
                scores[f"{metric_name}_score"] = score
            except Exception as e:
                self.logger.error(f"Error computing {metric_name}: {str(e)}")
                scores[f"{metric_name}_score"] = 0.0
        
        return scores
    
    def validate_against_thresholds(
        self, 
        result: EvaluationResult
    ) -> Tuple[List[str], List[str]]:
        """Validate evaluation result against quality thresholds."""
        passed_metrics = []
        failed_metrics = []
        
        threshold_checks = [
            ("faithfulness", result.faithfulness_score, self.thresholds.faithfulness_min),
            ("answer_relevancy", result.answer_relevancy_score, self.thresholds.answer_relevancy_min),
            ("context_precision", result.context_precision_score, self.thresholds.context_precision_min),
            ("context_recall", result.context_recall_score, self.thresholds.context_recall_min),
            ("overall_quality", result.overall_quality_score, self.thresholds.overall_quality_min),
        ]
        
        # Add optional metrics if present
        if result.citation_accuracy_score is not None:
            threshold_checks.append(
                ("citation_accuracy", result.citation_accuracy_score, self.thresholds.citation_accuracy_min)
            )
        
        if result.argument_coherence_score is not None:
            threshold_checks.append(
                ("argument_coherence", result.argument_coherence_score, self.thresholds.argument_coherence_min)
            )
        
        for metric_name, score, threshold in threshold_checks:
            if score >= threshold:
                passed_metrics.append(metric_name)
            else:
                failed_metrics.append(metric_name)
        
        return passed_metrics, failed_metrics
    
    def analyze_quality_trends(
        self, 
        historical_results: List[EvaluationResult]
    ) -> QualityTrendAnalysis:
        """Analyze quality trends over time."""
        if len(historical_results) < 2:
            return QualityTrendAnalysis(
                metric_trends={},
                overall_improvement=False,
                quality_stability=0.0,
                recommendations=["Need more data points for trend analysis"],
                analysis_period_days=0
            )
        
        # Sort by timestamp
        sorted_results = sorted(historical_results, key=lambda x: x.evaluation_timestamp)
        
        # Calculate trends for each metric
        metric_trends = {}
        
        # Faithfulness trend
        faithfulness_scores = [r.faithfulness_score for r in sorted_results]
        metric_trends['faithfulness_trend'] = self._calculate_trend(faithfulness_scores)
        
        # Answer relevancy trend
        relevancy_scores = [r.answer_relevancy_score for r in sorted_results]
        metric_trends['answer_relevancy_trend'] = self._calculate_trend(relevancy_scores)
        
        # Overall quality trend
        overall_scores = [r.overall_quality_score for r in sorted_results]
        overall_trend = self._calculate_trend(overall_scores)
        metric_trends['overall_quality_trend'] = overall_trend
        
        # Determine overall improvement
        overall_improvement = overall_trend > 0.01  # Improvement threshold
        
        # Calculate quality stability (inverse of variance)
        quality_variance = statistics.variance(overall_scores) if len(overall_scores) > 1 else 0
        quality_stability = max(0, 1 - quality_variance)
        
        # Generate recommendations
        recommendations = self._generate_quality_recommendations(metric_trends, overall_improvement)
        
        # Calculate analysis period
        period_start = sorted_results[0].evaluation_timestamp
        period_end = sorted_results[-1].evaluation_timestamp
        analysis_period_days = (period_end - period_start).days
        
        return QualityTrendAnalysis(
            metric_trends=metric_trends,
            overall_improvement=overall_improvement,
            quality_stability=quality_stability,
            recommendations=recommendations,
            analysis_period_days=analysis_period_days
        )
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """Calculate trend slope for a series of scores."""
        if len(scores) < 2:
            return 0.0
        
        n = len(scores)
        x = list(range(n))
        y = scores
        
        # Simple linear regression slope
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
    
    def _generate_quality_recommendations(
        self, 
        metric_trends: Dict[str, float], 
        overall_improvement: bool
    ) -> List[str]:
        """Generate recommendations based on quality trends."""
        recommendations = []
        
        if not overall_improvement:
            recommendations.append("Overall quality is declining. Consider reviewing RAG pipeline components.")
        
        if metric_trends.get('faithfulness_trend', 0) < -0.01:
            recommendations.append("Faithfulness is declining. Review source document quality and retrieval accuracy.")
        
        if metric_trends.get('answer_relevancy_trend', 0) < -0.01:
            recommendations.append("Answer relevancy is declining. Consider improving question understanding and response generation.")
        
        if not recommendations:
            recommendations.append("Quality metrics are stable or improving. Continue current practices.")
        
        return recommendations
    
    async def setup_continuous_monitoring(
        self, 
        monitoring_config: Dict[str, Any]
    ) -> 'QualityMonitor':
        """Set up continuous quality monitoring."""
        from .quality_monitor import QualityMonitor
        
        monitor = QualityMonitor(
            quality_service=self,
            config=monitoring_config
        )
        
        return monitor
    
    async def evaluate_rag_pipeline_output(
        self,
        query: str,
        retrieved_contexts: List[Dict[str, Any]],
        generated_response: str
    ) -> EvaluationResult:
        """Evaluate RAG pipeline output end-to-end."""
        # Extract context texts from retrieval results
        contexts = [ctx.get("text", "") for ctx in retrieved_contexts]
        
        # Evaluate using standard pipeline
        return await self.evaluate_single_query(
            question=query,
            contexts=contexts,
            answer=generated_response
        )
    
    def generate_quality_report(
        self, 
        results: List[EvaluationResult]
    ) -> Dict[str, Any]:
        """Generate comprehensive quality assessment report."""
        if not results:
            return {
                "summary_statistics": {},
                "metric_distributions": {},
                "quality_insights": [],
                "recommendations": []
            }
        
        # Calculate summary statistics
        faithfulness_scores = [r.faithfulness_score for r in results]
        relevancy_scores = [r.answer_relevancy_score for r in results]
        precision_scores = [r.context_precision_score for r in results]
        recall_scores = [r.context_recall_score for r in results]
        overall_scores = [r.overall_quality_score for r in results]
        
        summary_stats = {
            "total_evaluations": len(results),
            "average_overall_quality": statistics.mean(overall_scores),
            "quality_std_dev": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0,
            "metric_averages": {
                "faithfulness": statistics.mean(faithfulness_scores),
                "answer_relevancy": statistics.mean(relevancy_scores),
                "context_precision": statistics.mean(precision_scores),
                "context_recall": statistics.mean(recall_scores)
            }
        }
        
        # Calculate metric distributions
        metric_distributions = {
            "faithfulness_distribution": self._calculate_distribution(faithfulness_scores),
            "relevancy_distribution": self._calculate_distribution(relevancy_scores),
            "precision_distribution": self._calculate_distribution(precision_scores),
            "recall_distribution": self._calculate_distribution(recall_scores)
        }
        
        # Generate insights
        quality_insights = self._generate_quality_insights(summary_stats, results)
        
        # Generate recommendations
        recommendations = self._generate_report_recommendations(summary_stats, results)
        
        return {
            "summary_statistics": summary_stats,
            "metric_distributions": metric_distributions,
            "quality_insights": quality_insights,
            "recommendations": recommendations,
            "report_generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_distribution(self, scores: List[float]) -> Dict[str, float]:
        """Calculate distribution statistics for scores."""
        if not scores:
            return {}
            
        return {
            "min": min(scores),
            "max": max(scores),
            "median": statistics.median(scores),
            "q25": statistics.quantiles(scores, n=4)[0] if len(scores) > 1 else scores[0],
            "q75": statistics.quantiles(scores, n=4)[2] if len(scores) > 1 else scores[0]
        }
    
    def _generate_quality_insights(
        self, 
        summary_stats: Dict[str, Any], 
        results: List[EvaluationResult]
    ) -> List[str]:
        """Generate insights from quality analysis."""
        insights = []
        
        avg_quality = summary_stats["average_overall_quality"]
        
        if avg_quality >= 0.85:
            insights.append("Excellent overall quality achieved across evaluations")
        elif avg_quality >= 0.75:
            insights.append("Good overall quality with room for targeted improvements")
        elif avg_quality >= 0.65:
            insights.append("Moderate quality - significant improvements needed")
        else:
            insights.append("Low quality detected - comprehensive review required")
        
        # Metric-specific insights
        metrics = summary_stats["metric_averages"]
        
        if metrics["faithfulness"] < 0.7:
            insights.append("Faithfulness below threshold - review source material accuracy")
        
        if metrics["answer_relevancy"] < 0.7:
            insights.append("Answer relevancy below threshold - improve response targeting")
        
        return insights
    
    def _generate_report_recommendations(
        self, 
        summary_stats: Dict[str, Any], 
        results: List[EvaluationResult]
    ) -> List[str]:
        """Generate recommendations from quality report."""
        recommendations = []
        
        avg_quality = summary_stats["average_overall_quality"]
        
        if avg_quality < 0.75:
            recommendations.append("Implement systematic quality improvement process")
        
        if summary_stats["quality_std_dev"] > 0.15:
            recommendations.append("High quality variance detected - standardize evaluation process")
        
        # Check for consistent patterns
        low_quality_count = sum(1 for r in results if r.overall_quality_score < 0.7)
        if low_quality_count / len(results) > 0.3:
            recommendations.append("Over 30% of evaluations below quality threshold - urgent attention required")
        
        return recommendations