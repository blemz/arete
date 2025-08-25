"""
Intelligent LLM provider routing system for Arete Graph-RAG.

This module provides smart routing of LLM requests based on:
- Provider availability and health
- Cost optimization
- Quality requirements  
- Performance characteristics
- Philosophical accuracy for educational content
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import asyncio

from arete.services.llm_provider import (
    MultiProviderLLMService, LLMProvider, LLMMessage, LLMResponse,
    LLMProviderError, ProviderUnavailableError, RateLimitError
)
from arete.config import Settings

# Setup logger
logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Request priority levels for routing decisions."""
    LOW = "low"           # Cost-optimized, slower responses acceptable
    NORMAL = "normal"     # Balanced cost/quality
    HIGH = "high"         # Quality-prioritized, faster response
    CRITICAL = "critical" # Best available, ignore cost


class RequestType(Enum):
    """Type of request for specialized routing."""
    GENERAL = "general"           # General-purpose text generation
    PHILOSOPHICAL = "philosophical"  # Educational philosophical content
    ANALYTICAL = "analytical"     # Complex reasoning and analysis
    CREATIVE = "creative"         # Creative writing tasks
    FACTUAL = "factual"          # Fact-based queries


@dataclass
class ProviderCapabilities:
    """Capabilities and characteristics of an LLM provider."""
    name: str
    quality_score: float = 0.7      # 0.0-1.0, higher is better
    speed_score: float = 0.5        # 0.0-1.0, higher is faster
    cost_score: float = 0.5         # 0.0-1.0, higher is more expensive
    philosophical_accuracy: float = 0.5  # 0.0-1.0, educational accuracy
    max_tokens: int = 4000
    supports_streaming: bool = True
    reliability_score: float = 0.8  # 0.0-1.0, based on historical uptime


@dataclass
class RoutingRequest:
    """Request parameters for intelligent routing."""
    messages: List[LLMMessage]
    priority: RequestPriority = RequestPriority.NORMAL
    request_type: RequestType = RequestType.GENERAL
    max_cost: Optional[float] = None  # Maximum acceptable cost in USD
    min_quality: Optional[float] = None  # Minimum quality score required
    preferred_providers: Optional[List[str]] = None
    exclude_providers: Optional[List[str]] = None
    require_streaming: bool = False


