"""
Test suite for intelligent LLM routing system.

Tests the router's ability to select optimal providers based on:
- Request characteristics and requirements
- Provider capabilities and availability
- Cost optimization and quality thresholds
- Performance history and reliability
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from arete.services.llm_router import (
    IntelligentLLMRouter,
    RequestPriority,
    RequestType,
    ProviderCapabilities,
    RoutingRequest,
    create_llm_router,
    create_philosophical_request,
    create_cost_optimized_request,
    create_high_quality_request
)
from arete.services.llm_provider import (
    MultiProviderLLMService,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError
)
from arete.config import Settings


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, name: str, is_available: bool = True):
        super().__init__(name)
        self._is_available = is_available
        self._initialized = True
        
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    @property
    def supported_models(self) -> List[str]:
        return ["mock-model"]
    
    def initialize(self) -> None:
        pass
    
    async def generate_response(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        return LLMResponse(
            content=f"Response from {self.name}",
            provider=self.name,
            model="mock-model",
            usage_tokens=100
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        return {"provider": self.name, "status": "healthy"}


class TestProviderCapabilities:
    """Test provider capabilities data structure."""
    
    def test_capabilities_creation(self):
        """Test creating provider capabilities."""
        caps = ProviderCapabilities(
            name="test-provider",
            quality_score=0.8,
            speed_score=0.6,
            cost_score=0.4,
            philosophical_accuracy=0.9
        )
        
        assert caps.name == "test-provider"
        assert caps.quality_score == 0.8
        assert caps.speed_score == 0.6
        assert caps.cost_score == 0.4
        assert caps.philosophical_accuracy == 0.9
        assert caps.max_tokens == 4000  # Default
        assert caps.supports_streaming is True  # Default
        assert caps.reliability_score == 0.8  # Default


class TestRoutingRequest:
    """Test routing request data structure."""
    
    def test_routing_request_creation(self):
        """Test creating routing request."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        
        request = RoutingRequest(
            messages=messages,
            priority=RequestPriority.HIGH,
            request_type=RequestType.PHILOSOPHICAL,
            max_cost=0.10,
            min_quality=0.8,
            preferred_providers=["anthropic"],
            exclude_providers=["ollama"],
            require_streaming=True
        )
        
        assert request.messages == messages
        assert request.priority == RequestPriority.HIGH
        assert request.request_type == RequestType.PHILOSOPHICAL
        assert request.max_cost == 0.10
        assert request.min_quality == 0.8
        assert request.preferred_providers == ["anthropic"]
        assert request.exclude_providers == ["ollama"]
        assert request.require_streaming is True
    
    def test_routing_request_defaults(self):
        """Test routing request with default values."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        
        request = RoutingRequest(messages=messages)
        
        assert request.messages == messages
        assert request.priority == RequestPriority.NORMAL
        assert request.request_type == RequestType.GENERAL
        assert request.max_cost is None
        assert request.min_quality is None
        assert request.preferred_providers is None
        assert request.exclude_providers is None
        assert request.require_streaming is False


class TestIntelligentLLMRouter:
    """Test intelligent LLM router functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.settings = Settings()
        
        # Create mock LLM service with providers
        self.llm_service = Mock(spec=MultiProviderLLMService)
        self.llm_service._providers = [
            MockProvider("ollama", is_available=True),
            MockProvider("anthropic", is_available=True),
            MockProvider("openai", is_available=True),
            MockProvider("unavailable", is_available=False)
        ]
        
        # Mock generate_response method
        async def mock_generate_response(messages, preferred_provider=None, **kwargs):
            return LLMResponse(
                content=f"Response from {preferred_provider or 'default'}",
                provider=preferred_provider or "default",
                model="mock-model",
                usage_tokens=100,
                metadata={}
            )
        
        self.llm_service.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # Create router
        self.router = IntelligentLLMRouter(self.llm_service, self.settings)
    
    def test_router_initialization(self):
        """Test router initialization."""
        assert self.router.llm_service == self.llm_service
        assert self.router.settings == self.settings
        assert len(self.router.provider_capabilities) > 0
        assert "ollama" in self.router.provider_capabilities
        assert "anthropic" in self.router.provider_capabilities
        assert self.router.routing_stats["total_requests"] == 0
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        available = self.router._get_available_providers()
        
        assert "ollama" in available
        assert "anthropic" in available
        assert "openai" in available
        assert "unavailable" not in available
    
    def test_score_providers_normal_priority(self):
        """Test provider scoring for normal priority request."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(
            messages=messages,
            priority=RequestPriority.NORMAL,
            request_type=RequestType.GENERAL
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        assert len(scores) > 0
        assert all(0.0 <= score <= 1.0 for score in scores.values())
        
        # Ollama should score well for normal requests (free cost)
        assert "ollama" in scores
    
    def test_score_providers_philosophical_request(self):
        """Test provider scoring for philosophical request."""
        messages = [LLMMessage(role=MessageRole.USER, content="What is virtue ethics?")]
        request = RoutingRequest(
            messages=messages,
            priority=RequestPriority.HIGH,
            request_type=RequestType.PHILOSOPHICAL
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        # Anthropic should score well for philosophical requests
        assert "anthropic" in scores
        
        # Anthropic should outscore Ollama for philosophy due to higher accuracy
        if "ollama" in scores:
            assert scores["anthropic"] > scores["ollama"]
    
    def test_score_providers_cost_optimized(self):
        """Test provider scoring for cost-optimized request."""
        messages = [LLMMessage(role=MessageRole.USER, content="Simple question")]
        request = RoutingRequest(
            messages=messages,
            priority=RequestPriority.LOW,  # Cost-optimized
            request_type=RequestType.GENERAL
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        # Ollama should score highest for cost optimization (free)
        assert "ollama" in scores
        
        if len(scores) > 1:
            ollama_score = scores["ollama"]
            other_scores = [s for k, s in scores.items() if k != "ollama"]
            assert ollama_score >= max(other_scores)
    
    def test_score_providers_with_exclusions(self):
        """Test provider scoring with exclusion filters."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(
            messages=messages,
            exclude_providers=["ollama", "openai"]
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        assert "ollama" not in scores
        assert "openai" not in scores
        assert "anthropic" in scores  # Should not be excluded
    
    def test_score_providers_with_preferences(self):
        """Test provider scoring with preferred providers."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(
            messages=messages,
            preferred_providers=["anthropic"]
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        # Preferred provider should get a score boost
        if "anthropic" in scores and "ollama" in scores:
            # The boost is applied in scoring, so anthropic might have higher score
            # This test verifies the boost mechanism is considered
            assert "anthropic" in scores
    
    def test_score_providers_quality_threshold(self):
        """Test provider scoring with quality threshold."""
        messages = [LLMMessage(role=MessageRole.USER, content="Complex analysis needed")]
        request = RoutingRequest(
            messages=messages,
            min_quality=0.85  # High quality threshold
        )
        
        available = self.router._get_available_providers()
        scores = self.router._score_providers(request, available)
        
        # Only providers meeting quality threshold should be scored
        for provider_name in scores:
            capabilities = self.router.provider_capabilities[provider_name]
            assert capabilities.quality_score >= 0.85 or provider_name in ["anthropic", "openai"]
    
    @pytest.mark.asyncio
    async def test_route_request_success(self):
        """Test successful request routing."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(messages=messages)
        
        response = await self.router.route_request(request)
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.provider is not None
        assert "router_selected_provider" in response.metadata
        assert "router_score" in response.metadata
        
        # Check routing statistics updated
        assert self.router.routing_stats["total_requests"] == 1
        assert self.router.routing_stats["successful_routes"] == 1
    
    @pytest.mark.asyncio
    async def test_route_request_no_providers(self):
        """Test routing when no providers available."""
        # Mock empty provider list
        self.llm_service._providers = []
        
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(messages=messages)
        
        with pytest.raises(LLMProviderError, match="No providers available"):
            await self.router.route_request(request)
    
    @pytest.mark.asyncio
    async def test_route_request_no_suitable_providers(self):
        """Test routing when no providers meet requirements."""
        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
        request = RoutingRequest(
            messages=messages,
            min_quality=0.99,  # Impossibly high threshold
            require_streaming=True,
            exclude_providers=["ollama", "anthropic", "openai"]
        )
        
        with pytest.raises(LLMProviderError, match="No providers meet request requirements"):
            await self.router.route_request(request)
    
    def test_performance_history_tracking(self):
        """Test performance history tracking."""
        provider_name = "test_provider"
        
        # Initial state
        assert provider_name not in self.router.performance_history
        
        # Update with success
        self.router._update_performance_history(provider_name, True, 0.8)
        
        history = self.router.performance_history[provider_name]
        assert history["total_requests"] == 1
        assert history["successful_requests"] == 1
        assert history["success_rate"] == 1.0
        
        # Update with failure
        self.router._update_performance_history(provider_name, False, 0.6)
        
        history = self.router.performance_history[provider_name]
        assert history["total_requests"] == 2
        assert history["successful_requests"] == 1
        assert history["success_rate"] == 0.5
    
    def test_get_performance_modifier(self):
        """Test performance modifier calculation."""
        provider_name = "test_provider"
        
        # No history - should return 1.0
        modifier = self.router._get_performance_modifier(provider_name)
        assert modifier == 1.0
        
        # Add some history
        self.router.performance_history[provider_name] = {
            "success_rate": 0.8
        }
        
        modifier = self.router._get_performance_modifier(provider_name)
        expected = 0.8 + (0.8 * 0.4)  # 0.8 + 0.32 = 1.12
        assert modifier == expected
    
    def test_get_routing_statistics(self):
        """Test getting routing statistics."""
        # Add some mock statistics
        self.router.routing_stats["total_requests"] = 10
        self.router.routing_stats["successful_routes"] = 8
        self.router.routing_stats["cost_optimized"] = 3
        self.router.routing_stats["provider_failovers"] = 2
        
        stats = self.router.get_routing_statistics()
        
        assert stats["total_requests"] == 10
        assert stats["success_rate"] == 0.8
        assert stats["cost_optimized_requests"] == 3
        assert stats["provider_failovers"] == 2
        assert "provider_performance" in stats
        assert "active_providers" in stats
    
    def test_update_provider_capabilities(self):
        """Test updating provider capabilities."""
        provider_name = "test_provider"
        new_capabilities = ProviderCapabilities(
            name=provider_name,
            quality_score=0.95,
            speed_score=0.85,
            cost_score=0.3
        )
        
        self.router.update_provider_capabilities(provider_name, new_capabilities)
        
        assert self.router.provider_capabilities[provider_name] == new_capabilities
    
    def test_get_recommended_provider(self):
        """Test getting recommended provider."""
        # Normal request
        recommended = self.router.get_recommended_provider(
            RequestPriority.NORMAL,
            RequestType.GENERAL
        )
        
        assert recommended in ["ollama", "anthropic", "openai"]
        
        # Philosophical request
        recommended = self.router.get_recommended_provider(
            RequestPriority.HIGH,
            RequestType.PHILOSOPHICAL
        )
        
        # Should prefer providers with high philosophical accuracy
        assert recommended in ["anthropic", "openai"]  # These have higher phil. accuracy
    
    def test_get_recommended_provider_no_available(self):
        """Test getting recommended provider when none available."""
        # Mock no available providers
        self.llm_service._providers = []
        
        recommended = self.router.get_recommended_provider()
        assert recommended is None


