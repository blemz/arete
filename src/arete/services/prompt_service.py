"""
Prompt service for managing philosophical tutoring prompts.

This service coordinates prompt template generation, provider-specific optimization,
and integration with the SimpleLLMService for philosophical tutoring scenarios.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from arete.services.prompt_template import (
    BasePromptTemplate,
    PhilosophicalTutoringTemplate,
    ExplanationTemplate,
    PromptType,
    PromptContext,
    PromptResult,
    PhilosophicalContext,
    Citation
)
from arete.services.simple_llm_service import SimpleLLMService
from arete.services.llm_provider import LLMMessage, MessageRole, LLMResponse
from arete.config import Settings, get_settings

# Setup logger
logger = logging.getLogger(__name__)


class PromptTemplateFactory:
    """
    Factory for creating provider-specific prompt templates.
    
    Manages the creation and caching of prompt templates optimized for
    different LLM providers and philosophical tutoring scenarios.
    """
    
    def __init__(self):
        """Initialize template factory."""
        self._template_cache: Dict[str, BasePromptTemplate] = {}
        self._template_registry: Dict[PromptType, Type[BasePromptTemplate]] = {
            PromptType.TUTORING: PhilosophicalTutoringTemplate,
            PromptType.EXPLANATION: ExplanationTemplate,
            # Additional templates can be registered here
        }
    
    def get_template(self, provider: str, prompt_type: PromptType) -> BasePromptTemplate:
        """
        Get or create a prompt template for the specified provider and type.
        
        Args:
            provider: LLM provider name (ollama, anthropic, etc.)
            prompt_type: Type of prompt template needed
            
        Returns:
            Configured prompt template
            
        Raises:
            ValueError: If prompt type is not supported
        """
        cache_key = f"{provider}:{prompt_type.value}"
        
        # Check cache first
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Get template class
        template_class = self._template_registry.get(prompt_type)
        if not template_class:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
        
        # Create and cache template
        template = template_class(provider)
        self._template_cache[cache_key] = template
        
        logger.info(f"Created prompt template: {provider}:{prompt_type.value}")
        return template
    
    def register_template(self, prompt_type: PromptType, template_class: Type[BasePromptTemplate]) -> None:
        """
        Register a new template type.
        
        Args:
            prompt_type: Type of prompt this template handles
            template_class: Template class to register
        """
        self._template_registry[prompt_type] = template_class
        logger.info(f"Registered template class for {prompt_type.value}")
    
    def list_supported_types(self) -> List[PromptType]:
        """Get list of supported prompt types."""
        return list(self._template_registry.keys())
    
    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared")


@dataclass 
class TutoringRequest:
    """Request for philosophical tutoring assistance."""
    query: str
    student_level: str = "undergraduate"
    philosophical_context: Optional[PhilosophicalContext] = None
    learning_objective: Optional[str] = None
    retrieved_passages: Optional[List[str]] = None
    citations: Optional[List[Citation]] = None
    previous_context: Optional[str] = None
    provider: Optional[str] = None
    prompt_type: PromptType = PromptType.TUTORING
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.retrieved_passages is None:
            self.retrieved_passages = []
        if self.citations is None:
            self.citations = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TutoringResponse:
    """Response from philosophical tutoring service."""
    content: str
    prompt_used: PromptResult
    llm_response: LLMResponse
    citations_provided: List[Citation]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class PromptService:
    """
    Service for generating and managing philosophical tutoring prompts.
    
    Coordinates prompt template generation with LLM providers to deliver
    optimized philosophical tutoring experiences.
    """
    
    def __init__(self, settings: Optional[Settings] = None, llm_service: Optional[SimpleLLMService] = None):
        """
        Initialize prompt service.
        
        Args:
            settings: Application configuration
            llm_service: LLM service instance (creates new if None)
        """
        self.settings = settings or get_settings()
        self.llm_service = llm_service or SimpleLLMService(self.settings)
        self.template_factory = PromptTemplateFactory()
        
        logger.info("PromptService initialized")
    
    async def generate_tutoring_response(self, request: TutoringRequest) -> TutoringResponse:
        """
        Generate a philosophical tutoring response.
        
        Args:
            request: Tutoring request with query and context
            
        Returns:
            Tutoring response with content and metadata
            
        Raises:
            ValueError: If request parameters are invalid
            Exception: If response generation fails
        """
        # Validate request
        if not request.query.strip():
            raise ValueError("Query cannot be empty")
        
        # Determine provider
        provider = request.provider or self.llm_service.get_active_provider_name()
        
        # Create prompt context
        context = PromptContext(
            query=request.query,
            retrieved_passages=request.retrieved_passages,
            citations=request.citations,
            philosophical_context=request.philosophical_context,
            student_level=request.student_level,
            learning_objective=request.learning_objective,
            previous_context=request.previous_context,
            metadata=request.metadata
        )
        
        # Generate prompt
        prompt_result = await self.generate_prompt(context, request.prompt_type, provider)
        
        # Create messages for LLM
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=prompt_result.system_prompt),
            LLMMessage(role=MessageRole.USER, content=prompt_result.user_prompt)
        ]
        
        # Generate response
        llm_response = await self.llm_service.generate_response(
            messages=messages,
            provider=provider
        )
        
        # Create tutoring response
        response = TutoringResponse(
            content=llm_response.content,
            prompt_used=prompt_result,
            llm_response=llm_response,
            citations_provided=prompt_result.citations_included,
            metadata={
                "request_metadata": request.metadata,
                "prompt_metadata": prompt_result.metadata,
                "llm_metadata": llm_response.metadata,
                "provider_used": provider,
                "token_estimate": prompt_result.token_estimate
            }
        )
        
        logger.info(f"Generated tutoring response: {len(response.content)} chars, "
                   f"{len(response.citations_provided)} citations")
        
        return response
    
    async def generate_prompt(
        self, 
        context: PromptContext, 
        prompt_type: PromptType = PromptType.TUTORING,
        provider: Optional[str] = None
    ) -> PromptResult:
        """
        Generate a prompt for the specified context and type.
        
        Args:
            context: Prompt generation context
            prompt_type: Type of prompt to generate
            provider: LLM provider (uses active if None)
            
        Returns:
            Generated prompt result
        """
        provider = provider or self.llm_service.get_active_provider_name()
        
        # Get appropriate template
        template = self.template_factory.get_template(provider, prompt_type)
        
        # Generate prompt
        prompt_result = template.generate(context)
        
        logger.info(f"Generated {prompt_type.value} prompt for {provider}: "
                   f"{prompt_result.token_estimate} tokens")
        
        return prompt_result
    
    def create_citation_from_passage(
        self,
        text: str,
        source: str,
        author: Optional[str] = None,
        work: Optional[str] = None,
        reference: Optional[str] = None,
        confidence: float = 1.0
    ) -> Citation:
        """
        Create a Citation object from passage information.
        
        Args:
            text: Citation text content
            source: Source identifier
            author: Author name
            work: Work title
            reference: Specific reference (e.g., "Republic 514a")
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            Citation object
        """
        return Citation(
            text=text,
            source=source,
            author=author,
            work=work,
            reference=reference,
            confidence=confidence
        )
    
    def get_supported_prompt_types(self) -> List[PromptType]:
        """Get list of supported prompt types."""
        return self.template_factory.list_supported_types()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers and configuration."""
        llm_info = self.llm_service.get_provider_info()
        return {
            "llm_providers": llm_info,
            "supported_prompt_types": [pt.value for pt in self.get_supported_prompt_types()],
            "active_provider": llm_info["active_provider"],
            "template_cache_size": len(self.template_factory._template_cache)
        }
    
    def clear_template_cache(self) -> None:
        """Clear the prompt template cache."""
        self.template_factory.clear_cache()


