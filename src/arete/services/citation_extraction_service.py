"""
Citation Extraction Service for Arete Graph-RAG system.

This service provides comprehensive citation extraction and validation functionality:
- Extract citations from LLM-generated responses
- Validate citation accuracy against source material
- Track citation provenance and confidence scoring
- Format citations according to classical philosophical standards
- Integration with response generation pipeline for source attribution
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import difflib
from uuid import uuid4, UUID

from ..models.citation import Citation, CitationType, CitationContext
from ..services.context_composition_service import ContextResult, CitationContext as ComposedCitationContext
from .base import ServiceError

logger = logging.getLogger(__name__)


class CitationExtractionError(ServiceError):
    """Base exception for citation extraction service errors."""
    pass


class ValidationError(CitationExtractionError):
    """Exception for citation validation failures."""
    pass


class PatternMatchingError(CitationExtractionError):
    """Exception for pattern matching failures."""
    pass


@dataclass
class CitationMatch:
    """A potential citation match found in text."""
    
    text: str
    start_pos: int
    end_pos: int
    confidence: float = 0.0
    
    # Pattern information
    pattern_type: str = ""  # "classical_ref", "direct_quote", "author_work"
    pattern_match: Optional[re.Match] = None
    
    # Validation results
    is_validated: bool = False
    validation_score: float = 0.0
    source_citation: Optional[Citation] = None


@dataclass
class ExtractionResult:
    """Result of citation extraction from text."""
    
    # Extracted citations
    citations: List[Citation] = field(default_factory=list)
    
    # Processing metadata
    total_matches_found: int = 0
    validated_matches: int = 0
    processing_time: float = 0.0
    
    # Pattern matching results
    pattern_matches: List[CitationMatch] = field(default_factory=list)
    
    # Validation metrics
    accuracy_score: float = 0.0
    coverage_score: float = 0.0
    
    # Issues and warnings
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CitationExtractionConfig:
    """Configuration for citation extraction operations."""
    
    # Pattern matching settings
    enable_classical_patterns: bool = True
    enable_direct_quote_detection: bool = True
    enable_author_work_patterns: bool = True
    
    # Validation settings
    min_confidence_threshold: float = 0.6
    similarity_threshold: float = 0.8
    max_edit_distance: int = 5
    
    # Processing limits
    max_citations_to_extract: int = 20
    min_citation_length: int = 10
    max_citation_length: int = 500
    
    # Format preferences
    preferred_citation_format: str = "classical"  # classical, modern, chicago
    include_page_references: bool = True
    normalize_references: bool = True


class CitationExtractionService:
    """
    Citation Extraction Service for philosophical text analysis.
    
    Extracts, validates, and formats citations from LLM-generated responses
    to ensure accurate source attribution and scholarly integrity.
    """
    
    # Classical philosophical reference patterns
    CLASSICAL_PATTERNS = [
        # Republic 514a, Ethics 1094a, Meditations 2.11
        r'(?P<work>Republic|Ethics|Meditations|Politics|Poetics|Timaeus|Phaedo|Apology|Symposium|Phaedrus)\s+(?P<ref>\d+[a-z]?(?:\.\d+)?)',
        
        # Plato, Republic 514a
        r'(?P<author>Plato|Aristotle|Augustine|Aquinas|Descartes|Kant|Hegel|Nietzsche),?\s+(?P<work>\w+)\s+(?P<ref>\d+[a-z]?(?:\.\d+)?)',
        
        # (Republic 514a)
        r'\((?P<work>Republic|Ethics|Meditations|Politics|Poetics)\s+(?P<ref>\d+[a-z]?(?:\.\d+)?)\)',
        
        # Stephanus numbering: Phaedo 64a-65b
        r'(?P<work>Phaedo|Timaeus|Republic|Meno|Theaetetus)\s+(?P<ref>\d+[a-z]?(?:-\d+[a-z]?)?)',
    ]
    
    # Direct quote patterns
    QUOTE_PATTERNS = [
        r'"([^"]{10,200})"',  # Standard double quotes
        r'"([^"]{10,200})"',  # Curly quotes  
        r''([^']{10,200})'',  # Single curly quotes
    ]
    
    # Author-work patterns for broader matching
    AUTHOR_WORK_PATTERNS = [
        r'(?P<author>Plato|Aristotle|Augustine|Aquinas|Descartes|Kant|Hegel|Nietzsche)(?:\s+(?:in|writes in|argues in|states in))?\s+(?P<work>\w+)',
    ]
    
    def __init__(self, config: Optional[CitationExtractionConfig] = None):
        """
        Initialize citation extraction service.
        
        Args:
            config: Configuration for extraction operations
        """
        self.config = config or CitationExtractionConfig()
        
        # Compile patterns for efficiency
        self._classical_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.CLASSICAL_PATTERNS]
        self._quote_patterns = [re.compile(pattern) for pattern in self.QUOTE_PATTERNS]
        self._author_work_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.AUTHOR_WORK_PATTERNS]
        
        logger.info(f"Initialized CitationExtractionService with {len(self._classical_patterns)} classical patterns")
    
    def extract_citations_from_response(
        self,
        response_text: str,
        context_result: ContextResult,
        query: str = ""
    ) -> ExtractionResult:
        """
        Extract citations from LLM response text.
        
        Args:
            response_text: Generated response text to analyze
            context_result: Context used for generation (contains source citations)
            query: Original query for context
            
        Returns:
            Extraction result with found citations and validation metrics
        """
        import time
        start_time = time.time()
        
        try:
            # Find all potential citation matches
            matches = self._find_citation_matches(response_text)
            
            # Validate matches against source material
            validated_citations = self._validate_matches_against_context(
                matches, context_result
            )
            
            # Create extraction result
            result = ExtractionResult(
                citations=validated_citations,
                total_matches_found=len(matches),
                validated_matches=len(validated_citations),
                processing_time=time.time() - start_time,
                pattern_matches=matches
            )
            
            # Calculate accuracy and coverage scores
            result.accuracy_score = self._calculate_accuracy_score(validated_citations, context_result)
            result.coverage_score = self._calculate_coverage_score(validated_citations, context_result)
            
            # Add quality issues and warnings
            self._analyze_quality_issues(result, response_text, context_result)
            
            logger.info(
                f"Citation extraction completed: {len(validated_citations)} citations extracted, "
                f"accuracy: {result.accuracy_score:.3f}, coverage: {result.coverage_score:.3f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            raise CitationExtractionError(f"Citation extraction failed: {e}") from e
    
    def _find_citation_matches(self, text: str) -> List[CitationMatch]:
        """Find all potential citation matches in text."""
        matches = []
        
        # Classical reference patterns
        if self.config.enable_classical_patterns:
            for pattern in self._classical_patterns:
                for match in pattern.finditer(text):
                    citation_match = CitationMatch(
                        text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        pattern_type="classical_ref",
                        pattern_match=match,
                        confidence=0.9  # High confidence for classical patterns
                    )
                    matches.append(citation_match)
        
        # Direct quote patterns
        if self.config.enable_direct_quote_detection:
            for pattern in self._quote_patterns:
                for match in pattern.finditer(text):
                    quote_text = match.group(1)
                    if (self.config.min_citation_length <= len(quote_text) <= 
                        self.config.max_citation_length):
                        citation_match = CitationMatch(
                            text=quote_text,
                            start_pos=match.start(1),
                            end_pos=match.end(1),
                            pattern_type="direct_quote",
                            pattern_match=match,
                            confidence=0.7  # Medium confidence for quotes
                        )
                        matches.append(citation_match)
        
        # Author-work patterns
        if self.config.enable_author_work_patterns:
            for pattern in self._author_work_patterns:
                for match in pattern.finditer(text):
                    citation_match = CitationMatch(
                        text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        pattern_type="author_work",
                        pattern_match=match,
                        confidence=0.6  # Lower confidence for general patterns
                    )
                    matches.append(citation_match)
        
        # Remove overlapping matches (keep highest confidence)
        matches = self._remove_overlapping_matches(matches)
        
        # Filter by confidence threshold
        matches = [m for m in matches if m.confidence >= self.config.min_confidence_threshold]
        
        # Limit number of matches
        matches = matches[:self.config.max_citations_to_extract]
        
        logger.debug(f"Found {len(matches)} potential citation matches")
        return matches
    
    def _remove_overlapping_matches(self, matches: List[CitationMatch]) -> List[CitationMatch]:
        """Remove overlapping matches, keeping the highest confidence ones."""
        if not matches:
            return matches
        
        # Sort by position
        matches.sort(key=lambda m: m.start_pos)
        
        non_overlapping = []
        for match in matches:
            # Check for overlap with existing matches
            overlaps = False
            for existing in non_overlapping:
                if (match.start_pos < existing.end_pos and 
                    match.end_pos > existing.start_pos):
                    # There's overlap - keep the higher confidence match
                    if match.confidence > existing.confidence:
                        non_overlapping.remove(existing)
                    else:
                        overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(match)
        
        return non_overlapping
    
    def _validate_matches_against_context(
        self, 
        matches: List[CitationMatch], 
        context_result: ContextResult
    ) -> List[Citation]:
        """Validate citation matches against source context."""
        validated_citations = []
        
        for match in matches:
            try:
                citation = self._create_citation_from_match(match, context_result)
                if citation:
                    match.is_validated = True
                    match.source_citation = citation
                    validated_citations.append(citation)
                    logger.debug(f"Validated citation: {citation.text[:50]}...")
                
            except Exception as e:
                logger.warning(f"Failed to validate match '{match.text[:30]}...': {e}")
                continue
        
        return validated_citations
    
    def _create_citation_from_match(
        self, 
        match: CitationMatch, 
        context_result: ContextResult
    ) -> Optional[Citation]:
        """Create a Citation object from a validated match."""
        
        if match.pattern_type == "classical_ref" and match.pattern_match:
            return self._create_classical_reference_citation(match, context_result)
        elif match.pattern_type == "direct_quote":
            return self._create_quote_citation(match, context_result)
        elif match.pattern_type == "author_work" and match.pattern_match:
            return self._create_author_work_citation(match, context_result)
        
        return None
    
    def _create_classical_reference_citation(
        self, 
        match: CitationMatch, 
        context_result: ContextResult
    ) -> Optional[Citation]:
        """Create citation from classical reference pattern."""
        pattern_match = match.pattern_match
        groups = pattern_match.groupdict()
        
        # Extract work and reference
        work = groups.get('work', '')
        reference = groups.get('ref', '')
        author = groups.get('author', '')
        
        # Find corresponding source in context
        source_citation = self._find_matching_source_citation(
            work, reference, author, context_result
        )
        
        if not source_citation:
            return None
        
        # Create new citation based on source
        citation = Citation(
            id=uuid4(),
            text=match.text,
            citation_type=CitationType.REFERENCE,
            context=CitationContext.EXPLANATION,
            document_id=source_citation.document_id,
            source_title=source_citation.source_title,
            source_author=source_citation.source_author,
            source_reference=f"{work} {reference}",
            source_edition=source_citation.source_edition,
            source_translator=source_citation.source_translator,
            start_char=match.start_pos,
            end_char=match.end_pos,
            confidence=match.confidence
        )
        
        return citation
    
    def _create_quote_citation(
        self, 
        match: CitationMatch, 
        context_result: ContextResult
    ) -> Optional[Citation]:
        """Create citation from direct quote."""
        quote_text = match.text
        
        # Find best matching source citation
        best_match = None
        best_similarity = 0.0
        
        for ctx in context_result.citations:
            similarity = self._calculate_text_similarity(quote_text, ctx.citation.text)
            if similarity > best_similarity and similarity >= self.config.similarity_threshold:
                best_similarity = similarity
                best_match = ctx.citation
        
        if not best_match:
            return None
        
        # Create citation with quote type
        citation = Citation(
            id=uuid4(),
            text=quote_text,
            citation_type=CitationType.DIRECT_QUOTE,
            context=CitationContext.ARGUMENT,
            document_id=best_match.document_id,
            source_title=best_match.source_title,
            source_author=best_match.source_author,
            source_reference=best_match.source_reference,
            source_edition=best_match.source_edition,
            source_translator=best_match.source_translator,
            start_char=match.start_pos,
            end_char=match.end_pos,
            confidence=best_similarity
        )
        
        return citation
    
    def _create_author_work_citation(
        self, 
        match: CitationMatch, 
        context_result: ContextResult
    ) -> Optional[Citation]:
        """Create citation from author-work pattern."""
        pattern_match = match.pattern_match
        groups = pattern_match.groupdict()
        
        author = groups.get('author', '')
        work = groups.get('work', '')
        
        # Find matching source citation
        source_citation = self._find_matching_source_citation(
            work, '', author, context_result
        )
        
        if not source_citation:
            return None
        
        citation = Citation(
            id=uuid4(),
            text=match.text,
            citation_type=CitationType.REFERENCE,
            context=CitationContext.EXPLANATION,
            document_id=source_citation.document_id,
            source_title=work,
            source_author=author,
            source_reference=source_citation.source_reference,
            source_edition=source_citation.source_edition,
            source_translator=source_citation.source_translator,
            start_char=match.start_pos,
            end_char=match.end_pos,
            confidence=match.confidence
        )
        
        return citation
    
    def _find_matching_source_citation(
        self, 
        work: str, 
        reference: str, 
        author: str, 
        context_result: ContextResult
    ) -> Optional[Citation]:
        """Find matching citation in context sources."""
        for ctx in context_result.citations:
            citation = ctx.citation
            
            # Check work match
            if work and work.lower() in citation.source_title.lower():
                # Check reference if provided
                if reference:
                    if citation.source_reference and reference in citation.source_reference:
                        return citation
                else:
                    # Check author if provided
                    if author:
                        if author.lower() in citation.source_author.lower():
                            return citation
                    else:
                        return citation
        
        return None
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        # Use difflib for similarity calculation
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _calculate_accuracy_score(
        self, 
        citations: List[Citation], 
        context_result: ContextResult
    ) -> float:
        """Calculate accuracy score based on citation validation."""
        if not citations:
            return 0.0
        
        # Count validated citations with high confidence
        high_confidence_citations = sum(
            1 for c in citations 
            if c.confidence >= 0.8
        )
        
        return high_confidence_citations / len(citations)
    
    def _calculate_coverage_score(
        self, 
        citations: List[Citation], 
        context_result: ContextResult
    ) -> float:
        """Calculate coverage score (how much of source material is cited)."""
        if not context_result.citations:
            return 1.0  # Full coverage if no sources expected
        
        # Count unique sources that are cited
        cited_sources = set()
        for citation in citations:
            source_key = (citation.source_author, citation.source_title)
            cited_sources.add(source_key)
        
        # Count total unique sources in context
        total_sources = set()
        for ctx in context_result.citations:
            source_key = (ctx.citation.source_author, ctx.citation.source_title)
            total_sources.add(source_key)
        
        if not total_sources:
            return 1.0
        
        return len(cited_sources) / len(total_sources)
    
    def _analyze_quality_issues(
        self, 
        result: ExtractionResult, 
        response_text: str, 
        context_result: ContextResult
    ) -> None:
        """Analyze and report quality issues with extraction."""
        
        # Check for insufficient citations
        if result.coverage_score < 0.5:
            result.issues.append(
                f"Low citation coverage ({result.coverage_score:.2f}). "
                "Consider citing more of the provided source material."
            )
        
        # Check for low accuracy
        if result.accuracy_score < 0.7:
            result.issues.append(
                f"Low citation accuracy ({result.accuracy_score:.2f}). "
                "Some citations may not match the source material accurately."
            )
        
        # Check for missing classical references
        if (self.config.enable_classical_patterns and 
            not any(c.citation_type == CitationType.REFERENCE for c in result.citations)):
            result.warnings.append(
                "No classical references found. Consider using standard philosophical citations."
            )
        
        # Check for excessive quoting
        quote_count = sum(1 for c in result.citations if c.citation_type == CitationType.DIRECT_QUOTE)
        if quote_count > len(result.citations) * 0.7:
            result.warnings.append(
                "High proportion of direct quotes. Consider more paraphrasing and analysis."
            )
        
        # Check response length vs citations
        words_per_citation = len(response_text.split()) / max(len(result.citations), 1)
        if words_per_citation > 200:
            result.warnings.append(
                f"Low citation density ({words_per_citation:.0f} words per citation). "
                "Consider adding more source references."
            )


# Factory function following established pattern
def create_citation_extraction_service(
    config: Optional[CitationExtractionConfig] = None
) -> CitationExtractionService:
    """
    Create citation extraction service with configuration.
    
    Args:
        config: Optional configuration
        
    Returns:
        Configured CitationExtractionService instance
    """
    return CitationExtractionService(config=config)