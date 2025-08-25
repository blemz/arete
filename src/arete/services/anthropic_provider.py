"""
Anthropic Claude LLM provider implementation for Arete Graph-RAG system.

This module provides integration with Anthropic's Claude API for accessing
Claude 3 Haiku, Sonnet, and Opus models with advanced reasoning capabilities
and educational content generation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import json

import httpx

from arete.services.llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    LLMProviderError,
    ProviderUnavailableError,
    RateLimitError,
    AuthenticationError
)
from arete.config import Settings

# Setup logger
logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude LLM provider for advanced AI reasoning.
    
    Provides integration with Anthropic's Claude API including Claude 3 Haiku
    (fast), Claude 3 Sonnet (balanced), and Claude 3 Opus (most capable) with
    advanced reasoning, analysis, and educational content generation.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Anthropic provider.
        
        Args:
            settings: Application configuration settings
            
        Raises:
            AuthenticationError: If API key is not provided
        """
        super().__init__("anthropic")
        self.settings = settings
        self.base_url = "https://api.anthropic.com/v1"
        self.timeout = settings.llm_timeout
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        
        # Validate API key
        if not settings.anthropic_api_key or settings.anthropic_api_key.strip() == "":
            raise AuthenticationError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.",
                provider=self.name
            )
        
        self.api_key = settings.anthropic_api_key
        
        # Claude model information - static list as Anthropic doesn't provide a models endpoint
        self._available_models = [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022"  # Latest version
        ]
        
        self._model_info = {
            "claude-3-haiku-20240307": {
                "display_name": "Claude 3 Haiku",
                "description": "Fast and cost-effective model for simple tasks",
                "context_length": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.00025,
                "cost_per_1k_output": 0.00125
            },
            "claude-3-sonnet-20240229": {
                "display_name": "Claude 3 Sonnet", 
                "description": "Balanced model for complex tasks",
                "context_length": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015
            },
            "claude-3-opus-20240229": {
                "display_name": "Claude 3 Opus",
                "description": "Most capable model for highly complex tasks",
                "context_length": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075
            },
            "claude-3-5-sonnet-20241022": {
                "display_name": "Claude 3.5 Sonnet",
                "description": "Latest and most capable Sonnet model",
                "context_length": 200000,
                "max_output": 8192,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015
            }
        }
        
        self._default_model = "claude-3-sonnet-20240229"

    @property
    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        return self._initialized

    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        return self._available_models.copy()

    def initialize(self) -> None:
        """Initialize the Anthropic provider."""
        logger.info("Initializing Anthropic provider")
        
        try:
            # Anthropic doesn't require async initialization for model listing
            # The API key will be validated on first request
            self._initialized = True
            logger.info("Anthropic provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise LLMProviderError(f"Anthropic initialization failed: {e}")

    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from Anthropic API.
        
        Args:
            messages: Conversation messages
            model: Model to use (defaults to available model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to use streaming mode
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object with generated content
            
        Raises:
            LLMProviderError: If generation fails
            ProviderUnavailableError: If API is unavailable
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
        """
        if not self._initialized:
            raise LLMProviderError("Provider not initialized. Call initialize() first.")
        
        # Use defaults if not provided
        model = model or self._get_default_model(self._available_models)
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        try:
            if stream:
                return await self._generate_streaming(
                    messages, model, max_tokens, temperature, **kwargs
                )
            else:
                return await self._generate_standard(
                    messages, model, max_tokens, temperature, **kwargs
                )
                
        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"Anthropic API unavailable: {e}",
                provider=self.name
            )
        except httpx.TimeoutException as e:
            raise LLMProviderError(f"Request timeout: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            raise LLMProviderError(f"Generation failed: {e}")

    async def _generate_standard(
        self,
        messages: List[LLMMessage],
        model: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """Generate response using standard (non-streaming) mode."""
        request_data = self._build_request_params(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        headers = self._get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json=request_data,
                headers=headers
            )
            
            await self._handle_api_errors(response)
            
            response_data = response.json()
            content, tokens, finish_reason = self._extract_content_from_response(response_data)
            
            return LLMResponse(
                content=content,
                usage_tokens=tokens,
                provider=self.name,
                model=model,
                finish_reason=finish_reason,
                metadata={
                    "message_id": response_data.get("id"),
                    "usage": response_data.get("usage", {}),
                    "model_info": self._model_info.get(model, {})
                }
            )

    async def _generate_streaming(
        self,
        messages: List[LLMMessage],
        model: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """Generate response using streaming mode."""
        request_data = self._build_request_params(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs
        )
        
        headers = self._get_headers()
        content_parts = []
        final_usage = {"input_tokens": 0, "output_tokens": 0}
        final_finish_reason = None
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                json=request_data,
                headers=headers
            ) as response:
                
                await self._handle_api_errors(response)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse server-sent events format
                        if line.startswith("event: "):
                            event_type = line[7:]  # Remove "event: " prefix
                        elif line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            try:
                                chunk_data = json.loads(data_str)
                                
                                # Handle different event types
                                if chunk_data.get("type") == "message_start":
                                    message = chunk_data.get("message", {})
                                    usage = message.get("usage", {})
                                    if usage:
                                        final_usage["input_tokens"] = usage.get("input_tokens", 0)
                                
                                elif chunk_data.get("type") == "content_block_delta":
                                    delta = chunk_data.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        content_parts.append(delta.get("text", ""))
                                
                                elif chunk_data.get("type") == "message_delta":
                                    delta = chunk_data.get("delta", {})
                                    if "stop_reason" in delta:
                                        final_finish_reason = delta["stop_reason"]
                                    
                                    usage = chunk_data.get("usage", {})
                                    if usage:
                                        final_usage["output_tokens"] = usage.get("output_tokens", 0)
                                
                                elif chunk_data.get("type") == "message_stop":
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
        
        full_content = "".join(content_parts)
        total_tokens = final_usage["input_tokens"] + final_usage["output_tokens"]
        
        return LLMResponse(
            content=full_content,
            usage_tokens=total_tokens,
            provider=self.name,
            model=model,
            finish_reason=self._map_stop_reason(final_finish_reason),
            metadata={
                "streaming": True,
                "usage": final_usage,
                "model_info": self._model_info.get(model, {})
            }
        )

    async def _handle_api_errors(self, response: httpx.Response) -> None:
        """Handle API error responses."""
        if response.status_code == 200:
            return
        
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            error_message = error.get("message", "Unknown error")
            error_type = error.get("type", "unknown_error")
        except:
            error_message = response.text or f"HTTP {response.status_code}"
            error_type = "unknown_error"
        
        if response.status_code == 401:
            raise AuthenticationError(
                f"Anthropic API authentication failed: {error_message}",
                provider=self.name
            )
        elif response.status_code == 429:
            retry_after = None
            if "retry-after" in response.headers:
                try:
                    retry_after = int(response.headers["retry-after"])
                except ValueError:
                    pass
            
            raise RateLimitError(
                f"Anthropic API rate limit exceeded: {error_message}",
                retry_after=retry_after
            )
        elif response.status_code in (502, 503, 504):
            raise ProviderUnavailableError(
                f"Anthropic API temporarily unavailable: {error_message}",
                provider=self.name
            )
        else:
            raise LLMProviderError(
                f"Anthropic API error: HTTP {response.status_code} - {error_message}"
            )

    def _build_request_params(
        self,
        messages: List[LLMMessage],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request parameters for Anthropic API."""
        formatted = self._format_messages(messages)
        
        params = {
            "model": model,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": formatted["messages"]
        }
        
        # Add system message if present
        if formatted["system"]:
            params["system"] = formatted["system"]
        
        # Add streaming parameter
        if stream:
            params["stream"] = True
        
        # Add additional parameters
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            params["top_k"] = kwargs["top_k"]
        
        return params

    def _format_messages(self, messages: List[LLMMessage]) -> Dict[str, Any]:
        """Format messages for Anthropic API."""
        system_message = None
        conversation_messages = []
        
        # Extract system message
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                system_message = message.content
                break
        
        # Process conversation messages (user/assistant only)
        for message in messages:
            if message.role in (MessageRole.USER, MessageRole.ASSISTANT):
                conversation_messages.append({
                    "role": message.role.value,
                    "content": message.content
                })
        
        return {
            "system": system_message,
            "messages": conversation_messages
        }

    def _extract_content_from_response(self, response_data: Dict[str, Any]) -> tuple[str, Optional[int], Optional[str]]:
        """Extract content, tokens, and finish reason from Anthropic response."""
        content = ""
        tokens = None
        finish_reason = None
        
        # Extract content from text blocks
        content_blocks = response_data.get("content", [])
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        content = "".join(text_parts)
        
        # Extract usage information
        usage = response_data.get("usage", {})
        if usage:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            tokens = input_tokens + output_tokens
        
        # Extract stop reason
        stop_reason = response_data.get("stop_reason")
        if stop_reason:
            finish_reason = self._map_stop_reason(stop_reason)
        
        return content, tokens, finish_reason

    def _map_stop_reason(self, stop_reason: Optional[str]) -> str:
        """Map Anthropic stop reasons to standard format."""
        if not stop_reason:
            return "stop"
        
        mapping = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop"
        }
        
        return mapping.get(stop_reason, stop_reason)

    def _get_default_model(self, available_models: List[str]) -> str:
        """Get default model to use."""
        if not available_models:
            return self._default_model
        
        # Prefer models in order of capability/cost balance
        preferred_models = [
            "claude-3-5-sonnet-20241022",  # Latest Sonnet
            "claude-3-sonnet-20240229",   # Balanced choice
            "claude-3-haiku-20240307",    # Fast and cheap
            "claude-3-opus-20240229"      # Most capable but expensive
        ]
        
        for preferred in preferred_models:
            if preferred in available_models:
                return preferred
        
        # Return first available model
        return available_models[0]

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        return self._model_info.get(model_id)

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """Estimate cost for a request."""
        model_info = self._model_info.get(model_id, {})
        
        input_cost_per_1k = model_info.get("cost_per_1k_input", 0)
        output_cost_per_1k = model_info.get("cost_per_1k_output", 0)
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "currency": "USD"
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status and diagnostics."""
        if not self._initialized:
            return {
                "provider": self.name,
                "status": "not_initialized",
                "initialized": False,
                "api_url": self.base_url
            }
        
        return {
            "provider": self.name,
            "status": "healthy" if self.is_available else "unhealthy",
            "initialized": self._initialized,
            "api_url": self.base_url,
            "available_models": self._available_models.copy(),
            "default_model": self._get_default_model(self._available_models),
            "settings": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout
            },
            "model_count": len(self._available_models)
        }

    def cleanup(self) -> None:
        """Cleanup provider resources."""
        logger.info("Cleaning up Anthropic provider")
        self._initialized = False
        logger.info("Anthropic provider cleanup complete")


# Factory function for easy Anthropic provider creation
def create_anthropic_provider(settings: Optional[Settings] = None) -> AnthropicProvider:
    """
    Create and initialize an Anthropic provider.
    
    Args:
        settings: Application settings (uses default if None)
        
    Returns:
        Configured Anthropic provider instance
    """
    if settings is None:
        from arete.config import get_settings
        settings = get_settings()
    
    provider = AnthropicProvider(settings)
    
    try:
        provider.initialize()
        logger.info("Anthropic provider created and initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic provider: {e}")
        # Don't raise - allow provider to be created but mark as unavailable
    
    return provider