# Convenience functions
def get_prompt_service(settings: Optional[Settings] = None) -> PromptService:
    """Get a PromptService instance."""
    return PromptService(settings)


async def quick_tutoring_response(
    query: str,
    retrieved_passages: Optional[List[str]] = None,
    citations: Optional[List[Citation]] = None,
    student_level: str = "undergraduate",
    provider: Optional[str] = None
) -> str:
    """
    Quick utility function for generating tutoring responses.
    
    Args:
        query: Student's question
        retrieved_passages: Relevant source passages
        citations: Source citations
        student_level: Academic level
        provider: LLM provider to use
        
    Returns:
        Tutoring response content
    """
    service = get_prompt_service()
    
    request = TutoringRequest(
        query=query,
        retrieved_passages=retrieved_passages or [],
        citations=citations or [],
        student_level=student_level,
        provider=provider
    )
    
    response = await service.generate_tutoring_response(request)
    return response.content


if __name__ == "__main__":
    # Demo/test
    import asyncio
    
    async def demo():
        print("🤖 PromptService Demo")
        print("=" * 30)
        
        service = get_prompt_service()
        info = service.get_provider_info()
        
        print(f"Active Provider: {info['active_provider']}")
        print(f"Supported Prompt Types: {', '.join(info['supported_prompt_types'])}")
        
        # Test prompt generation
        context = PromptContext(
            query="What is Plato's theory of Forms?",
            student_level="undergraduate",
            philosophical_context=PhilosophicalContext.ANCIENT
        )
        
        try:
            prompt_result = await service.generate_prompt(context)
            print(f"\nGenerated prompt ({prompt_result.token_estimate} tokens)")
            print(f"System: {prompt_result.system_prompt[:100]}...")
            print(f"User: {prompt_result.user_prompt[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    asyncio.run(demo())