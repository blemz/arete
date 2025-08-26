"""
Citation Validation Service for Arete Graph-RAG system.

This service provides comprehensive citation validation and accuracy checking:
- Validate citation accuracy against original source material
- Cross-reference citations with knowledge graph relationships
- Detect misattributions and citation errors
- Provide confidence scoring for citation claims
- Integration with expert validation systems
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import difflib
from uuid import UUID
import asyncio

from ..models.citation import Citation, CitationType, CitationContext
from ..models.document import Document
from ..models.chunk import Chunk
from ..services.context_composition_service import ContextResult
from .base import ServiceError

logger = logging.getLogger(__name__)


class CitationValidationError(ServiceError):
    """Base exception for citation validation service errors."""
    pass


class ValidationRuleError(CitationValidationError):
    """Exception for validation rule failures."""
    pass


class ValidationType(str, Enum):
    """Types of citation validation."""
    
    TEXTUAL_ACCURACY = "textual_accuracy"
    SOURCE_ATTRIBUTION = "source_attribution"
    CONTEXTUAL_RELEVANCE = "contextual_relevance"
    LOGICAL_CONSISTENCY = "logical_consistency"
    SCHOLARLY_FORMAT = "scholarly_format"


@dataclass
class ValidationRule:
    """A validation rule for citations."""
    
    name: str
    validation_type: ValidationType
    weight: float = 1.0
    is_required: bool = True
    
    # Rule configuration
    min_similarity_threshold: float = 0.8
    max_edit_distance: int = 5
    case_sensitive: bool = False


@dataclass
class ValidationResult:
    """Result of validating a single citation."""
    
    citation_id: UUID
    is_valid: bool = True
    confidence_score: float = 1.0
    
    # Rule-specific results
    rule_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Detailed findings
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Source verification
    source_found: bool = False
    source_accuracy: float = 0.0
    attribution_accuracy: float = 0.0
    
    # Context analysis
    contextual_relevance: float = 0.0
    philosophical_accuracy: float = 0.0


@dataclass
class BatchValidationResult:
    """Result of validating multiple citations."""
    
    # Individual results
    citation_results: List[ValidationResult] = field(default_factory=list)
    
    # Aggregate metrics
    overall_validity: bool = True
    average_confidence: float = 0.0
    
    # Citation quality metrics
    accuracy_score: float = 0.0
    coverage_score: float = 0.0
    scholarly_quality: float = 0.0
    
    # Processing metadata
    total_citations: int = 0
    valid_citations: int = 0
    processing_time: float = 0.0
    
    # Quality assessment
    quality_issues: List[str] = field(default_factory=list)
    quality_recommendations: List[str] = field(default_factory=list)


@dataclass
class CitationValidationConfig:
    """Configuration for citation validation operations."""
    
    # Validation settings
    enable_textual_validation: bool = True
    enable_source_validation: bool = True
    enable_contextual_validation: bool = True
    enable_format_validation: bool = True
    
    # Threshold settings
    min_confidence_threshold: float = 0.7
    textual_similarity_threshold: float = 0.8
    contextual_relevance_threshold: float = 0.6
    
    # Rule weights
    textual_accuracy_weight: float = 0.3
    source_attribution_weight: float = 0.3
    contextual_relevance_weight: float = 0.2
    format_accuracy_weight: float = 0.2
    
    # Performance settings
    max_concurrent_validations: int = 5
    validation_timeout: float = 30.0
    
    # Citation format preferences
    require_classical_format: bool = True
    allow_modern_format: bool = True
    strict_attribution: bool = True


class CitationValidationService:
    """
    Citation Validation Service for philosophical accuracy verification.
    
    Provides comprehensive validation of citations to ensure accuracy,
    proper attribution, and scholarly integrity in philosophical discourse.
    """
    
    def __init__(
        self,
        config: Optional[CitationValidationConfig] = None
    ):
        """
        Initialize citation validation service.
        
        Args:
            config: Validation configuration
        """
        self.config = config or CitationValidationConfig()
        
        # Initialize validation rules
        self.validation_rules = self._create_validation_rules()
        
        logger.info(f"Initialized CitationValidationService with {len(self.validation_rules)} rules")
    
    async def validate_citation(
        self,
        citation: Citation,
        source_context: Optional[ContextResult] = None,
        original_document: Optional[Document] = None
    ) -> ValidationResult:
        """
        Validate a single citation for accuracy and proper attribution.
        
        Args:
            citation: Citation to validate
            source_context: Context from which citation was derived
            original_document: Original document for cross-reference
            
        Returns:
            Validation result with detailed analysis
        """
        result = ValidationResult(citation_id=citation.id)
        
        try:
            # Apply all validation rules
            for rule in self.validation_rules:
                rule_result = await self._apply_validation_rule(
                    citation, rule, source_context, original_document
                )
                result.rule_results[rule.name] = rule_result
                
                # Update overall validity based on required rules
                if rule.is_required and not rule_result.get('passed', True):
                    result.is_valid = False
                    result.issues.append(f"Failed required validation: {rule.name}")
            
            # Calculate confidence score
            result.confidence_score = self._calculate_confidence_score(
                citation, result.rule_results
            )
            
            # Perform source verification
            if source_context:
                result = await self._verify_source_accuracy(
                    citation, source_context, result
                )
            
            # Analyze contextual relevance
            result = await self._analyze_contextual_relevance(
                citation, source_context, result
            )
            
            # Generate suggestions for improvement
            result.suggestions = self._generate_improvement_suggestions(
                citation, result
            )
            
            logger.debug(
                f"Validated citation {citation.id}: valid={result.is_valid}, "
                f"confidence={result.confidence_score:.3f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Citation validation failed for {citation.id}: {e}")
            result.is_valid = False
            result.confidence_score = 0.0
            result.issues.append(f"Validation error: {e}")
            return result
    
    async def validate_citations_batch(
        self,
        citations: List[Citation],
        source_context: Optional[ContextResult] = None,
        original_documents: Optional[List[Document]] = None
    ) -> BatchValidationResult:
        """
        Validate multiple citations in batch with parallel processing.
        
        Args:
            citations: Citations to validate
            source_context: Context from which citations were derived
            original_documents: Original documents for cross-reference
            
        Returns:
            Batch validation result with aggregate metrics
        """
        import time
        start_time = time.time()
        
        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.config.max_concurrent_validations)
            
            # Create validation tasks
            async def validate_with_semaphore(citation: Citation, doc: Optional[Document] = None):
                async with semaphore:
                    return await self.validate_citation(citation, source_context, doc)
            
            # Prepare document mapping if provided
            doc_mapping = {}
            if original_documents:
                for doc in original_documents:
                    doc_mapping[doc.id] = doc
            
            # Execute validations
            tasks = []
            for citation in citations:
                doc = doc_mapping.get(citation.document_id) if original_documents else None
                task = validate_with_semaphore(citation, doc)
                tasks.append(task)
            
            # Wait for all validations with timeout
            try:
                citation_results = await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=self.config.validation_timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Batch validation timed out, returning partial results")
                # Handle timeout by creating error results for incomplete validations
                citation_results = []
                for citation in citations:
                    error_result = ValidationResult(
                        citation_id=citation.id,
                        is_valid=False,
                        confidence_score=0.0,
                        issues=["Validation timed out"]
                    )
                    citation_results.append(error_result)
            
            # Create batch result
            batch_result = BatchValidationResult(
                citation_results=citation_results,
                total_citations=len(citations),
                processing_time=time.time() - start_time
            )
            
            # Calculate aggregate metrics
            batch_result = self._calculate_batch_metrics(batch_result)
            
            # Generate quality assessment
            batch_result = self._assess_batch_quality(batch_result, citations)
            
            logger.info(
                f"Batch validation completed: {batch_result.valid_citations}/{batch_result.total_citations} valid, "
                f"avg confidence: {batch_result.average_confidence:.3f}"
            )
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch validation failed: {e}")
            return BatchValidationResult(
                total_citations=len(citations),
                overall_validity=False,
                quality_issues=[f"Batch validation error: {e}"],
                processing_time=time.time() - start_time
            )
    
    def _create_validation_rules(self) -> List[ValidationRule]:
        """Create default validation rules."""
        rules = []
        
        # Textual accuracy rule
        if self.config.enable_textual_validation:
            rules.append(ValidationRule(
                name="textual_accuracy",
                validation_type=ValidationType.TEXTUAL_ACCURACY,
                weight=self.config.textual_accuracy_weight,
                is_required=True,
                min_similarity_threshold=self.config.textual_similarity_threshold
            ))
        
        # Source attribution rule
        if self.config.enable_source_validation:
            rules.append(ValidationRule(
                name="source_attribution",
                validation_type=ValidationType.SOURCE_ATTRIBUTION,
                weight=self.config.source_attribution_weight,
                is_required=self.config.strict_attribution
            ))
        
        # Contextual relevance rule
        if self.config.enable_contextual_validation:
            rules.append(ValidationRule(
                name="contextual_relevance",
                validation_type=ValidationType.CONTEXTUAL_RELEVANCE,
                weight=self.config.contextual_relevance_weight,
                is_required=False,
                min_similarity_threshold=self.config.contextual_relevance_threshold
            ))
        
        # Scholarly format rule
        if self.config.enable_format_validation:
            rules.append(ValidationRule(
                name="scholarly_format",
                validation_type=ValidationType.SCHOLARLY_FORMAT,
                weight=self.config.format_accuracy_weight,
                is_required=self.config.require_classical_format
            ))
        
        return rules
    
    async def _apply_validation_rule(
        self,
        citation: Citation,
        rule: ValidationRule,
        source_context: Optional[ContextResult],
        original_document: Optional[Document]
    ) -> Dict[str, Any]:
        """Apply a specific validation rule to a citation."""
        
        if rule.validation_type == ValidationType.TEXTUAL_ACCURACY:
            return await self._validate_textual_accuracy(citation, source_context, rule)
        
        elif rule.validation_type == ValidationType.SOURCE_ATTRIBUTION:
            return await self._validate_source_attribution(citation, source_context, rule)
        
        elif rule.validation_type == ValidationType.CONTEXTUAL_RELEVANCE:
            return await self._validate_contextual_relevance(citation, source_context, rule)
        
        elif rule.validation_type == ValidationType.SCHOLARLY_FORMAT:
            return await self._validate_scholarly_format(citation, rule)
        
        else:
            return {"passed": True, "score": 1.0, "message": "Unknown rule type"}
    
    async def _validate_textual_accuracy(
        self,
        citation: Citation,
        source_context: Optional[ContextResult],
        rule: ValidationRule
    ) -> Dict[str, Any]:
        """Validate textual accuracy of citation against source."""
        if not source_context or not source_context.citations:
            return {"passed": True, "score": 0.5, "message": "No source context available"}
        
        best_similarity = 0.0
        best_match = None
        
        # Find best matching source citation
        for ctx in source_context.citations:
            similarity = difflib.SequenceMatcher(
                None, 
                citation.text.lower(),
                ctx.citation.text.lower()
            ).ratio()
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = ctx.citation
        
        passed = best_similarity >= rule.min_similarity_threshold
        
        return {
            "passed": passed,
            "score": best_similarity,
            "similarity": best_similarity,
            "best_match_id": str(best_match.id) if best_match else None,
            "message": f"Textual similarity: {best_similarity:.3f}"
        }
    
    async def _validate_source_attribution(
        self,
        citation: Citation,
        source_context: Optional[ContextResult],
        rule: ValidationRule
    ) -> Dict[str, Any]:
        """Validate source attribution accuracy."""
        if not citation.source_author or not citation.source_title:
            return {
                "passed": False,
                "score": 0.0,
                "message": "Missing source author or title"
            }
        
        # Check if attribution matches known sources
        if source_context and source_context.citations:
            for ctx in source_context.citations:
                source_cit = ctx.citation
                if (citation.source_author.lower() in source_cit.source_author.lower() and
                    citation.source_title.lower() in source_cit.source_title.lower()):
                    return {
                        "passed": True,
                        "score": 1.0,
                        "message": "Source attribution verified"
                    }
        
        # Check classical reference format
        if citation.source_reference:
            classical_pattern = r'^[A-Za-z]+\s+\d+[a-z]?(?:\.\d+)?$'
            if re.match(classical_pattern, citation.source_reference):
                return {
                    "passed": True,
                    "score": 0.9,
                    "message": "Classical reference format valid"
                }
        
        return {
            "passed": not rule.is_required,
            "score": 0.6,
            "message": "Could not verify source attribution"
        }
    
    async def _validate_contextual_relevance(
        self,
        citation: Citation,
        source_context: Optional[ContextResult],
        rule: ValidationRule
    ) -> Dict[str, Any]:
        """Validate contextual relevance of citation."""
        
        # Basic relevance based on citation context type
        context_scores = {
            CitationContext.ARGUMENT: 1.0,
            CitationContext.COUNTERARGUMENT: 0.9,
            CitationContext.EXAMPLE: 0.8,
            CitationContext.DEFINITION: 0.9,
            CitationContext.EXPLANATION: 0.7
        }
        
        base_score = context_scores.get(citation.context, 0.5)
        
        # Adjust based on citation type
        type_adjustments = {
            CitationType.DIRECT_QUOTE: 1.0,
            CitationType.PARAPHRASE: 0.9,
            CitationType.REFERENCE: 0.8,
            CitationType.ALLUSION: 0.7
        }
        
        type_adjustment = type_adjustments.get(citation.citation_type, 0.5)
        final_score = (base_score + type_adjustment) / 2
        
        passed = final_score >= rule.min_similarity_threshold
        
        return {
            "passed": passed,
            "score": final_score,
            "message": f"Contextual relevance score: {final_score:.3f}"
        }
    
    async def _validate_scholarly_format(
        self,
        citation: Citation,
        rule: ValidationRule
    ) -> Dict[str, Any]:
        """Validate scholarly format of citation."""
        score = 0.0
        issues = []
        
        # Check for proper source reference format
        if citation.source_reference:
            # Classical format: "Republic 514a"
            classical_pattern = r'^[A-Za-z]+\s+\d+[a-z]?(?:\.\d+)?$'
            if re.match(classical_pattern, citation.source_reference):
                score += 0.4
            else:
                issues.append("Non-standard reference format")
        else:
            issues.append("Missing source reference")
        
        # Check for complete attribution
        if citation.source_author and citation.source_title:
            score += 0.3
        else:
            issues.append("Incomplete source attribution")
        
        # Check citation type appropriateness
        if citation.citation_type in [CitationType.DIRECT_QUOTE, CitationType.PARAPHRASE]:
            if citation.text and len(citation.text) > 10:
                score += 0.3
            else:
                issues.append("Citation text too brief for type")
        else:
            score += 0.3
        
        passed = score >= 0.7
        
        return {
            "passed": passed,
            "score": score,
            "issues": issues,
            "message": f"Scholarly format score: {score:.3f}"
        }
    
    def _calculate_confidence_score(
        self,
        citation: Citation,
        rule_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence score from rule results."""
        if not rule_results:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for rule in self.validation_rules:
            result = rule_results.get(rule.name, {})
            score = result.get('score', 0.0)
            
            weighted_sum += score * rule.weight
            total_weight += rule.weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    async def _verify_source_accuracy(
        self,
        citation: Citation,
        source_context: ContextResult,
        result: ValidationResult
    ) -> ValidationResult:
        """Verify accuracy against source context."""
        if not source_context or not source_context.citations:
            result.source_found = False
            result.source_accuracy = 0.0
            return result
        
        # Find matching source
        best_match = None
        best_accuracy = 0.0
        
        for ctx in source_context.citations:
            # Check text similarity
            text_similarity = difflib.SequenceMatcher(
                None, 
                citation.text.lower(),
                ctx.citation.text.lower()
            ).ratio()
            
            # Check attribution match
            attr_match = 0.0
            if (citation.source_author.lower() in ctx.citation.source_author.lower() and
                citation.source_title.lower() in ctx.citation.source_title.lower()):
                attr_match = 1.0
            
            # Combined accuracy
            accuracy = (text_similarity + attr_match) / 2
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_match = ctx.citation
        
        result.source_found = best_match is not None
        result.source_accuracy = best_accuracy
        result.attribution_accuracy = best_accuracy
        
        return result
    
    async def _analyze_contextual_relevance(
        self,
        citation: Citation,
        source_context: Optional[ContextResult],
        result: ValidationResult
    ) -> ValidationResult:
        """Analyze contextual relevance of citation."""
        
        # Base relevance from citation properties
        relevance = 0.5
        
        # Adjust based on citation type and context
        if citation.citation_type == CitationType.DIRECT_QUOTE:
            relevance += 0.2
        elif citation.citation_type == CitationType.PARAPHRASE:
            relevance += 0.15
        
        if citation.context in [CitationContext.ARGUMENT, CitationContext.COUNTERARGUMENT]:
            relevance += 0.2
        elif citation.context == CitationContext.DEFINITION:
            relevance += 0.15
        
        # Consider confidence score
        relevance = min(1.0, relevance * citation.confidence)
        
        result.contextual_relevance = relevance
        result.philosophical_accuracy = relevance  # Simplified for now
        
        return result
    
    def _generate_improvement_suggestions(
        self,
        citation: Citation,
        result: ValidationResult
    ) -> List[str]:
        """Generate suggestions for improving citation quality."""
        suggestions = []
        
        # Low confidence suggestions
        if result.confidence_score < 0.7:
            suggestions.append("Consider verifying the citation against the original source")
        
        # Source attribution suggestions
        if result.attribution_accuracy < 0.8:
            suggestions.append("Check source attribution for accuracy")
            if not citation.source_reference:
                suggestions.append("Add specific page or section reference (e.g., 'Republic 514a')")
        
        # Contextual relevance suggestions
        if result.contextual_relevance < 0.6:
            suggestions.append("Consider the relevance of this citation to your argument")
            suggestions.append("Provide more context to explain the citation's significance")
        
        # Format suggestions
        format_issues = []
        for rule_result in result.rule_results.values():
            if 'issues' in rule_result:
                format_issues.extend(rule_result['issues'])
        
        if format_issues:
            suggestions.append("Address formatting issues: " + ", ".join(format_issues))
        
        return suggestions
    
    def _calculate_batch_metrics(self, batch_result: BatchValidationResult) -> BatchValidationResult:
        """Calculate aggregate metrics for batch validation."""
        if not batch_result.citation_results:
            return batch_result
        
        # Count valid citations
        valid_count = sum(1 for r in batch_result.citation_results if r.is_valid)
        batch_result.valid_citations = valid_count
        batch_result.overall_validity = valid_count == batch_result.total_citations
        
        # Calculate average confidence
        total_confidence = sum(r.confidence_score for r in batch_result.citation_results)
        batch_result.average_confidence = total_confidence / len(batch_result.citation_results)
        
        # Calculate accuracy score (proportion of high-confidence valid citations)
        high_conf_valid = sum(
            1 for r in batch_result.citation_results 
            if r.is_valid and r.confidence_score >= 0.8
        )
        batch_result.accuracy_score = high_conf_valid / batch_result.total_citations
        
        # Calculate coverage score (proportion with good source accuracy)
        good_source_accuracy = sum(
            1 for r in batch_result.citation_results
            if r.source_accuracy >= 0.7
        )
        batch_result.coverage_score = good_source_accuracy / batch_result.total_citations
        
        # Calculate scholarly quality (average of various quality metrics)
        quality_scores = []
        for r in batch_result.citation_results:
            quality = (r.confidence_score + r.source_accuracy + r.contextual_relevance) / 3
            quality_scores.append(quality)
        
        batch_result.scholarly_quality = sum(quality_scores) / len(quality_scores)
        
        return batch_result
    
    def _assess_batch_quality(
        self, 
        batch_result: BatchValidationResult, 
        citations: List[Citation]
    ) -> BatchValidationResult:
        """Assess overall quality and provide recommendations."""
        
        # Quality issues
        if batch_result.accuracy_score < 0.7:
            batch_result.quality_issues.append(
                f"Low accuracy score ({batch_result.accuracy_score:.2f}). "
                "Many citations may not accurately reflect their sources."
            )
        
        if batch_result.coverage_score < 0.6:
            batch_result.quality_issues.append(
                f"Low source coverage ({batch_result.coverage_score:.2f}). "
                "Consider citing more diverse or authoritative sources."
            )
        
        if batch_result.scholarly_quality < 0.7:
            batch_result.quality_issues.append(
                f"Below-standard scholarly quality ({batch_result.scholarly_quality:.2f}). "
                "Review citation formatting and attribution practices."
            )
        
        # Recommendations
        invalid_count = batch_result.total_citations - batch_result.valid_citations
        if invalid_count > 0:
            batch_result.quality_recommendations.append(
                f"Review and correct {invalid_count} invalid citations"
            )
        
        quote_count = sum(1 for c in citations if c.citation_type == CitationType.DIRECT_QUOTE)
        if quote_count > batch_result.total_citations * 0.7:
            batch_result.quality_recommendations.append(
                "Consider balancing direct quotes with paraphrases and analysis"
            )
        
        if batch_result.average_confidence < 0.8:
            batch_result.quality_recommendations.append(
                "Improve citation accuracy by double-checking sources"
            )
        
        return batch_result


# Factory function following established pattern
def create_citation_validation_service(
    config: Optional[CitationValidationConfig] = None
) -> CitationValidationService:
    """
    Create citation validation service with configuration.
    
    Args:
        config: Optional configuration
        
    Returns:
        Configured CitationValidationService instance
    """
    return CitationValidationService(config=config)