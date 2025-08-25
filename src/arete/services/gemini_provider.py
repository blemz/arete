"""
Google Gemini LLM provider implementation for Arete Graph-RAG system.

This module provides integration with Google's Gemini API for accessing
Gemini Pro and other models with safety filtering, system instructions,
and advanced generation features.
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


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider for advanced AI capabilities.
    
    Provides integration with Google's Gemini API including Gemini Pro,
    Gemini 1.5 Pro, and Gemini 1.5 Flash models with advanced safety
    filtering and system instruction support.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Gemini provider.
        
        Args:
            settings: Application configuration settings
            
        Raises:
            AuthenticationError: If API key is not provided
        """
        super().__init__("gemini")
        self.settings = settings
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = settings.llm_timeout
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        
        # Validate API key
        if not settings.gemini_api_key or settings.gemini_api_key.strip() == "":
            raise AuthenticationError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable.",
                provider=self.name
            )
        
        self.api_key = settings.gemini_api_key
        
        # Model management
        self._available_models: List[str] = []
        self._model_info: Dict[str, Dict[str, Any]] = {}
        self._default_model = "gemini-1.5-pro"

    @property
    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        return self._initialized

    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        if not self._initialized:
            return []
        return self._available_models.copy()

    def initialize(self) -> None:
        """Initialize the Gemini provider."""
        logger.info("Initializing Gemini provider")
        
        try:
            # Run async initialization
            import asyncio
            
            async def init_check():
                models = await self._get_available_models()
                if not models:
                    raise ProviderUnavailableError(
                        "Gemini API returned no available models",
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
            logger.error(f"Failed to initialize Gemini provider: {e}")
            if isinstance(e, (ProviderUnavailableError, AuthenticationError)):
                raise
            raise LLMProviderError(f"Gemini initialization failed: {e}")
        
        logger.info("Gemini provider initialized successfully")

    async def _init_async(self) -> None:
        """Async initialization helper."""
        try:
            models = await self._get_available_models()
            if models:
                self._available_models = models
                logger.info(f"Loaded {len(models)} available models from Gemini")
        except Exception as e:
            logger.warning(f"Async initialization warning: {e}")

    async def _get_available_models(self) -> List[str]:
        """Get list of available models from Gemini API."""
        try:
            url = self._get_models_url()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 403:
                    raise AuthenticationError(
                        "Gemini API authentication failed. Check your API key.",
                        provider=self.name
                    )
                elif response.status_code == 429:
                    raise RateLimitError("Gemini API rate limit exceeded")
                elif response.status_code != 200:
                    raise ProviderUnavailableError(
                        f"Gemini API error: HTTP {response.status_code}",
                        provider=self.name
                    )
                
                data = response.json()
                models = []
                
                for model in data.get("models", []):
                    model_name = model.get("name", "")
                    if model_name and "generateContent" in model.get("supportedGenerationMethods", []):
                        # Extract model ID from full name (e.g., "models/gemini-pro" -> "gemini-pro")
                        model_id = self._normalize_model_name(model_name)
                        models.append(model_id)
                        
                        # Store model info
                        self._model_info[model_id] = {
                            "display_name": model.get("displayName", model_id),
                            "description": model.get("description", ""),
                            "input_token_limit": model.get("inputTokenLimit", 32768),
                            "output_token_limit": model.get("outputTokenLimit", 8192),
                            "supported_methods": model.get("supportedGenerationMethods", [])
                        }
                
                return models
                
        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"Gemini API unavailable: {e}",
                provider=self.name
            )
        except Exception as e:
            if isinstance(e, (AuthenticationError, ProviderUnavailableError, RateLimitError)):
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
        Generate response from Gemini API.
        
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
                f"Gemini API unavailable: {e}",
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
        
        url = self._get_generation_url(model)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=request_data)
            
            await self._handle_api_errors(response)
            
            response_data = response.json()
            content, tokens, finish_reason = self._extract_content_from_response(response_data)
            
            # Check for safety blocking
            if finish_reason == "safety":
                raise LLMProviderError("Content blocked by safety filters")
            
            return LLMResponse(
                content=content,
                usage_tokens=tokens,
                provider=self.name,
                model=model,
                finish_reason=finish_reason,
                metadata={
                    "safety_ratings": self._extract_safety_ratings(response_data),
                    "usage": response_data.get("usageMetadata", {}),
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
        
        url = self._get_generation_url(model, stream=True)
        content_parts = []
        final_usage = None
        final_finish_reason = None
        safety_ratings = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=request_data) as response:
                
                await self._handle_api_errors(response)
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk_data = json.loads(line)
                            
                            if "candidates" in chunk_data and chunk_data["candidates"]:
                                candidate = chunk_data["candidates"][0]
                                
                                # Extract content
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            content_parts.append(part["text"])
                                
                                # Check finish reason
                                if "finishReason" in candidate:
                                    final_finish_reason = candidate["finishReason"].lower()
                                
                                # Extract safety ratings
                                if "safetyRatings" in candidate:
                                    safety_ratings = candidate["safetyRatings"]
                            
                            # Extract usage info if available
                            if "usageMetadata" in chunk_data:
                                final_usage = chunk_data["usageMetadata"]
                                
                        except json.JSONDecodeError:
                            continue
        
        full_content = "".join(content_parts)
        total_tokens = None
        
        if final_usage:
            total_tokens = final_usage.get("totalTokenCount")
        
        # Check for safety blocking
        if final_finish_reason == "safety":
            raise LLMProviderError("Content blocked by safety filters")
        
        return LLMResponse(
            content=full_content,
            usage_tokens=total_tokens,
            provider=self.name,
            model=model,
            finish_reason=final_finish_reason or "stop",
            metadata={
                "streaming": True,
                "safety_ratings": safety_ratings,
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
            error = error_data.get("error", {})
            error_message = error.get("message", "Unknown error")
        except:
            error_message = response.text or f"HTTP {response.status_code}"
        
        if response.status_code == 403:
            raise AuthenticationError(
                f"Gemini API authentication failed: {error_message}",
                provider=self.name
            )
        elif response.status_code == 429:
            raise RateLimitError(f"Gemini API rate limit exceeded: {error_message}")
        elif response.status_code in (502, 503, 504):
            raise ProviderUnavailableError(
                f"Gemini API temporarily unavailable: {error_message}",
                provider=self.name
            )
        else:
            raise LLMProviderError(
                f"Gemini API error: HTTP {response.status_code} - {error_message}"
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
        """Build request parameters for Gemini API."""
        formatted_messages = self._format_messages(messages)
        
        params = {
            "contents": formatted_messages["contents"],
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "topP": kwargs.get("top_p", 0.95),
                "topK": kwargs.get("top_k", 40)
            },
            "safetySettings": self._get_safety_settings()
        }
        
        # Add system instruction if present
        if formatted_messages["system_instruction"]:
            params["systemInstruction"] = formatted_messages["system_instruction"]
        
        return params

    def _format_messages(self, messages: List[LLMMessage]) -> Dict[str, Any]:
        """Format messages for Gemini API."""
        contents = []
        system_instruction = None
        
        # Extract system message first
        system_messages = [msg for msg in messages if msg.role == MessageRole.SYSTEM]
        if system_messages:
            system_instruction = {
                "parts": [{"text": system_messages[0].content}]
            }
        
        # Process conversation messages
        conversation_messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]
        
        for message in conversation_messages:
            role = "user" if message.role == MessageRole.USER else "model"
            contents.append({
                "role": role,
                "parts": [{"text": message.content}]
            })
        
        return {
            "contents": contents,
            "system_instruction": system_instruction
        }

    def _extract_content_from_response(self, response_data: Dict[str, Any]) -> tuple[str, Optional[int], Optional[str]]:
        """Extract content, tokens, and finish reason from Gemini response."""
        content = ""
        tokens = None
        finish_reason = None
        
        candidates = response_data.get("candidates", [])
        if candidates:
            candidate = candidates[0]
            
            # Extract content
            if "content" in candidate and "parts" in candidate["content"]:
                text_parts = []
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_parts.append(part["text"])
                content = "".join(text_parts)
            
            # Extract finish reason
            if "finishReason" in candidate:
                finish_reason = candidate["finishReason"].lower()
        
        # Extract usage info
        usage = response_data.get("usageMetadata", {})
        if usage:
            tokens = usage.get("totalTokenCount")
        
        if not candidates:
            finish_reason = "error"
        
        return content, tokens, finish_reason

    def _extract_safety_ratings(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract safety ratings from response."""
        candidates = response_data.get("candidates", [])
        if candidates and "safetyRatings" in candidates[0]:
            return candidates[0]["safetyRatings"]
        return []

    def _get_default_model(self, available_models: List[str]) -> str:
        """Get default model to use."""
        if not available_models:
            return self._default_model
        
        # Prefer certain models if available
        preferred_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ]
        
        for preferred in preferred_models:
            if preferred in available_models:
                return preferred
        
        # Return first available model
        return available_models[0]

    def _get_safety_settings(self) -> List[Dict[str, Any]]:
        """Get safety settings for content filtering."""
        # Set to BLOCK_ONLY_HIGH for educational content
        return [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]

    def _normalize_model_name(self, model_name: str) -> str:
        """Normalize model name by removing 'models/' prefix."""
        if model_name.startswith("models/"):
            return model_name[7:]  # Remove "models/" prefix
        return model_name

    def _get_models_url(self) -> str:
        """Get URL for listing models."""
        return f"{self.base_url}/models?key={self.api_key}"

    def _get_generation_url(self, model: str, stream: bool = False) -> str:
        """Get URL for content generation."""
        method = "streamGenerateContent" if stream else "generateContent"
        return f"{self.base_url}/models/{model}:{method}?key={self.api_key}"

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        return self._model_info.get(model_id)

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
        logger.info("Cleaning up Gemini provider")
        self._initialized = False
        self._available_models.clear()
        self._model_info.clear()
        logger.info("Gemini provider cleanup complete")


# Factory function for easy Gemini provider creation
def create_gemini_provider(settings: Optional[Settings] = None) -> GeminiProvider:
    """
    Create and initialize a Gemini provider.
    
    Args:
        settings: Application settings (uses default if None)
        
    Returns:
        Configured Gemini provider instance
    """
    if settings is None:
        from arete.config import get_settings
        settings = get_settings()
    
    provider = GeminiProvider(settings)
    
    try:
        provider.initialize()
        logger.info("Gemini provider created and initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini provider: {e}")
        # Don't raise - allow provider to be created but mark as unavailable
    
    return provider