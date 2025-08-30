"""
Data Quality Services for Arete Graph-RAG System.

This package provides comprehensive data quality validation and assessment
services including:
- RAGAS-based RAG evaluation metrics
- Duplicate detection and deduplication
- Citation accuracy validation
- Quality trend analysis and monitoring
- Philosophical domain-specific quality metrics
"""

from .ragas_quality_service import (
    RAGASQualityService,
    QualityMetrics,
    EvaluationResult,
    QualityThresholds,
    PhilosophicalEvaluationDataset
)
from .duplicate_detection_service import (
    DuplicateDetectionService,
    DuplicateResult,
    SimilarityMetrics,
    DeduplicationResult,
    DuplicationStrategy
)
from .quality_monitor import (
    QualityMonitor,
    QualityAlert,
    MonitoringStats,
    AlertSeverity
)
from .data_quality_pipeline import (
    DataQualityPipeline,
    QualityAssessmentReport,
    QualityValidationRules,
    QualityPipelineConfig,
    QualityAssessmentLevel,
    ValidationStatus
)

__all__ = [
    # RAGAS Quality Service
    "RAGASQualityService",
    "QualityMetrics", 
    "EvaluationResult",
    "QualityThresholds",
    "PhilosophicalEvaluationDataset",
    # Duplicate Detection
    "DuplicateDetectionService",
    "DuplicateResult",
    "SimilarityMetrics",
    "DeduplicationResult",
    "DuplicationStrategy",
    # Quality Monitoring
    "QualityMonitor",
    "QualityAlert",
    "MonitoringStats",
    "AlertSeverity",
    # Quality Pipeline
    "DataQualityPipeline",
    "QualityAssessmentReport",
    "QualityValidationRules",
    "QualityPipelineConfig",
    "QualityAssessmentLevel",
    "ValidationStatus",
]