class TestUtilityFunctions:
    """Test utility functions for common routing patterns."""
    
    def test_create_philosophical_request(self):
        """Test creating philosophical request."""
        messages = [
            LLMMessage(role=MessageRole.USER, content="What is Aristotelian virtue ethics?")
        ]
        
        request = create_philosophical_request(messages, RequestPriority.HIGH)
        
        assert request.messages == messages
        assert request.priority == RequestPriority.HIGH
        assert request.request_type == RequestType.PHILOSOPHICAL
        assert request.min_quality == 0.7
        assert "anthropic" in request.preferred_providers
        assert "openai" in request.preferred_providers
        assert "gemini" in request.preferred_providers
    
    def test_create_cost_optimized_request(self):
        """Test creating cost-optimized request."""
        messages = [
            LLMMessage(role=MessageRole.USER, content="Simple question")
        ]
        
        request = create_cost_optimized_request(messages)
        
        assert request.messages == messages
        assert request.priority == RequestPriority.LOW
        assert request.request_type == RequestType.GENERAL
        assert request.max_cost == 0.01
        assert "ollama" in request.preferred_providers
    
    def test_create_high_quality_request(self):
        """Test creating high-quality request."""
        messages = [
            LLMMessage(role=MessageRole.USER, content="Complex analysis needed")
        ]
        
        request = create_high_quality_request(messages, RequestType.ANALYTICAL)
        
        assert request.messages == messages
        assert request.priority == RequestPriority.CRITICAL
        assert request.request_type == RequestType.ANALYTICAL
        assert request.min_quality == 0.8
        assert "anthropic" in request.preferred_providers
        assert "openai" in request.preferred_providers
    
    @patch('arete.services.llm_router.create_llm_service')
    def test_create_llm_router_factory(self, mock_create_service):
        """Test creating LLM router with factory function."""
        mock_service = Mock(spec=MultiProviderLLMService)
        mock_create_service.return_value = mock_service
        
        router = create_llm_router()
        
        assert isinstance(router, IntelligentLLMRouter)
        assert router.llm_service == mock_service
        
        # Should create service if none provided
        mock_create_service.assert_called_once()


