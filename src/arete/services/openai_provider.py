"""
OpenAI API provider for Arete Graph-RAG system.

This module provides integration with OpenAI's GPT models including GPT-4, GPT-3.5-turbo,
and other models through their REST API. Supports both streaming and standard responses
with comprehensive error handling.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
import json
import time

from arete.services.llm_provider import (
    LLMProvider, LLMMessage, LLMResponse, MessageRole,
    LLMProviderError, ProviderUnavailableError, RateLimitError, AuthenticationError
)
from arete.config import Settings

# Setup logger
logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider for GPT models.
    
    Provides access to OpenAI's GPT-4, GPT-3.5-turbo, and other models
    through their REST API with streaming support.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize OpenAI provider.
        
        Args:
            settings: Application configuration containing API key
        """
        super().__init__("openai")
        self.settings = settings
        self.api_key = settings.openai_api_key
        
        # Validate API key on initialization
        if not self.api_key or not self.api_key.strip():
            raise AuthenticationError("OpenAI API key not provided", "openai")
            
        self.base_url = "https://api.openai.com/v1"
        self.client: Optional[httpx.AsyncClient] = None
        self._models_cache: Optional[List[str]] = None
        self._models_cache_time: float = 0
        self._cache_ttl = 300  # 5 minutes
        
        # Default models supported by OpenAI
        self._default_models = [
            "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "gpt-4o", "gpt-4o-mini"
        ]
    
    @property
    def timeout(self) -> int:
        """Get timeout setting."""
        return self.settings.llm_timeout
    
    @property
    def max_tokens(self) -> int:
        """Get max tokens setting."""
        return self.settings.llm_max_tokens
    
    @property 
    def temperature(self) -> float:
        """Get temperature setting."""
        return self.settings.llm_temperature
        
    @property
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return bool(self.api_key and self.api_key.strip())
    
    @property
    def supported_models(self) -> List[str]:
        """Get list of supported OpenAI models."""
        if self._models_cache and (time.time() - self._models_cache_time) < self._cache_ttl:
            return self._models_cache
        return self._default_models
    
    def initialize(self) -> None:
        """Initialize the OpenAI provider."""
        if not self.api_key:
            raise AuthenticationError("OpenAI API key not provided", "openai")
        
        # Create HTTP client
        headers = self.get_headers()
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout
        )
        
        self._initialized = True
        logger.info("OpenAI provider initialized successfully")
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for OpenAI API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        return "gpt-3.5-turbo"
    
    def _get_default_model(self, available_models: List[str]) -> str:
        """Get the best default model from available models."""
        if not available_models:
            return "gpt-4-turbo"
        
        # Preference order: latest GPT-4 variants first
        preferred_order = [
            "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-4", "gpt-4-turbo-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        
        for preferred in preferred_order:
            if preferred in available_models:
                return preferred
        
        # If none of the preferred models are available, return first available
        return available_models[0] if available_models else "gpt-3.5-turbo"
    
    def build_request_params(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request parameters for OpenAI API."""
        model = model or self.get_default_model()
        formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": kwargs.get("stream", False)
        }
        
        # Add optional parameters
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = max(0, min(2, temperature))
        
        # Add advanced parameters
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            payload["top_p"] = max(0, min(1, kwargs["top_p"]))
        if "frequency_penalty" in kwargs and kwargs["frequency_penalty"] is not None:
            payload["frequency_penalty"] = max(-2, min(2, kwargs["frequency_penalty"]))
        if "presence_penalty" in kwargs and kwargs["presence_penalty"] is not None:
            payload["presence_penalty"] = max(-2, min(2, kwargs["presence_penalty"]))
            
        return payload
    
    def extract_content_from_response(self, response_data: Dict[str, Any]) -> str:
        """Extract content from OpenAI API response."""
        choices = response_data.get("choices", [])
        if not choices:
            return ""
        
        choice = choices[0]
        message = choice.get("message", {})
        return message.get("content", "")
    
    async def _fetch_available_models(self) -> List[str]:
        """Fetch available models from OpenAI API."""
        if not self.client:
            await self._ensure_initialized()
        
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            
            # Filter for GPT models only
            gpt_models = [model for model in models if model.startswith("gpt")]
            
            # Cache the results
            self._models_cache = gpt_models
            self._models_cache_time = time.time()
            
            return gpt_models
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid OpenAI API key", "openai")
            elif e.response.status_code == 429:
                raise RateLimitError("OpenAI API rate limit exceeded")
            else:
                logger.warning(f"Failed to fetch OpenAI models: {e}")
                return self._default_models
        except Exception as e:
            logger.warning(f"Error fetching OpenAI models: {e}")
            return self._default_models
    
    async def _ensure_initialized(self):
        """Ensure provider is initialized."""
        if not self._initialized:
            self.initialize()
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using OpenAI API.
        
        Args:
            messages: Conversation messages
            model: Model to use (defaults to gpt-3.5-turbo)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            stream: Whether to stream response
            top_p: Top-p sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMProviderError: If generation fails
            ProviderUnavailableError: If OpenAI API is unavailable
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
        """
        await self._ensure_initialized()
        
        if not self.is_available:
            raise ProviderUnavailableError("OpenAI provider not available", "openai")
        
        # Use default model if none specified
        model = model or self.get_default_model()
        
        # Prepare request payload using helper method
        payload = self.build_request_params(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            **kwargs
        )
        
        try:
            if stream:
                return await self._generate_streaming_response(payload)
            else:
                return await self._generate_standard_response(payload)
                
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI generation: {e}")
            raise LLMProviderError(f"OpenAI generation failed: {e}")
    
    async def _generate_standard_response(self, payload: Dict[str, Any]) -> LLMResponse:
        """Generate standard (non-streaming) response."""
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract response content using helper method
        content = self.extract_content_from_response(data)
        
        # Extract response metadata
        choice = data["choices"][0] if data.get("choices") else {}
        finish_reason = choice.get("finish_reason")
        
        # Extract usage information
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens")
        
        return LLMResponse(
            content=content,
            provider="openai",
            model=data.get("model"),
            usage_tokens=total_tokens,
            finish_reason=finish_reason,
            metadata={
                "usage": usage,
                "created": data.get("created"),
                "id": data.get("id")
            }
        )
    
    async def _generate_streaming_response(self, payload: Dict[str, Any]) -> LLMResponse:
        """Generate streaming response."""
        content_chunks = []
        finish_reason = None
        model = None
        usage_tokens = None
        metadata = {}
        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        
                        if "choices" in chunk_data and chunk_data["choices"]:
                            choice = chunk_data["choices"][0]
                            
                            # Get model from first chunk
                            if model is None:
                                model = chunk_data.get("model")
                            
                            # Extract content delta
                            delta = choice.get("delta", {})
                            if "content" in delta and delta["content"]:
                                content_chunks.append(delta["content"])
                            
                            # Check for finish reason
                            if choice.get("finish_reason"):
                                finish_reason = choice["finish_reason"]
                        
                        # Extract metadata from first chunk
                        if not metadata and chunk_data.get("id"):
                            metadata.update({
                                "id": chunk_data.get("id"),
                                "created": chunk_data.get("created")
                            })
                            
                    except json.JSONDecodeError:
                        continue
        
        content = "".join(content_chunks)
        
        return LLMResponse(
            content=content,
            provider="openai",
            model=model,
            usage_tokens=usage_tokens,
            finish_reason=finish_reason,
            metadata=metadata
        )
    
    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API."""
        formatted = []
        
        for message in messages:
            formatted.append({
                "role": message.role.value,
                "content": message.content
            })
        
        return formatted
    
    async def _handle_http_error(self, error: httpx.HTTPStatusError):
        """Handle HTTP errors from OpenAI API."""
        status_code = error.response.status_code
        
        try:
            error_data = error.response.json()
            error_message = error_data.get("error", {}).get("message", str(error))
        except:
            error_message = str(error)
        
        if status_code == 401:
            raise AuthenticationError(f"OpenAI authentication failed: {error_message}", "openai")
        elif status_code == 429:
            # Try to get retry-after header
            retry_after = error.response.headers.get("retry-after")
            retry_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(f"OpenAI rate limit exceeded: {error_message}", retry_seconds)
        elif status_code == 503:
            raise ProviderUnavailableError(f"OpenAI API unavailable: {error_message}", "openai")
        else:
            raise LLMProviderError(f"OpenAI API error ({status_code}): {error_message}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get OpenAI provider health status."""
        status = {
            "provider": "openai",
            "status": "healthy" if self.is_available else "unhealthy",
            "initialized": self._initialized,
            "has_api_key": bool(self.api_key),
            "models_cached": len(self._models_cache) if self._models_cache else 0
        }
        
        if not self.is_available:
            status["error"] = "API key not configured"
        
        return status
    
    async def get_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        if not self.is_available:
            return []
        
        try:
            return await self._fetch_available_models()
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI models: {e}")
            return self._default_models
    
    async def estimate_cost(self, messages: List[LLMMessage], model: Optional[str] = None) -> Optional[float]:
        """
        Estimate cost for generating response.
        
        Args:
            messages: Input messages
            model: Model to use for estimation
            
        Returns:
            Estimated cost in USD, or None if unavailable
        """
        model = model or "gpt-3.5-turbo"
        
        # Rough token estimation (4 chars = 1 token)
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // 4
        
        # Pricing per 1K tokens (as of 2024, approximate)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        if model not in pricing:
            return None
        
        model_pricing = pricing[model]
        input_cost = (estimated_tokens / 1000) * model_pricing["input"]
        
        # Estimate output tokens (assume 25% of input)
        output_tokens = estimated_tokens * 0.25
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def cleanup(self):
        """Cleanup OpenAI provider resources."""
        if self.client:
            asyncio.create_task(self.client.aclose())
            self.client = None
        
        self._models_cache = None
        self._initialized = False
        logger.info("OpenAI provider cleanup complete")