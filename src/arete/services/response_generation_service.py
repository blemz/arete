"""
Response Generation Service for Arete Graph-RAG system.

This service provides complete response generation functionality including:
- Multi-provider LLM integration for response generation
- Citation formatting and source attribution
- Educational accuracy validation
- Integration with RAG pipeline (retrieval → re-ranking → diversification → generation)
- Performance optimization with caching and token management
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from ..config import Settings, get_settings
from ..services.context_composition_service import ContextResult
from ..services.simple_llm_service import SimpleLLMService
from ..services.expert_validation_service import ExpertValidationService
from ..services.citation_extraction_service import CitationExtractionService, CitationExtractionConfig
from ..services.citation_validation_service import CitationValidationService, CitationValidationConfig
from ..services.citation_tracking_service import CitationTrackingService, CitationTrackingConfig, TrackingEventType, CitationSource
from ..services.llm_provider import LLMMessage, LLMResponse, MessageRole
from ..models.citation import Citation
from .base import ServiceError

logger = logging.getLogger(__name__)


class ResponseGenerationError(ServiceError):
    """Base exception for response generation service errors."""
    pass


class ValidationError(ResponseGenerationError):
    """Exception for validation failures."""
    pass


class CitationError(ResponseGenerationError):
    """Exception for citation-related errors."""
    
    def __init__(self, message: str, citation_id: Optional[str] = None):
        super().__init__(message)
        self.citation_id = citation_id


@dataclass
class ResponseGenerationConfig:
    """Configuration for response generation operations."""
    
    # Response generation parameters
    max_response_tokens: int = 2000
    max_context_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Validation settings
    enable_validation: bool = True
    fail_on_validation_error: bool = False
    min_accuracy_score: float = 0.7
    min_citation_coverage: float = 0.5
    
    # Citation handling
    citation_format: str = "classical"  # classical, modern, footnote
    include_source_attribution: bool = True
    max_citations: int = 10
    deduplicate_citations: bool = True
    
    # Performance optimization
    enable_caching: bool = True
    cache_ttl: int = 3600  # Cache time-to-live in seconds
    
    # Provider selection
    preferred_provider: Optional[str] = None
    fallback_providers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration values."""
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError("temperature must be between 0.0 and 1.0")
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("top_p must be between 0.0 and 1.0")
        if self.max_response_tokens <= 0:
            raise ValueError("max_response_tokens must be positive")
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        if self.max_citations < 0:
            raise ValueError("max_citations cannot be negative")


@dataclass
class ResponseValidation:
    """Result of response validation."""
    
    is_valid: bool
    accuracy_score: float
    citation_coverage: float
    issues: List[str] = field(default_factory=list)
    
    # Detailed validation metrics
    claim_verification: Dict[str, float] = field(default_factory=dict)
    citation_accuracy: Dict[str, float] = field(default_factory=dict)
    educational_quality: float = 0.0
    
    def is_high_quality(self, accuracy_threshold: float = 0.8, citation_threshold: float = 0.7) -> bool:
        """Check if response meets high quality standards."""
        return (
            self.is_valid and 
            self.accuracy_score >= accuracy_threshold and 
            self.citation_coverage >= citation_threshold and
            len(self.issues) == 0
        )


