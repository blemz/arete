"""
Comprehensive Data Quality Pipeline Orchestration for Arete Graph-RAG System.

This module provides the main orchestration layer for all data quality validation,
assessment, and monitoring activities. It coordinates RAGAS evaluation, duplicate
detection, citation validation, and quality monitoring into a unified pipeline.

Components:
- DataQualityPipeline: Main orchestration service
- QualityAssessmentReport: Comprehensive quality assessment results
- QualityValidationRules: Configurable validation rules and thresholds
- QualityPipelineConfig: Configuration management for pipeline execution
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict

from .ragas_quality_service import (
    RAGASQualityService, 
    EvaluationResult, 
    QualityThresholds,
    QualityMetrics
)
from .duplicate_detection_service import (
    DuplicateDetectionService,
    DuplicateResult,
    DeduplicationResult,
    SimilarityMetrics,
    DuplicationStrategy
)
from .quality_monitor import (
    QualityMonitor,
    QualityAlert,
    MonitoringStats,
    AlertSeverity
)

from arete.models.document import Document
from arete.models.chunk import Chunk
from arete.models.citation import Citation


class QualityAssessmentLevel(str, Enum):
    """Quality assessment levels for different validation depths."""
    BASIC = "basic"           # Essential validation only
    STANDARD = "standard"     # Full RAGAS + duplicate detection
    COMPREHENSIVE = "comprehensive"  # All validations + monitoring
    RESEARCH = "research"     # Maximum accuracy for research use


class ValidationStatus(str, Enum):
    """Validation status for quality pipeline results."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class QualityAssessmentReport(BaseModel):
    """Comprehensive quality assessment report from data quality pipeline."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Report metadata
    assessment_id: str = Field(..., description="Unique assessment identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assessment_level: QualityAssessmentLevel = Field(..., description="Level of assessment performed")
    
    # RAGAS evaluation results
    ragas_results: Optional[EvaluationResult] = Field(None, description="RAGAS evaluation results")
    ragas_status: ValidationStatus = Field(ValidationStatus.SKIPPED, description="RAGAS validation status")
    
    # Duplicate detection results
    duplicate_results: List[DuplicateResult] = Field(default_factory=list, description="Detected duplicates")
    deduplication_summary: Optional[DeduplicationResult] = Field(None, description="Deduplication summary")
    duplicate_status: ValidationStatus = Field(ValidationStatus.SKIPPED, description="Duplicate detection status")
    
    # Citation validation results
    citation_accuracy: Optional[float] = Field(None, description="Citation accuracy score", ge=0.0, le=1.0)
    citation_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Citation validation issues")
    citation_status: ValidationStatus = Field(ValidationStatus.SKIPPED, description="Citation validation status")
    
    # Overall quality metrics
    overall_quality_score: Optional[float] = Field(None, description="Overall quality score", ge=0.0, le=1.0)
    quality_grade: Optional[str] = Field(None, description="Quality grade (A, B, C, D, F)")
    validation_summary: Dict[str, Any] = Field(default_factory=dict, description="Validation summary statistics")
    
    # Performance metrics
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    items_processed: int = Field(0, description="Number of items processed")
    
    # Alerts and recommendations
    quality_alerts: List[QualityAlert] = Field(default_factory=list, description="Quality alerts generated")
    recommendations: List[str] = Field(default_factory=list, description="Quality improvement recommendations")
    
    def calculate_overall_score(self) -> float:
        """Calculate overall quality score from component scores."""
        scores = []
        weights = []
        
        if self.ragas_results and self.ragas_results.overall_quality_score:
            scores.append(self.ragas_results.overall_quality_score)
            weights.append(0.5)  # RAGAS gets 50% weight
        
        if self.citation_accuracy is not None:
            scores.append(self.citation_accuracy)
            weights.append(0.3)  # Citations get 30% weight
        
        # Duplicate penalty (reduce score based on duplicate rate)
        if self.deduplication_summary:
            duplicate_rate = len(self.deduplication_summary.removed_items) / (
                len(self.deduplication_summary.kept_items) + len(self.deduplication_summary.removed_items)
            ) if (self.deduplication_summary.kept_items or self.deduplication_summary.removed_items) else 0.0
            duplicate_score = max(0.0, 1.0 - duplicate_rate)
            scores.append(duplicate_score)
            weights.append(0.2)  # Duplicates get 20% weight
        
        if not scores:
            return 0.0
        
        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        self.overall_quality_score = overall_score
        return overall_score
    
    def assign_quality_grade(self) -> str:
        """Assign letter grade based on overall quality score."""
        if self.overall_quality_score is None:
            self.calculate_overall_score()
        
        score = self.overall_quality_score or 0.0
        
        if score >= 0.9:
            grade = "A"
        elif score >= 0.8:
            grade = "B" 
        elif score >= 0.7:
            grade = "C"
        elif score >= 0.6:
            grade = "D"
        else:
            grade = "F"
        
        self.quality_grade = grade
        return grade
    
    def add_recommendation(self, recommendation: str):
        """Add a quality improvement recommendation."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get a summary dictionary for reporting."""
        return {
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "assessment_level": self.assessment_level,
            "overall_score": self.overall_quality_score,
            "quality_grade": self.quality_grade,
            "items_processed": self.items_processed,
            "processing_time": self.processing_time,
            "validation_status": {
                "ragas": self.ragas_status,
                "duplicates": self.duplicate_status,
                "citations": self.citation_status
            },
            "alerts_count": len(self.quality_alerts),
            "recommendations_count": len(self.recommendations)
        }