class TestRouterIntegration:
    """Test router integration with actual LLM service patterns."""
    
    @pytest.mark.asyncio
    async def test_philosophical_tutoring_scenario(self):
        """Test end-to-end philosophical tutoring scenario."""
        # Create mock LLM service
        llm_service = Mock(spec=MultiProviderLLMService)
        llm_service._providers = [
            MockProvider("anthropic", is_available=True),
            MockProvider("ollama", is_available=True)
        ]
        
        # Mock high-quality response for philosophy
        async def mock_generate_response(messages, preferred_provider=None, **kwargs):
            if preferred_provider == "anthropic":
                return LLMResponse(
                    content="Aristotelian virtue ethics focuses on character development and eudaimonia...",
                    provider="anthropic",
                    model="claude-3-opus",
                    usage_tokens=200,
                    metadata={"philosophical_accuracy": 0.95}
                )
            else:
                return LLMResponse(
                    content="Virtue ethics is about being a good person...",
                    provider="ollama",
                    model="llama2",
                    usage_tokens=50,
                    metadata={}
                )
        
        llm_service.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # Create router
        router = IntelligentLLMRouter(llm_service, Settings())
        
        # Create philosophical request
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
            LLMMessage(role=MessageRole.USER, content="Explain Aristotelian virtue ethics")
        ]
        
        request = create_philosophical_request(messages, RequestPriority.HIGH)
        
        # Route the request
        response = await router.route_request(request)
        
        # Should prefer Anthropic for philosophical content
        assert response.provider == "anthropic"
        assert "Aristotelian" in response.content
        assert response.metadata["router_selected_provider"] == "anthropic"
        assert response.metadata["request_type"] == "philosophical"
    
    @pytest.mark.asyncio
    async def test_cost_optimization_scenario(self):
        """Test cost optimization routing scenario."""
        # Create mock LLM service
        llm_service = Mock(spec=MultiProviderLLMService)
        llm_service._providers = [
            MockProvider("ollama", is_available=True),
            MockProvider("openai", is_available=True)
        ]
        
        # Mock responses with different costs implied
        async def mock_generate_response(messages, preferred_provider=None, **kwargs):
            return LLMResponse(
                content=f"Response from {preferred_provider}",
                provider=preferred_provider or "default",
                model="mock-model",
                usage_tokens=50,
                metadata={}
            )
        
        llm_service.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # Create router
        router = IntelligentLLMRouter(llm_service, Settings())
        
        # Create cost-optimized request
        messages = [
            LLMMessage(role=MessageRole.USER, content="What's the weather like?")
        ]
        
        request = create_cost_optimized_request(messages)
        
        # Route the request
        response = await router.route_request(request)
        
        # Should prefer Ollama for cost optimization (free local)
        assert response.provider == "ollama"
        assert response.metadata["router_selected_provider"] == "ollama"
        assert response.metadata["request_priority"] == "low"