@dataclass
class ResponseResult:
    """Complete result from response generation."""
    
    # Core response
    response_text: str
    query: str
    
    # Citations and sources
    citations: List[Citation]
    source_attribution: str = ""
    
    # Validation results
    validation: ResponseValidation = field(default_factory=lambda: ResponseValidation(
        is_valid=True, accuracy_score=0.0, citation_coverage=0.0
    ))
    
    # Generation metadata
    llm_response_metadata: Dict[str, Any] = field(default_factory=dict)
    generation_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    
    # Pipeline information
    context_tokens_used: int = 0
    citations_formatted: int = 0
    provider_used: str = ""
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseGenerationService:
    """
    Response Generation Service for philosophical tutoring responses.
    
    Integrates LLM generation, citation formatting, and educational validation
    to produce high-quality philosophical tutoring responses from composed contexts.
    """
    
    def __init__(
        self,
        llm_service: Optional[SimpleLLMService] = None,
        validation_service: Optional[ExpertValidationService] = None,
        citation_extraction_service: Optional[CitationExtractionService] = None,
        citation_validation_service: Optional[CitationValidationService] = None,
        citation_tracking_service: Optional[CitationTrackingService] = None,
        config: Optional[ResponseGenerationConfig] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize response generation service.
        
        Args:
            llm_service: LLM service for response generation
            validation_service: Service for response validation
            citation_extraction_service: Service for extracting citations from responses
            citation_validation_service: Service for validating citation accuracy
            citation_tracking_service: Service for tracking citation provenance
            config: Response generation configuration
            settings: Application settings
        """
        self.config = config or ResponseGenerationConfig()
        self.settings = settings or get_settings()
        
        # Initialize services
        self.llm_service = llm_service or SimpleLLMService(self.settings)
        self.validation_service = validation_service
        self.citation_extraction_service = citation_extraction_service or CitationExtractionService()
        self.citation_validation_service = citation_validation_service or CitationValidationService()
        self.citation_tracking_service = citation_tracking_service or CitationTrackingService()
        
        # Initialize caching
        self._response_cache: Dict[str, ResponseResult] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        logger.info(
            f"Initialized ResponseGenerationService with max_tokens: {self.config.max_response_tokens}, "
            f"validation: {self.config.enable_validation}"
        )
    
    async def generate_response(
        self,
        context_result: ContextResult,
        query: str,
        config: Optional[ResponseGenerationConfig] = None
    ) -> ResponseResult:
        """
        Generate educational response from composed context.
        
        Args:
            context_result: Composed context from retrieval pipeline
            query: Original user query
            config: Optional configuration override
            
        Returns:
            Complete response result with validation
            
        Raises:
            ResponseGenerationError: If generation fails
            ValidationError: If validation fails and fail_on_validation_error is True
        """
        start_time = time.time()
        generation_config = config or self.config
        
        try:
            # Check cache if enabled
            if generation_config.enable_caching:
                cache_key = self._generate_cache_key(context_result, query, generation_config)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    logger.debug(f"Returning cached response for query: {query[:50]}...")
                    return cached_result
            
            # Build messages for LLM
            messages = self._build_messages(context_result, query)
            
            # Generate response using LLM service
            llm_response = await self._generate_llm_response(
                messages, generation_config
            )
            
            # Extract citations from LLM response
            extraction_result = self.citation_extraction_service.extract_citations_from_response(
                llm_response.content, context_result, query
            )
            
            # Validate extracted citations
            validated_citations = []
            if extraction_result.citations:
                validation_results = await self.citation_validation_service.validate_citations_batch(
                    extraction_result.citations, context_result
                )
                validated_citations = [
                    citation for citation, result in zip(
                        extraction_result.citations, validation_results.citation_results
                    )
                    if result.is_valid or not generation_config.fail_on_validation_error
                ]
            
            # Track citation events
            for citation in validated_citations:
                self.citation_tracking_service.record_citation_event(
                    citation,
                    TrackingEventType.EXTRACTED,
                    CitationSource.LLM_RESPONSE,
                    processor="response_generation_service",
                    context={
                        "query": query,
                        "response_length": len(llm_response.content),
                        "extraction_confidence": extraction_result.accuracy_score
                    }
                )
            
            # Process additional citations from context (for completeness)
            context_citations = self._process_citations(context_result, generation_config)
            
            # Combine and deduplicate citations
            all_citations = validated_citations + context_citations
            if generation_config.deduplicate_citations:
                all_citations = self._deduplicate_citations(all_citations)
            
            # Format source attribution
            source_attribution = self._format_source_attribution(
                context_result, all_citations, generation_config
            )
            
            # Create initial response result
            response_result = ResponseResult(
                response_text=llm_response.content,
                query=query,
                citations=all_citations,
                source_attribution=source_attribution,
                llm_response_metadata={
                    "model": llm_response.model,
                    "provider": llm_response.provider,
                    "usage_tokens": llm_response.usage_tokens
                },
                generation_time=time.time() - start_time,
                token_usage={
                    "context_tokens": context_result.total_tokens,
                    "response_tokens": llm_response.usage_tokens
                },
                context_tokens_used=context_result.total_tokens,
                citations_formatted=len(all_citations),
                provider_used=llm_response.provider
            )
            
            # Validate response if enabled
            if generation_config.enable_validation and self.validation_service:
                try:
                    validation = await self._validate_response(
                        response_result, context_result, generation_config
                    )
                    response_result.validation = validation
                    
                    # Handle validation failures
                    if not validation.is_valid and generation_config.fail_on_validation_error:
                        raise ValidationError(
                            f"Response validation failed: {', '.join(validation.issues)}"
                        )
                        
                except Exception as e:
                    logger.warning(f"Response validation failed: {e}")
                    if generation_config.fail_on_validation_error:
                        raise ValidationError(f"Validation service error: {e}") from e
            
            # Cache result if enabled
            if generation_config.enable_caching and cache_key:
                self._cache_result(cache_key, response_result)
            
            logger.info(
                f"Response generated successfully: {len(response_result.response_text)} chars, "
                f"{len(citations)} citations, {response_result.generation_time:.3f}s"
            )
            
            return response_result
            
        except (ValidationError, CitationError):
            # Re-raise these specific errors
            raise
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise ResponseGenerationError(f"Response generation failed: {e}") from e
    
    async def generate_response_batch(
        self,
        context_results: List[ContextResult],
        queries: List[str],
        config: Optional[ResponseGenerationConfig] = None
    ) -> List[ResponseResult]:
        """
        Generate responses for multiple queries in batch.
        
        Args:
            context_results: List of composed contexts
            queries: List of queries
            config: Optional configuration override
            
        Returns:
            List of response results
        """
        if len(context_results) != len(queries):
            raise ResponseGenerationError(
                "context_results and queries must have the same length"
            )
        
        # Process all requests concurrently
        tasks = [
            self.generate_response(context_result, query, config)
            for context_result, query in zip(context_results, queries)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions in the results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch generation failed for query '{queries[i]}': {result}")
                    # Create error result
                    error_result = ResponseResult(
                        response_text=f"Error generating response: {result}",
                        query=queries[i],
                        citations=[],
                        validation=ResponseValidation(
                            is_valid=False,
                            accuracy_score=0.0,
                            citation_coverage=0.0,
                            issues=[str(result)]
                        )
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch response generation failed: {e}")
            raise ResponseGenerationError(f"Batch generation failed: {e}") from e
    
    def _build_messages(
        self, 
        context_result: ContextResult, 
        query: str
    ) -> List[LLMMessage]:
        """
        Build LLM messages from context and query.
        
        Args:
            context_result: Composed context
            query: User query
            
        Returns:
            List of LLM messages
        """
        messages = []
        
        # System message for philosophical tutoring
        system_prompt = self._build_system_prompt(context_result)
        messages.append(LLMMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt
        ))
        
        # User message with context and query
        user_prompt = self._build_user_prompt(context_result, query)
        messages.append(LLMMessage(
            role=MessageRole.USER,
            content=user_prompt
        ))
        
        return messages
    
    def _build_system_prompt(self, context_result: ContextResult) -> str:
        """Build system prompt for philosophical tutoring."""
        return (
            "You are an expert philosophy tutor specializing in classical philosophical texts. "
            "Your role is to provide educational, accurate, and well-cited responses that help "
            "students understand complex philosophical concepts.\n\n"
            
            "Guidelines:\n"
            "1. Always cite your sources using the provided references\n"
            "2. Distinguish between direct quotes, paraphrases, and your own analysis\n"
            "3. Structure your response clearly with logical progression\n"
            "4. Focus on educational value and conceptual understanding\n"
            "5. Use examples and analogies when helpful for comprehension\n"
            "6. Encourage further exploration and critical thinking\n\n"
            
            "Citation Format: Use classical references like 'Republic 514a' when available. "
            "Always indicate which parts of your response come from the provided sources."
        )
    
    def _build_user_prompt(self, context_result: ContextResult, query: str) -> str:
        """Build user prompt with context and query."""
        prompt_parts = []
        
        # Add composed context
        if context_result.composed_text:
            # Truncate if necessary to fit token limits
            context_text = context_result.composed_text
            if context_result.total_tokens > self.config.max_context_tokens:
                # Simple truncation - could be enhanced
                max_chars = self.config.max_context_tokens * 4  # rough estimate
                context_text = context_text[:max_chars] + "..."
            
            prompt_parts.append(f"**Source Material:**\n{context_text}")
        
        # Add citations if available
        if context_result.citations:
            citations_text = self._format_citations_for_prompt(context_result.citations)
            prompt_parts.append(f"**Citations:**\n{citations_text}")
        
        # Add the query
        prompt_parts.append(f"**Question:** {query}")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_llm_response(
        self,
        messages: List[LLMMessage],
        config: ResponseGenerationConfig
    ) -> LLMResponse:
        """Generate response using LLM service."""
        try:
            # Use preferred provider if specified
            provider = config.preferred_provider
            
            response = await self.llm_service.generate_response(
                messages=messages,
                provider=provider,
                max_tokens=config.max_response_tokens,
                temperature=config.temperature,
                top_p=config.top_p
            )
            
            return response
            
        except Exception as e:
            # Try fallback providers if configured
            if config.fallback_providers:
                for fallback_provider in config.fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_provider}")
                        response = await self.llm_service.generate_response(
                            messages=messages,
                            provider=fallback_provider,
                            max_tokens=config.max_response_tokens,
                            temperature=config.temperature,
                            top_p=config.top_p
                        )
                        return response
                    except Exception as fallback_error:
                        logger.warning(f"Fallback provider {fallback_provider} failed: {fallback_error}")
                        continue
            
            raise ResponseGenerationError(f"All LLM providers failed. Last error: {e}") from e
    
    def _process_citations(
        self,
        context_result: ContextResult,
        config: ResponseGenerationConfig
    ) -> List[Citation]:
        """Process and format citations from context."""
        if not context_result.citations:
            return []
        
        try:
            # Extract citations from context
            citations = []
            for citation_context in context_result.citations[:config.max_citations]:
                citations.append(citation_context.citation)
            
            # Deduplicate if enabled
            if config.deduplicate_citations:
                citations = self._deduplicate_citations(citations)
            
            return citations
            
        except Exception as e:
            raise CitationError(f"Citation processing failed: {e}") from e
    
    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Remove duplicate citations while preserving order."""
        seen_references = set()
        unique_citations = []
        
        for citation in citations:
            # Use source_reference as the deduplication key
            reference_key = citation.source_reference or str(citation.id)
            
            if reference_key not in seen_references:
                seen_references.add(reference_key)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _format_citations(
        self,
        citations: List[Citation],
        format_style: str = "classical"
    ) -> str:
        """Format citations according to specified style."""
        if not citations:
            return ""
        
        formatted_citations = []
        
        for i, citation in enumerate(citations, 1):
            if format_style == "classical":
                # Classical format: "Republic 514a"
                ref = citation.source_reference or f"Citation {citation.id}"
                formatted_citations.append(f"{ref}")
                
            elif format_style == "modern":
                # Modern format: "(Plato, Republic, 514a)"
                ref = citation.source_reference or ""
                if ref:
                    formatted_citations.append(f"({ref})")
                else:
                    formatted_citations.append(f"(Citation {citation.id})")
                    
            elif format_style == "footnote":
                # Footnote format: "[1] Republic 514a"
                ref = citation.source_reference or f"Citation {citation.id}"
                formatted_citations.append(f"[{i}] {ref}")
            
            else:
                # Default to source reference
                formatted_citations.append(citation.source_reference or str(citation.id))
        
        return ", ".join(formatted_citations)
    
    def _format_citations_for_prompt(self, citation_contexts) -> str:
        """Format citation contexts for inclusion in prompts."""
        if not citation_contexts:
            return ""
        
        formatted = []
        for i, ctx in enumerate(citation_contexts, 1):
            citation = ctx.citation
            formatted.append(
                f"[{i}] {citation.text}\n    — {citation.source_reference or 'Unknown source'}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_source_attribution(
        self,
        context_result: ContextResult,
        citations: List[Citation],
        config: ResponseGenerationConfig
    ) -> str:
        """Format complete source attribution."""
        if not config.include_source_attribution:
            return ""
        
        attribution_parts = []
        
        # Add formatted citations
        if citations:
            citations_text = self._format_citations(citations, config.citation_format)
            attribution_parts.append(f"Sources: {citations_text}")
        
        # Add retrieval metadata
        if context_result.metadata:
            methods = context_result.metadata.get('retrieval_methods', [])
            if methods:
                attribution_parts.append(f"Retrieved via: {', '.join(methods)}")
        
        return " | ".join(attribution_parts)
    
    async def _validate_response(
        self,
        response_result: ResponseResult,
        context_result: ContextResult,
        config: ResponseGenerationConfig
    ) -> ResponseValidation:
        """Validate response using expert validation service."""
        if not self.validation_service:
            # Return basic validation if no service available
            return ResponseValidation(
                is_valid=True,
                accuracy_score=0.8,  # Default assumption
                citation_coverage=len(response_result.citations) / max(len(context_result.citations), 1)
            )
        
        try:
            # Use validation service to check response quality
            validation = self.validation_service.validate_response(
                response_text=response_result.response_text,
                query=response_result.query,
                context_result=context_result,
                citations=response_result.citations
            )
            
            return validation
            
        except Exception as e:
            logger.error(f"Validation service error: {e}")
            # Return failed validation
            return ResponseValidation(
                is_valid=False,
                accuracy_score=0.0,
                citation_coverage=0.0,
                issues=[f"Validation service error: {e}"]
            )
    
    def _generate_cache_key(
        self,
        context_result: ContextResult,
        query: str,
        config: ResponseGenerationConfig
    ) -> str:
        """Generate cache key for response request."""
        key_components = [
            query,
            context_result.composed_text,
            str(config.max_response_tokens),
            str(config.temperature),
            config.citation_format,
            str(len(context_result.citations))
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ResponseResult]:
        """Get cached response result if valid."""
        if cache_key not in self._response_cache:
            return None
        
        # Check cache TTL
        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > self.config.cache_ttl:
            # Remove expired cache entry
            del self._response_cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._response_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: ResponseResult) -> None:
        """Cache response result."""
        self._response_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        # Limit cache size (simple LRU)
        if len(self._response_cache) > 50:  # Max 50 cached results
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._response_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    def clear_cache(self) -> None:
        """Clear response cache."""
        self._response_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Response generation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cached_responses': len(self._response_cache),
            'cache_hit_potential': len(self._response_cache) > 0,
            'oldest_entry_age': (
                time.time() - min(self._cache_timestamps.values())
                if self._cache_timestamps else 0
            )
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'llm_service_info': self.llm_service.get_provider_info() if self.llm_service else {},
            'validation_enabled': self.config.enable_validation,
            'cache_stats': self.get_cache_stats(),
            'config': {
                'max_response_tokens': self.config.max_response_tokens,
                'temperature': self.config.temperature,
                'citation_format': self.config.citation_format,
                'max_citations': self.config.max_citations
            }
        }


# Factory function following established pattern
def create_response_generation_service(
    llm_service: Optional[SimpleLLMService] = None,
    validation_service: Optional[ExpertValidationService] = None,
    citation_extraction_service: Optional[CitationExtractionService] = None,
    citation_validation_service: Optional[CitationValidationService] = None,
    citation_tracking_service: Optional[CitationTrackingService] = None,
    config: Optional[ResponseGenerationConfig] = None,
    settings: Optional[Settings] = None
) -> ResponseGenerationService:
    """
    Create response generation service with optional dependencies.
    
    Args:
        llm_service: Optional LLM service
        validation_service: Optional validation service
        citation_extraction_service: Optional citation extraction service
        citation_validation_service: Optional citation validation service
        citation_tracking_service: Optional citation tracking service
        config: Optional configuration
        settings: Optional settings
        
    Returns:
        Configured ResponseGenerationService instance
    """
    return ResponseGenerationService(
        llm_service=llm_service,
        validation_service=validation_service,
        citation_extraction_service=citation_extraction_service,
        citation_validation_service=citation_validation_service,
        citation_tracking_service=citation_tracking_service,
        config=config,
        settings=settings
    )