class IntelligentLLMRouter:
    """
    Intelligent router for LLM provider selection.
    
    Routes requests to optimal providers based on:
    - Request characteristics and requirements
    - Provider capabilities and current status
    - Cost optimization and quality thresholds
    - Historical performance and reliability
    """
    
    def __init__(self, llm_service: MultiProviderLLMService, settings: Settings):
        """
        Initialize the intelligent router.
        
        Args:
            llm_service: Multi-provider LLM service instance
            settings: Application configuration
        """
        self.llm_service = llm_service
        self.settings = settings
        
        # Provider capabilities database
        self.provider_capabilities = self._initialize_provider_capabilities()
        
        # Historical performance tracking
        self.performance_history: Dict[str, Dict[str, float]] = {}
        
        # Routing statistics
        self.routing_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "cost_optimized": 0,
            "quality_upgrades": 0,
            "provider_failovers": 0
        }
    
    def _initialize_provider_capabilities(self) -> Dict[str, ProviderCapabilities]:
        """Initialize provider capabilities based on known characteristics."""
        return {
            "ollama": ProviderCapabilities(
                name="ollama",
                quality_score=0.7,
                speed_score=0.9,  # Local execution
                cost_score=0.0,   # Free local usage
                philosophical_accuracy=0.6,
                max_tokens=8192,
                supports_streaming=True,
                reliability_score=0.9  # Local, highly reliable
            ),
            "openrouter": ProviderCapabilities(
                name="openrouter",
                quality_score=0.8,
                speed_score=0.7,
                cost_score=0.3,  # Variable pricing
                philosophical_accuracy=0.7,
                max_tokens=32000,
                supports_streaming=True,
                reliability_score=0.8
            ),
            "gemini": ProviderCapabilities(
                name="gemini",
                quality_score=0.8,
                speed_score=0.8,
                cost_score=0.2,  # Competitive pricing
                philosophical_accuracy=0.8,  # Good for educational content
                max_tokens=32000,
                supports_streaming=True,
                reliability_score=0.8
            ),
            "anthropic": ProviderCapabilities(
                name="anthropic",
                quality_score=0.9,  # High quality responses
                speed_score=0.6,
                cost_score=0.8,     # Premium pricing
                philosophical_accuracy=0.9,  # Excellent for philosophy
                max_tokens=200000,  # Large context
                supports_streaming=True,
                reliability_score=0.9
            ),
            "openai": ProviderCapabilities(
                name="openai",
                quality_score=0.9,  # High quality
                speed_score=0.7,
                cost_score=0.7,     # Premium pricing
                philosophical_accuracy=0.8,
                max_tokens=128000,  # Large context for GPT-4
                supports_streaming=True,
                reliability_score=0.9
            )
        }
    
    async def route_request(self, request: RoutingRequest) -> LLMResponse:
        """
        Route request to optimal provider.
        
        Args:
            request: Routing request with parameters and requirements
            
        Returns:
            LLM response from selected provider
            
        Raises:
            LLMProviderError: If no suitable provider available
        """
        self.routing_stats["total_requests"] += 1
        
        try:
            # Get available providers
            available_providers = self._get_available_providers()
            
            if not available_providers:
                raise LLMProviderError("No providers available for routing")
            
            # Score and rank providers for this request
            provider_scores = self._score_providers(request, available_providers)
            
            if not provider_scores:
                raise LLMProviderError("No providers meet request requirements")
            
            # Sort by score (highest first)
            ranked_providers = sorted(
                provider_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Try providers in order until success
            last_error = None
            
            for provider_name, score in ranked_providers:
                try:
                    logger.info(f"Routing request to {provider_name} (score: {score:.3f})")
                    
                    response = await self.llm_service.generate_response(
                        messages=request.messages,
                        preferred_provider=provider_name,
                        **self._get_provider_kwargs(request)
                    )
                    
                    # Track successful routing
                    self.routing_stats["successful_routes"] += 1
                    self._update_performance_history(provider_name, True, score)
                    
                    # Add routing metadata
                    response.metadata.update({
                        "router_selected_provider": provider_name,
                        "router_score": score,
                        "router_alternatives": len(ranked_providers) - 1,
                        "request_priority": request.priority.value,
                        "request_type": request.request_type.value
                    })
                    
                    return response
                    
                except (ProviderUnavailableError, RateLimitError) as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    self._update_performance_history(provider_name, False, score)
                    self.routing_stats["provider_failovers"] += 1
                    last_error = e
                    continue
                    
                except Exception as e:
                    logger.error(f"Unexpected error from provider {provider_name}: {e}")
                    self._update_performance_history(provider_name, False, score)
                    last_error = e
                    continue
            
            # All providers failed
            error_msg = "All suitable providers failed for request"
            if last_error:
                error_msg += f". Last error: {last_error}"
            
            raise LLMProviderError(error_msg)
            
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            raise
    
    def _get_available_providers(self) -> List[str]:
        """Get list of currently available provider names."""
        available = []
        
        for provider in self.llm_service._providers:
            if provider.is_available:
                available.append(provider.name)
        
        return available
    
    def _score_providers(
        self, 
        request: RoutingRequest, 
        available_providers: List[str]
    ) -> Dict[str, float]:
        """
        Score providers based on request requirements.
        
        Args:
            request: Routing request
            available_providers: List of available provider names
            
        Returns:
            Dictionary mapping provider names to scores (0.0-1.0)
        """
        scores = {}
        
        for provider_name in available_providers:
            if provider_name not in self.provider_capabilities:
                continue
                
            capabilities = self.provider_capabilities[provider_name]
            
            # Apply exclusion filters
            if request.exclude_providers and provider_name in request.exclude_providers:
                continue
            
            # Check minimum quality requirement
            if request.min_quality and capabilities.quality_score < request.min_quality:
                continue
            
            # Check streaming requirement
            if request.require_streaming and not capabilities.supports_streaming:
                continue
            
            # Calculate base score
            score = self._calculate_provider_score(request, capabilities)
            
            # Apply historical performance adjustment
            performance_modifier = self._get_performance_modifier(provider_name)
            score *= performance_modifier
            
            # Boost preferred providers
            if request.preferred_providers and provider_name in request.preferred_providers:
                score *= 1.2  # 20% boost for preferred providers
            
            scores[provider_name] = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        return scores
    
    def _calculate_provider_score(
        self, 
        request: RoutingRequest, 
        capabilities: ProviderCapabilities
    ) -> float:
        """Calculate base score for a provider given request requirements."""
        
        # Priority-based weighting
        if request.priority == RequestPriority.LOW:
            # Cost-optimized: prioritize low cost
            cost_weight = 0.5
            quality_weight = 0.2
            speed_weight = 0.1
            reliability_weight = 0.2
            
        elif request.priority == RequestPriority.HIGH:
            # Quality-prioritized: prioritize quality and speed
            cost_weight = 0.1
            quality_weight = 0.4
            speed_weight = 0.3
            reliability_weight = 0.2
            
        elif request.priority == RequestPriority.CRITICAL:
            # Best available: maximum quality and reliability
            cost_weight = 0.0
            quality_weight = 0.5
            speed_weight = 0.2
            reliability_weight = 0.3
            
        else:  # NORMAL
            # Balanced approach
            cost_weight = 0.25
            quality_weight = 0.3
            speed_weight = 0.25
            reliability_weight = 0.2
        
        # Request type adjustments
        if request.request_type == RequestType.PHILOSOPHICAL:
            # Boost philosophical accuracy for educational content
            philosophical_weight = 0.3
            quality_weight *= 0.8  # Slightly reduce general quality weight
        else:
            philosophical_weight = 0.0
        
        # Calculate weighted score
        # Note: Cost score is inverted (lower cost = higher score)
        cost_score = 1.0 - capabilities.cost_score
        
        base_score = (
            cost_score * cost_weight +
            capabilities.quality_score * quality_weight +
            capabilities.speed_score * speed_weight +
            capabilities.reliability_score * reliability_weight +
            capabilities.philosophical_accuracy * philosophical_weight
        )
        
        return base_score
    
    def _get_performance_modifier(self, provider_name: str) -> float:
        """Get performance modifier based on historical success rate."""
        if provider_name not in self.performance_history:
            return 1.0  # No history, no modifier
        
        history = self.performance_history[provider_name]
        success_rate = history.get("success_rate", 1.0)
        
        # Apply performance modifier: 0.8x to 1.2x based on success rate
        return 0.8 + (success_rate * 0.4)
    
    def _update_performance_history(
        self, 
        provider_name: str, 
        success: bool, 
        score: float
    ) -> None:
        """Update performance history for provider."""
        if provider_name not in self.performance_history:
            self.performance_history[provider_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "success_rate": 1.0,
                "average_score": 0.0
            }
        
        history = self.performance_history[provider_name]
        history["total_requests"] += 1
        
        if success:
            history["successful_requests"] += 1
        
        # Update success rate
        history["success_rate"] = history["successful_requests"] / history["total_requests"]
        
        # Update average score (exponential moving average)
        alpha = 0.1  # Learning rate
        history["average_score"] = (
            alpha * score + (1 - alpha) * history["average_score"]
        )
    
    def _get_provider_kwargs(self, request: RoutingRequest) -> Dict[str, Any]:
        """Get provider-specific kwargs from routing request."""
        kwargs = {}
        
        # Add standard LLM parameters
        if hasattr(request, 'max_tokens'):
            kwargs['max_tokens'] = request.max_tokens
        if hasattr(request, 'temperature'):
            kwargs['temperature'] = request.temperature
        if hasattr(request, 'model'):
            kwargs['model'] = request.model
            
        return kwargs
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and performance metrics."""
        total_requests = self.routing_stats["total_requests"]
        success_rate = (
            self.routing_stats["successful_routes"] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": total_requests,
            "success_rate": success_rate,
            "cost_optimized_requests": self.routing_stats["cost_optimized"],
            "quality_upgrades": self.routing_stats["quality_upgrades"], 
            "provider_failovers": self.routing_stats["provider_failovers"],
            "provider_performance": dict(self.performance_history),
            "active_providers": len(self._get_available_providers())
        }
    
    def update_provider_capabilities(
        self, 
        provider_name: str, 
        capabilities: ProviderCapabilities
    ) -> None:
        """Update capabilities for a provider."""
        self.provider_capabilities[provider_name] = capabilities
        logger.info(f"Updated capabilities for provider: {provider_name}")
    
    def get_recommended_provider(
        self, 
        priority: RequestPriority = RequestPriority.NORMAL,
        request_type: RequestType = RequestType.GENERAL
    ) -> Optional[str]:
        """
        Get recommended provider for given priority and request type.
        
        Args:
            priority: Request priority level
            request_type: Type of request
            
        Returns:
            Recommended provider name or None if none available
        """
        available_providers = self._get_available_providers()
        
        if not available_providers:
            return None
        
        # Create minimal routing request for scoring
        dummy_request = RoutingRequest(
            messages=[],  # Empty for recommendation
            priority=priority,
            request_type=request_type
        )
        
        provider_scores = self._score_providers(dummy_request, available_providers)
        
        if not provider_scores:
            return None
        
        # Return highest scoring provider
        return max(provider_scores.items(), key=lambda x: x[1])[0]


# Convenience function for creating router
def create_llm_router(
    llm_service: Optional[MultiProviderLLMService] = None,
    settings: Optional[Settings] = None
) -> IntelligentLLMRouter:
    """
    Create an intelligent LLM router.
    
    Args:
        llm_service: Multi-provider LLM service (creates default if None)
        settings: Application settings (uses default if None)
        
    Returns:
        Configured intelligent router
    """
    if settings is None:
        from arete.config import get_settings
        settings = get_settings()
    
    if llm_service is None:
        from arete.services.llm_provider import create_llm_service
        llm_service = create_llm_service(settings)
    
    return IntelligentLLMRouter(llm_service, settings)


# Utility functions for common routing patterns
def create_philosophical_request(
    messages: List[LLMMessage],
    priority: RequestPriority = RequestPriority.HIGH
) -> RoutingRequest:
    """Create a routing request optimized for philosophical content."""
    return RoutingRequest(
        messages=messages,
        priority=priority,
        request_type=RequestType.PHILOSOPHICAL,
        min_quality=0.7,  # Require high quality for educational content
        preferred_providers=["anthropic", "openai", "gemini"]  # Best for philosophy
    )


def create_cost_optimized_request(
    messages: List[LLMMessage]
) -> RoutingRequest:
    """Create a cost-optimized routing request."""
    return RoutingRequest(
        messages=messages,
        priority=RequestPriority.LOW,
        request_type=RequestType.GENERAL,
        max_cost=0.01,  # 1 cent maximum
        preferred_providers=["ollama"]  # Free local execution preferred
    )


def create_high_quality_request(
    messages: List[LLMMessage],
    request_type: RequestType = RequestType.ANALYTICAL
) -> RoutingRequest:
    """Create a high-quality routing request."""
    return RoutingRequest(
        messages=messages,
        priority=RequestPriority.CRITICAL,
        request_type=request_type,
        min_quality=0.8,  # Require very high quality
        preferred_providers=["anthropic", "openai"]  # Premium providers
    )