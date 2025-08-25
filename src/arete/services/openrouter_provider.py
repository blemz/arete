"""
OpenRouter LLM provider implementation for Arete Graph-RAG system.

This module provides integration with OpenRouter API for accessing multiple
cloud-based LLMs through a unified interface, including cost tracking,
model selection, and rate limit handling.
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


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter LLM provider for cloud-based model access.
    
    Provides integration with OpenRouter API for accessing multiple LLM providers
    including Anthropic Claude, OpenAI GPT, Meta Llama, and others through a
    unified API with cost tracking and intelligent model selection.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize OpenRouter provider.
        
        Args:
            settings: Application configuration settings
            
        Raises:
            AuthenticationError: If API key is not provided
        """
        super().__init__("openrouter")
        self.settings = settings
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = settings.llm_timeout
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        
        # Validate API key
        if not settings.openrouter_api_key or settings.openrouter_api_key.strip() == "":
            raise AuthenticationError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable.",
                provider=self.name
            )
        
        self.api_key = settings.openrouter_api_key
        
        # Model management
        self._available_models: List[str] = []
        self._model_info: Dict[str, Dict[str, Any]] = {}
        self._default_model = "anthropic/claude-3-haiku"

    @property
    def is_available(self) -> bool:
        """Check if OpenRouter API is available."""
        return self._initialized

    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        if not self._initialized:
            return []
        return self._available_models.copy()

    def initialize(self) -> None:
        """Initialize the OpenRouter provider."""
        logger.info("Initializing OpenRouter provider")
        
        try:
            # Run async initialization
            import asyncio
            
            async def init_check():
                models = await self._get_available_models()
                if not models:
                    raise ProviderUnavailableError(
                        "OpenRouter API returned no available models",
                        provider=self.name
                    )
                self._available_models = models
                return True
            
            # Run the async check
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            
            if loop is not None:
                # We're in an async context, create a task
                task = loop.create_task(self._init_async())
                self._initialized = True
            else:
                # We're not in an async context, run synchronously
                asyncio.run(init_check())
                self._initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {e}")
            if isinstance(e, (ProviderUnavailableError, AuthenticationError)):
                raise
            raise LLMProviderError(f"OpenRouter initialization failed: {e}")
        
        logger.info("OpenRouter provider initialized successfully")

    async def _init_async(self) -> None:
        """Async initialization helper."""
        try:
            models = await self._get_available_models()
            if models:
                self._available_models = models
                logger.info(f"Loaded {len(models)} available models from OpenRouter")
        except Exception as e:
            logger.warning(f"Async initialization warning: {e}")

    async def _get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter API."""
        try:
            headers = self._get_headers()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                
                if response.status_code == 401:
                    raise AuthenticationError(
                        "OpenRouter API authentication failed. Check your API key.",
                        provider=self.name
                    )
                elif response.status_code == 403:
                    raise AuthenticationError(
                        "OpenRouter API access forbidden. Check your account status.",
                        provider=self.name
                    )
                elif response.status_code != 200:
                    raise ProviderUnavailableError(
                        f"OpenRouter API error: HTTP {response.status_code}",
                        provider=self.name
                    )
                
                data = response.json()
                models = []
                
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    if model_id:
                        models.append(model_id)
                        # Store model info for later use
                        self._model_info[model_id] = {
                            "name": model.get("name", model_id),
                            "context_length": model.get("context_length", 4000),
                            "pricing": model.get("pricing", {}),
                            "description": model.get("description", "")
                        }
                
                return models
                
        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"OpenRouter API unavailable: {e}",
                provider=self.name
            )
        except Exception as e:
            if isinstance(e, (AuthenticationError, ProviderUnavailableError)):
                raise
            logger.error(f"Error getting available models: {e}")
            return []

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
        Generate response from OpenRouter API.
        
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
                f"OpenRouter API unavailable: {e}",
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
                f"{self.base_url}/chat/completions",
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
                    "response_id": response_data.get("id"),
                    "created": response_data.get("created"),
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
        final_usage = None
        final_finish_reason = None
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers=headers
            ) as response:
                
                await self._handle_api_errors(response)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse server-sent events format
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                
                                if "choices" in chunk_data and chunk_data["choices"]:
                                    choice = chunk_data["choices"][0]
                                    
                                    # Extract content delta
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content_parts.append(choice["delta"]["content"])
                                    
                                    # Check for finish reason
                                    if "finish_reason" in choice and choice["finish_reason"]:
                                        final_finish_reason = choice["finish_reason"]
                                
                                # Extract usage info if available
                                if "usage" in chunk_data:
                                    final_usage = chunk_data["usage"]
                                    
                            except json.JSONDecodeError:
                                continue
        
        full_content = "".join(content_parts)
        total_tokens = None
        
        if final_usage:
            total_tokens = final_usage.get("total_tokens")
        
        return LLMResponse(
            content=full_content,
            usage_tokens=total_tokens,
            provider=self.name,
            model=model,
            finish_reason=final_finish_reason or "stop",
            metadata={
                "streaming": True,
                "usage": final_usage or {},
                "model_info": self._model_info.get(model, {})
            }
        )

    async def _handle_api_errors(self, response: httpx.Response) -> None:
        """Handle API error responses."""
        if response.status_code == 200:
            return
        
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
        except:
            error_message = response.text or f"HTTP {response.status_code}"
        
        if response.status_code == 401:
            raise AuthenticationError(
                f"OpenRouter API authentication failed: {error_message}",
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
                f"OpenRouter API rate limit exceeded: {error_message}",
                retry_after=retry_after
            )
        elif response.status_code in (502, 503, 504):
            raise ProviderUnavailableError(
                f"OpenRouter API temporarily unavailable: {error_message}",
                provider=self.name
            )
        else:
            raise LLMProviderError(
                f"OpenRouter API error: HTTP {response.status_code} - {error_message}"
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
        """Build request parameters for OpenRouter API."""
        params = {
            "model": model,
            "messages": self._format_messages(messages),
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": stream
        }
        
        # Add OpenRouter-specific parameters if provided
        if "provider_preferences" in kwargs:
            params["provider"] = kwargs["provider_preferences"]
        
        return params

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Format messages for OpenRouter API."""
        return [
            {
                "role": message.role.value,
                "content": message.content
            }
            for message in messages
        ]

    def _extract_content_from_response(self, response_data: Dict[str, Any]) -> tuple[str, Optional[int], Optional[str]]:
        """Extract content, tokens, and finish reason from OpenRouter response."""
        content = ""
        tokens = None
        finish_reason = None
        
        choices = response_data.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason")
        
        usage = response_data.get("usage", {})
        if usage:
            tokens = usage.get("total_tokens")
        
        if not choices:
            finish_reason = "error"
        
        return content, tokens, finish_reason

    def _get_default_model(self, available_models: List[str]) -> str:
        """Get default model to use."""
        if not available_models:
            return self._default_model
        
        # Prefer certain models if available
        preferred_models = [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet", 
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-3-8b-instruct"
        ]
        
        for preferred in preferred_models:
            if preferred in available_models:
                return preferred
        
        # Return first available model
        return available_models[0]

    def _get_headers(
        self,
        app_name: Optional[str] = None,
        site_url: Optional[str] = None
    ) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"Arete-Graph-RAG/1.0 (https://github.com/your-org/arete)"
        }
        
        # Add optional headers for cost tracking
        if site_url:
            headers["HTTP-Referer"] = site_url
        
        if app_name:
            headers["X-Title"] = app_name
        
        return headers

    def _extract_pricing_info(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pricing information from model data."""
        pricing = model_data.get("pricing", {})
        
        return {
            "prompt_cost": float(pricing.get("prompt", "0")),
            "completion_cost": float(pricing.get("completion", "0")),
            "currency": "USD"
        }

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        return self._model_info.get(model_id)

    def estimate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict[str, float]:
        """Estimate cost for a request."""
        model_info = self._model_info.get(model_id, {})
        pricing = model_info.get("pricing", {})
        
        prompt_cost_per_token = float(pricing.get("prompt", "0")) / 1000000  # Per million tokens
        completion_cost_per_token = float(pricing.get("completion", "0")) / 1000000
        
        prompt_cost = prompt_tokens * prompt_cost_per_token
        completion_cost = completion_tokens * completion_cost_per_token
        total_cost = prompt_cost + completion_cost
        
        return {
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
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
        logger.info("Cleaning up OpenRouter provider")
        self._initialized = False
        self._available_models.clear()
        self._model_info.clear()
        logger.info("OpenRouter provider cleanup complete")


# Factory function for easy OpenRouter provider creation
def create_openrouter_provider(settings: Optional[Settings] = None) -> OpenRouterProvider:
    """
    Create and initialize an OpenRouter provider.
    
    Args:
        settings: Application settings (uses default if None)
        
    Returns:
        Configured OpenRouter provider instance
    """
    if settings is None:
        from arete.config import get_settings
        settings = get_settings()
    
    provider = OpenRouterProvider(settings)
    
    try:
        provider.initialize()
        logger.info("OpenRouter provider created and initialized")
    except Exception as e:
        logger.error(f"Failed to initialize OpenRouter provider: {e}")
        # Don't raise - allow provider to be created but mark as unavailable
    
    return provider