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

from .data_quality_pipeline import (
    DataQualityPipeline,
    QualityAssessmentLevel,
    QualityAssessmentReport,
    QualityPipelineConfig,
    QualityValidationRules,
    ValidationStatus,
)
from .duplicate_detection_service import (
    DeduplicationResult,
    DuplicateDetectionService,
    DuplicateResult,
    DuplicationStrategy,
    SimilarityMetrics,
)
from .quality_monitor import (
    AlertSeverity,
    MonitoringStats,
    QualityAlert,
    QualityMonitor,
)
from .ragas_quality_service import (
    EvaluationResult,
    PhilosophicalEvaluationDataset,
    QualityMetrics,
    QualityThresholds,
    RAGASQualityService,
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