class QualityValidationRules(BaseModel):
    """Configurable validation rules and thresholds for quality assessment."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # RAGAS thresholds
    min_faithfulness: float = Field(0.7, description="Minimum faithfulness score", ge=0.0, le=1.0)
    min_answer_relevancy: float = Field(0.7, description="Minimum answer relevancy", ge=0.0, le=1.0)
    min_context_precision: float = Field(0.6, description="Minimum context precision", ge=0.0, le=1.0)
    min_context_recall: float = Field(0.6, description="Minimum context recall", ge=0.0, le=1.0)
    
    # Philosophical quality thresholds
    min_argument_coherence: float = Field(0.6, description="Minimum argument coherence", ge=0.0, le=1.0)
    min_conceptual_clarity: float = Field(0.7, description="Minimum conceptual clarity", ge=0.0, le=1.0)
    min_textual_fidelity: float = Field(0.8, description="Minimum textual fidelity", ge=0.0, le=1.0)
    
    # Duplicate detection thresholds
    max_duplicate_rate: float = Field(0.1, description="Maximum allowed duplicate rate", ge=0.0, le=1.0)
    semantic_similarity_threshold: float = Field(0.85, description="Semantic similarity threshold", ge=0.0, le=1.0)
    fuzzy_matching_threshold: float = Field(0.8, description="Fuzzy matching threshold", ge=0.0, le=1.0)
    
    # Citation validation thresholds
    min_citation_accuracy: float = Field(0.8, description="Minimum citation accuracy", ge=0.0, le=1.0)
    max_citation_errors: int = Field(5, description="Maximum citation errors allowed", ge=0)
    
    # Performance thresholds
    max_processing_time: float = Field(300.0, description="Maximum processing time in seconds")
    min_throughput_items_per_second: float = Field(0.1, description="Minimum processing throughput")
    
    def validate_ragas_results(self, results: EvaluationResult) -> Tuple[ValidationStatus, List[str]]:
        """Validate RAGAS results against thresholds."""
        issues = []
        status = ValidationStatus.PASSED
        
        if results.faithfulness_score < self.min_faithfulness:
            issues.append(f"Faithfulness {results.faithfulness_score:.3f} below threshold {self.min_faithfulness}")
            status = ValidationStatus.FAILED
        
        if results.answer_relevancy_score < self.min_answer_relevancy:
            issues.append(f"Answer relevancy {results.answer_relevancy_score:.3f} below threshold {self.min_answer_relevancy}")
            status = ValidationStatus.FAILED
        
        if results.context_precision_score < self.min_context_precision:
            issues.append(f"Context precision {results.context_precision_score:.3f} below threshold {self.min_context_precision}")
            status = ValidationStatus.WARNING if status != ValidationStatus.FAILED else status
        
        if results.context_recall_score < self.min_context_recall:
            issues.append(f"Context recall {results.context_recall_score:.3f} below threshold {self.min_context_recall}")
            status = ValidationStatus.WARNING if status != ValidationStatus.FAILED else status
        
        return status, issues
    
    def validate_duplicate_results(self, duplicates: List[DuplicateResult], total_items: int) -> Tuple[ValidationStatus, List[str]]:
        """Validate duplicate detection results against thresholds."""
        issues = []
        status = ValidationStatus.PASSED
        
        if not total_items:
            return ValidationStatus.SKIPPED, ["No items to validate"]
        
        # Calculate duplicate rate
        duplicate_items = sum(len(dup.items) - 1 for dup in duplicates)  # -1 because we keep one from each group
        duplicate_rate = duplicate_items / total_items
        
        if duplicate_rate > self.max_duplicate_rate:
            issues.append(f"Duplicate rate {duplicate_rate:.3f} exceeds threshold {self.max_duplicate_rate}")
            status = ValidationStatus.WARNING  # Usually warning, not failure
        
        return status, issues
    
    def validate_citation_accuracy(self, accuracy: float, error_count: int) -> Tuple[ValidationStatus, List[str]]:
        """Validate citation accuracy against thresholds."""
        issues = []
        status = ValidationStatus.PASSED
        
        if accuracy < self.min_citation_accuracy:
            issues.append(f"Citation accuracy {accuracy:.3f} below threshold {self.min_citation_accuracy}")
            status = ValidationStatus.FAILED
        
        if error_count > self.max_citation_errors:
            issues.append(f"Citation errors {error_count} exceed threshold {self.max_citation_errors}")
            status = ValidationStatus.WARNING if status != ValidationStatus.FAILED else status
        
        return status, issues


class QualityPipelineConfig(BaseModel):
    """Configuration for data quality pipeline execution."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Assessment configuration
    assessment_level: QualityAssessmentLevel = Field(
        QualityAssessmentLevel.STANDARD,
        description="Level of quality assessment to perform"
    )
    
    # Component enablement
    enable_ragas_evaluation: bool = Field(True, description="Enable RAGAS evaluation")
    enable_duplicate_detection: bool = Field(True, description="Enable duplicate detection")
    enable_citation_validation: bool = Field(True, description="Enable citation validation")
    enable_quality_monitoring: bool = Field(True, description="Enable quality monitoring")
    
    # RAGAS configuration
    ragas_metrics: List[str] = Field(
        default_factory=lambda: ["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
        description="RAGAS metrics to evaluate"
    )
    
    # Duplicate detection configuration
    duplication_strategies: List[DuplicationStrategy] = Field(
        default_factory=lambda: [
            DuplicationStrategy.EXACT_MATCH,
            DuplicationStrategy.SEMANTIC_SIMILARITY,
            DuplicationStrategy.FUZZY_MATCHING
        ],
        description="Duplicate detection strategies to use"
    )
    
    # Validation rules
    validation_rules: QualityValidationRules = Field(
        default_factory=QualityValidationRules,
        description="Quality validation rules and thresholds"
    )
    
    # Performance configuration
    batch_size: int = Field(50, description="Batch size for processing", gt=0)
    max_workers: int = Field(4, description="Maximum number of worker threads", gt=0)
    timeout_seconds: float = Field(600.0, description="Pipeline timeout in seconds")
    
    # Output configuration
    save_results: bool = Field(True, description="Save assessment results to file")
    results_directory: Optional[Path] = Field(None, description="Directory to save results")
    generate_report: bool = Field(True, description="Generate detailed quality report")


class DataQualityPipeline:
    """
    Comprehensive data quality pipeline orchestration service.
    
    Coordinates all data quality validation activities including RAGAS evaluation,
    duplicate detection, citation validation, and quality monitoring.
    """
    
    def __init__(self, config: Optional[QualityPipelineConfig] = None):
        """Initialize the data quality pipeline."""
        self.config = config or QualityPipelineConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize component services
        self._ragas_service = None
        self._duplicate_service = None
        self._quality_monitor = None
        
        # Performance tracking
        self._performance_stats = {}
    
    @property
    def ragas_service(self) -> RAGASQualityService:
        """Get or create RAGAS quality service."""
        if self._ragas_service is None:
            self._ragas_service = RAGASQualityService()
        return self._ragas_service
    
    @property
    def duplicate_service(self) -> DuplicateDetectionService:
        """Get or create duplicate detection service."""
        if self._duplicate_service is None:
            self._duplicate_service = DuplicateDetectionService()
        return self._duplicate_service
    
    @property
    def quality_monitor(self) -> QualityMonitor:
        """Get or create quality monitor."""
        if self._quality_monitor is None:
            self._quality_monitor = QualityMonitor()
        return self._quality_monitor
    
    async def assess_data_quality(
        self,
        data: Union[List[Document], List[Chunk], List[Citation], Dict[str, List[Any]]],
        query: Optional[str] = None,
        contexts: Optional[List[str]] = None,
        ground_truth: Optional[str] = None
    ) -> QualityAssessmentReport:
        """
        Perform comprehensive data quality assessment.
        
        Args:
            data: Data to assess (documents, chunks, citations, or mixed)
            query: Query for RAG evaluation (if applicable)
            contexts: Context texts for evaluation
            ground_truth: Ground truth answer for evaluation
            
        Returns:
            Comprehensive quality assessment report
        """
        start_time = datetime.now(timezone.utc)
        assessment_id = f"qa_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting data quality assessment {assessment_id}")
        
        # Initialize report
        report = QualityAssessmentReport(
            assessment_id=assessment_id,
            assessment_level=self.config.assessment_level
        )
        
        try:
            # Determine data types
            data_by_type = self._categorize_data(data)
            total_items = sum(len(items) for items in data_by_type.values())
            report.items_processed = total_items
            
            if total_items == 0:
                self.logger.warning("No items to process in data quality assessment")
                return report
            
            # Run assessment components based on configuration and level
            await self._run_assessment_components(
                report, data_by_type, query, contexts, ground_truth
            )
            
            # Calculate overall metrics
            report.calculate_overall_score()
            report.assign_quality_grade()
            
            # Generate recommendations
            self._generate_recommendations(report)
            
            # Record performance metrics
            end_time = datetime.now(timezone.utc)
            report.processing_time = (end_time - start_time).total_seconds()
            
            # Save results if configured
            if self.config.save_results:
                await self._save_assessment_results(report)
            
            self.logger.info(
                f"Data quality assessment {assessment_id} completed: "
                f"Score {report.overall_quality_score:.3f}, Grade {report.quality_grade}"
            )
            
        except Exception as e:
            self.logger.error(f"Error in data quality assessment {assessment_id}: {e}")
            report.quality_alerts.append(QualityAlert(
                severity=AlertSeverity.CRITICAL,
                message=f"Assessment failed: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            ))
            raise
        
        return report
    
    def _categorize_data(self, data: Union[List[Any], Dict[str, List[Any]]]) -> Dict[str, List[Any]]:
        """Categorize data by type for appropriate processing."""
        if isinstance(data, dict):
            return data
        
        categorized = {
            "documents": [],
            "chunks": [],
            "citations": [],
            "other": []
        }
        
        for item in data:
            if isinstance(item, Document):
                categorized["documents"].append(item)
            elif isinstance(item, Chunk):
                categorized["chunks"].append(item)
            elif isinstance(item, Citation):
                categorized["citations"].append(item)
            else:
                categorized["other"].append(item)
        
        return categorized
    
    async def _run_assessment_components(
        self,
        report: QualityAssessmentReport,
        data_by_type: Dict[str, List[Any]],
        query: Optional[str],
        contexts: Optional[List[str]],
        ground_truth: Optional[str]
    ):
        """Run all enabled assessment components."""
        
        # RAGAS Evaluation
        if self.config.enable_ragas_evaluation and query:
            await self._run_ragas_evaluation(report, query, contexts, ground_truth)
        
        # Duplicate Detection
        if self.config.enable_duplicate_detection:
            await self._run_duplicate_detection(report, data_by_type)
        
        # Citation Validation
        if self.config.enable_citation_validation and data_by_type.get("citations"):
            await self._run_citation_validation(report, data_by_type["citations"])
        
        # Quality Monitoring (if comprehensive level)
        if (self.config.enable_quality_monitoring and 
            self.config.assessment_level in [QualityAssessmentLevel.COMPREHENSIVE, QualityAssessmentLevel.RESEARCH]):
            await self._run_quality_monitoring(report)
    
    async def _run_ragas_evaluation(
        self,
        report: QualityAssessmentReport,
        query: str,
        contexts: Optional[List[str]],
        ground_truth: Optional[str]
    ):
        """Run RAGAS evaluation component."""
        try:
            self.logger.info("Running RAGAS evaluation")
            
            # Run RAGAS evaluation
            ragas_result = await self.ragas_service.evaluate_query(
                question=query,
                contexts=contexts or [],
                ground_truth=ground_truth
            )
            
            report.ragas_results = ragas_result
            
            # Validate against thresholds
            status, issues = self.config.validation_rules.validate_ragas_results(ragas_result)
            report.ragas_status = status
            
            # Add alerts for issues
            for issue in issues:
                severity = AlertSeverity.ERROR if status == ValidationStatus.FAILED else AlertSeverity.WARNING
                report.quality_alerts.append(QualityAlert(
                    severity=severity,
                    message=f"RAGAS validation: {issue}",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            self.logger.info(f"RAGAS evaluation completed with status: {status}")
            
        except Exception as e:
            self.logger.error(f"RAGAS evaluation failed: {e}")
            report.ragas_status = ValidationStatus.FAILED
            report.quality_alerts.append(QualityAlert(
                severity=AlertSeverity.ERROR,
                message=f"RAGAS evaluation failed: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            ))
    
    async def _run_duplicate_detection(
        self,
        report: QualityAssessmentReport,
        data_by_type: Dict[str, List[Any]]
    ):
        """Run duplicate detection component."""
        try:
            self.logger.info("Running duplicate detection")
            
            all_duplicates = []
            total_items = 0
            
            # Process each data type
            for data_type, items in data_by_type.items():
                if not items:
                    continue
                
                total_items += len(items)
                
                # Determine field to check for duplicates
                text_field = self._get_text_field_for_type(data_type)
                if not text_field:
                    continue
                
                # Run duplicate detection with configured strategies
                for strategy in self.config.duplication_strategies:
                    if strategy == DuplicationStrategy.EXACT_MATCH:
                        duplicates = self.duplicate_service.find_exact_duplicates(items, field=text_field)
                    elif strategy == DuplicationStrategy.SEMANTIC_SIMILARITY:
                        duplicates = await self.duplicate_service.find_semantic_duplicates(
                            items, field=text_field
                        )
                    elif strategy == DuplicationStrategy.FUZZY_MATCHING:
                        duplicates = self.duplicate_service.find_fuzzy_duplicates(
                            items, field=text_field
                        )
                    else:
                        continue
                    
                    all_duplicates.extend(duplicates)
            
            report.duplicate_results = all_duplicates
            
            # Run deduplication if duplicates found
            if all_duplicates and total_items > 0:
                # Combine all items for deduplication
                all_items = []
                for items in data_by_type.values():
                    all_items.extend(items)
                
                dedup_result = await self.duplicate_service.deduplicate_items(all_items)
                report.deduplication_summary = dedup_result
            
            # Validate against thresholds
            status, issues = self.config.validation_rules.validate_duplicate_results(
                all_duplicates, total_items
            )
            report.duplicate_status = status
            
            # Add alerts for issues
            for issue in issues:
                report.quality_alerts.append(QualityAlert(
                    severity=AlertSeverity.WARNING,
                    message=f"Duplicate detection: {issue}",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            self.logger.info(f"Duplicate detection completed: {len(all_duplicates)} groups found")
            
        except Exception as e:
            self.logger.error(f"Duplicate detection failed: {e}")
            report.duplicate_status = ValidationStatus.FAILED
            report.quality_alerts.append(QualityAlert(
                severity=AlertSeverity.ERROR,
                message=f"Duplicate detection failed: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            ))
    
    async def _run_citation_validation(
        self,
        report: QualityAssessmentReport,
        citations: List[Citation]
    ):
        """Run citation validation component."""
        try:
            self.logger.info(f"Running citation validation for {len(citations)} citations")
            
            # Basic citation validation
            valid_citations = 0
            citation_errors = []
            
            for citation in citations:
                # Validate citation structure
                if not citation.text or not citation.target_passage:
                    citation_errors.append(f"Missing text or target_passage in citation")
                    continue
                
                # Validate citation format (basic check)
                if not self._is_valid_classical_reference(citation.target_passage):
                    citation_errors.append(f"Invalid reference format: {citation.target_passage}")
                    continue
                
                # Validate confidence score
                if hasattr(citation, 'confidence') and citation.confidence < 0.7:
                    citation_errors.append(f"Low confidence citation: {citation.target_passage}")
                    continue
                
                valid_citations += 1
            
            # Calculate accuracy
            accuracy = valid_citations / len(citations) if citations else 0.0
            report.citation_accuracy = accuracy
            report.citation_issues = [{"error": error} for error in citation_errors]
            
            # Validate against thresholds
            status, issues = self.config.validation_rules.validate_citation_accuracy(
                accuracy, len(citation_errors)
            )
            report.citation_status = status
            
            # Add alerts for issues
            for issue in issues:
                severity = AlertSeverity.ERROR if status == ValidationStatus.FAILED else AlertSeverity.WARNING
                report.quality_alerts.append(QualityAlert(
                    severity=severity,
                    message=f"Citation validation: {issue}",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            self.logger.info(f"Citation validation completed: {accuracy:.3f} accuracy")
            
        except Exception as e:
            self.logger.error(f"Citation validation failed: {e}")
            report.citation_status = ValidationStatus.FAILED
            report.quality_alerts.append(QualityAlert(
                severity=AlertSeverity.ERROR,
                message=f"Citation validation failed: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            ))
    
    async def _run_quality_monitoring(self, report: QualityAssessmentReport):
        """Run quality monitoring component."""
        try:
            self.logger.info("Running quality monitoring")
            
            # Get current monitoring stats
            stats = await self.quality_monitor.get_monitoring_stats()
            
            # Add monitoring information to report
            report.validation_summary["monitoring_stats"] = {
                "total_evaluations": stats.total_evaluations,
                "avg_quality_score": stats.average_quality_score,
                "evaluations_last_24h": stats.evaluations_last_24h,
                "active_alerts": len(stats.active_alerts)
            }
            
            # Add any active monitoring alerts
            report.quality_alerts.extend(stats.active_alerts)
            
        except Exception as e:
            self.logger.warning(f"Quality monitoring component failed: {e}")
            # Don't fail the entire assessment for monitoring issues
    
    def _get_text_field_for_type(self, data_type: str) -> Optional[str]:
        """Get the appropriate text field name for duplicate detection by data type."""
        field_mapping = {
            "documents": "content",
            "chunks": "text",
            "citations": "text",
            "other": None
        }
        return field_mapping.get(data_type)
    
    def _is_valid_classical_reference(self, reference: str) -> bool:
        """Basic validation for classical text references."""
        if not reference:
            return False
        
        # Check for common classical reference patterns
        classical_patterns = [
            r"Republic \d+[a-z]?",      # Republic 514a
            r"Ethics \d+[a-z]?",        # Ethics 1094a
            r"Rep\. \d+[a-z]?",         # Rep. 433a
            r"Eth\. \d+[a-z]?",         # Eth. 1094a
            r"[A-Z][a-z]+ \d+[a-z]?",   # Generic Work 123a
        ]
        
        import re
        for pattern in classical_patterns:
            if re.search(pattern, reference):
                return True
        
        return False
    
    def _generate_recommendations(self, report: QualityAssessmentReport):
        """Generate quality improvement recommendations based on assessment results."""
        
        # RAGAS-based recommendations
        if report.ragas_results:
            
            if report.ragas_results.faithfulness_score < 0.8:
                report.add_recommendation(
                    "Improve source document quality and relevance to increase faithfulness scores"
                )
            
            if report.ragas_results.answer_relevancy_score < 0.8:
                report.add_recommendation(
                    "Refine query processing and context selection to improve answer relevancy"
                )
            
            if report.ragas_results.context_precision_score < 0.7:
                report.add_recommendation(
                    "Enhance retrieval algorithms to improve context precision"
                )
            
            if report.ragas_results.context_recall_score < 0.7:
                report.add_recommendation(
                    "Expand context retrieval to improve recall of relevant information"
                )
        
        # Duplicate-based recommendations
        if report.duplicate_results:
            duplicate_count = len(report.duplicate_results)
            if duplicate_count > 0:
                report.add_recommendation(
                    f"Address {duplicate_count} duplicate groups to improve content uniqueness"
                )
        
        # Citation-based recommendations
        if report.citation_accuracy and report.citation_accuracy < 0.9:
            report.add_recommendation(
                "Improve citation validation and formatting for better academic accuracy"
            )
        
        # Performance recommendations
        if report.processing_time and report.processing_time > self.config.validation_rules.max_processing_time:
            report.add_recommendation(
                "Optimize processing performance through better indexing or parallel processing"
            )
        
        # Overall quality recommendations
        if report.overall_quality_score and report.overall_quality_score < 0.8:
            report.add_recommendation(
                "Consider implementing additional quality controls and validation steps"
            )
    
    async def _save_assessment_results(self, report: QualityAssessmentReport):
        """Save assessment results to file."""
        try:
            results_dir = self.config.results_directory or Path("data_quality_results")
            results_dir.mkdir(exist_ok=True)
            
            # Save detailed report
            report_file = results_dir / f"{report.assessment_id}_report.json"
            with open(report_file, 'w') as f:
                f.write(report.model_dump_json(indent=2))
            
            # Save summary
            summary_file = results_dir / f"{report.assessment_id}_summary.json"
            with open(summary_file, 'w') as f:
                import json
                json.dump(report.get_summary_dict(), f, indent=2, default=str)
            
            self.logger.info(f"Assessment results saved to {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save assessment results: {e}")
    
    async def run_continuous_assessment(
        self,
        data_source: callable,
        assessment_interval: int = 3600  # 1 hour
    ):
        """Run continuous data quality assessment."""
        self.logger.info(f"Starting continuous assessment with {assessment_interval}s interval")
        
        while True:
            try:
                # Get data from source
                data = await data_source()
                
                # Run assessment
                report = await self.assess_data_quality(data)
                
                # Log results
                self.logger.info(
                    f"Continuous assessment completed: Score {report.overall_quality_score:.3f}, "
                    f"Grade {report.quality_grade}, Alerts {len(report.quality_alerts)}"
                )
                
                # Wait for next interval
                await asyncio.sleep(assessment_interval)
                
            except Exception as e:
                self.logger.error(f"Error in continuous assessment: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying