"""
Provider Configuration Management Service.

Advanced configuration management system for LLM providers with validation,
health monitoring, persistence, and backup capabilities.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_serializer
from arete.config import Settings, get_settings
from arete.services.llm_provider import LLMProviderFactory, LLMProviderError

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    """Provider status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNCONFIGURED = "unconfigured"
    AUTHENTICATON_FAILED = "authentication_failed"
    UNKNOWN = "unknown"


class ConfigurationSource(str, Enum):
    """Configuration source types."""
    ENVIRONMENT = "environment"
    SETTINGS_FILE = "settings_file"
    USER_OVERRIDE = "user_override"
    BACKUP = "backup"
    DEFAULT = "default"


@dataclass
class ProviderHealth:
    """Provider health information."""
    provider: str
    status: ProviderStatus
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "response_time": self.response_time,
            "error_message": self.error_message,
            "consecutive_failures": self.consecutive_failures,
            "last_success": self.last_success.isoformat() if self.last_success else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderHealth':
        """Create from dictionary."""
        return cls(
            provider=data["provider"],
            status=ProviderStatus(data["status"]),
            last_check=datetime.fromisoformat(data["last_check"]),
            response_time=data.get("response_time"),
            error_message=data.get("error_message"),
            consecutive_failures=data.get("consecutive_failures", 0),
            last_success=datetime.fromisoformat(data["last_success"]) if data.get("last_success") else None
        )


class ProviderConfiguration(BaseModel):
    """Provider configuration model."""
    
    provider: str = Field(..., description="Provider name")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    api_key: Optional[str] = Field(default=None, description="API key", repr=False)
    base_url: Optional[str] = Field(default=None, description="Base URL")
    default_model: Optional[str] = Field(default=None, description="Default model")
    models: List[str] = Field(default_factory=list, description="Available models")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retries")
    rate_limit: Optional[int] = Field(default=None, ge=1, description="Rate limit per minute")
    priority: int = Field(default=1, ge=1, le=10, description="Provider priority")
    tags: List[str] = Field(default_factory=list, description="Provider tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('provider')
    @classmethod
    def validate_provider_name(cls, v):
        """Validate provider name."""
        valid_providers = {"ollama", "openrouter", "gemini", "anthropic", "openai"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid provider: {v}. Must be one of {valid_providers}")
        return v.lower()
    
    model_config = ConfigDict(
        use_enum_values=True
    )
    
    @model_serializer
    def serialize_model(self):
        """Custom serializer for datetime fields."""
        data = self.__dict__.copy()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


class ProviderConfigurationService:
    """
    Advanced provider configuration management service.
    
    Features:
    - Configuration validation and persistence
    - Health monitoring and status tracking
    - Backup and restore capabilities
    - Environment variable integration
    - Configuration switching and rollback
    """
    
    def __init__(self, settings: Optional[Settings] = None, config_dir: Optional[Path] = None):
        """
        Initialize configuration service.
        
        Args:
            settings: Application settings
            config_dir: Configuration directory path
        """
        self.settings = settings or get_settings()
        self.config_dir = config_dir or Path.home() / ".arete" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.config_file = self.config_dir / "providers.json"
        self.health_file = self.config_dir / "health.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # In-memory state
        self._configurations: Dict[str, ProviderConfiguration] = {}
        self._health_status: Dict[str, ProviderHealth] = {}
        self._factory = LLMProviderFactory(self.settings)
        
        # Health monitoring
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = 0
        
        # Load configurations
        self._load_configurations()
        self._load_health_status()
        
        logger.info("ProviderConfigurationService initialized")
    
    # Configuration Management
    
    def create_configuration(
        self,
        provider: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> ProviderConfiguration:
        """
        Create new provider configuration.
        
        Args:
            provider: Provider name
            api_key: API key
            **kwargs: Additional configuration options
            
        Returns:
            Created configuration
        """
        config_data = {
            "provider": provider,
            "api_key": api_key,
            **kwargs
        }
        
        config = ProviderConfiguration(**config_data)
        self._configurations[provider] = config
        self._save_configurations()
        
        logger.info(f"Created configuration for provider: {provider}")
        return config
    
    def update_configuration(
        self,
        provider: str,
        **updates
    ) -> ProviderConfiguration:
        """
        Update existing provider configuration.
        
        Args:
            provider: Provider name
            **updates: Configuration updates
            
        Returns:
            Updated configuration
            
        Raises:
            ValueError: If provider not found
        """
        if provider not in self._configurations:
            raise ValueError(f"Configuration not found for provider: {provider}")
        
        config = self._configurations[provider]
        update_data = config.dict()
        update_data.update(updates)
        update_data["updated_at"] = datetime.now()
        
        updated_config = ProviderConfiguration(**update_data)
        self._configurations[provider] = updated_config
        self._save_configurations()
        
        logger.info(f"Updated configuration for provider: {provider}")
        return updated_config
    
    def delete_configuration(self, provider: str) -> None:
        """
        Delete provider configuration.
        
        Args:
            provider: Provider name
        """
        if provider in self._configurations:
            del self._configurations[provider]
            self._save_configurations()
            logger.info(f"Deleted configuration for provider: {provider}")
    
    def get_configuration(self, provider: str) -> Optional[ProviderConfiguration]:
        """
        Get provider configuration.
        
        Args:
            provider: Provider name
            
        Returns:
            Provider configuration or None
        """
        return self._configurations.get(provider)
    
    def list_configurations(self) -> List[ProviderConfiguration]:
        """Get all provider configurations."""
        return list(self._configurations.values())
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers."""
        return [
            provider for provider, config in self._configurations.items()
            if config.enabled
        ]
    
    # Environment Integration
    
    def sync_with_environment(self) -> None:
        """Synchronize configurations with environment variables."""
        env_provider = os.getenv("SELECTED_LLM_PROVIDER")
        env_model = os.getenv("SELECTED_LLM_MODEL")
        
        # Update from environment variables
        api_keys = {
            "ollama": os.getenv("OLLAMA_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY")
        }
        
        for provider, api_key in api_keys.items():
            if api_key:
                if provider not in self._configurations:
                    self.create_configuration(provider, api_key=api_key)
                else:
                    current_config = self._configurations[provider]
                    if current_config.api_key != api_key:
                        self.update_configuration(provider, api_key=api_key)
        
        logger.info("Synchronized configurations with environment")
    
    def set_active_provider(
        self,
        provider: str,
        model: Optional[str] = None,
        persist: bool = True
    ) -> None:
        """
        Set active provider and optionally model.
        
        Args:
            provider: Provider name
            model: Model name (optional)
            persist: Whether to persist to environment
        """
        provider = provider.lower()  # Normalize provider name
        
        if provider not in self._configurations:
            raise ValueError(f"Provider not configured: {provider}")
        
        config = self._configurations[provider]
        if not config.enabled:
            raise ValueError(f"Provider is disabled: {provider}")
        
        # Set environment variables
        os.environ["SELECTED_LLM_PROVIDER"] = provider
        if model:
            os.environ["SELECTED_LLM_MODEL"] = model
        elif "SELECTED_LLM_MODEL" in os.environ:
            del os.environ["SELECTED_LLM_MODEL"]
        
        logger.info(f"Set active provider: {provider}" + (f", model: {model}" if model else ""))
    
    # Health Monitoring
    
    async def check_provider_health(self, provider: str, force: bool = False) -> ProviderHealth:
        """
        Check health of specific provider.
        
        Args:
            provider: Provider name
            force: Force health check even if recently checked
            
        Returns:
            Provider health information
        """
        now = datetime.now()
        
        # Check if recent health check exists and force is not set
        if not force and provider in self._health_status:
            health = self._health_status[provider]
            if (now - health.last_check).seconds < self._health_check_interval:
                return health
        
        # Initialize health record
        health = self._health_status.get(provider, ProviderHealth(
            provider=provider,
            status=ProviderStatus.UNKNOWN,
            last_check=now
        ))
        
        health.last_check = now
        
        try:
            # Check if provider is configured
            config = self.get_configuration(provider)
            if not config:
                health.status = ProviderStatus.UNCONFIGURED
                health.error_message = "Provider not configured"
            elif not config.enabled:
                health.status = ProviderStatus.UNAVAILABLE
                health.error_message = "Provider disabled"
            else:
                # Perform actual health check
                start_time = time.time()
                
                try:
                    # Create provider instance and test
                    provider_instance = self._factory.create_provider(provider)
                    provider_instance.initialize()
                    
                    if provider_instance.is_available:
                        health.status = ProviderStatus.HEALTHY
                        health.response_time = time.time() - start_time
                        health.error_message = None
                        health.consecutive_failures = 0
                        health.last_success = now
                    else:
                        health.status = ProviderStatus.UNAVAILABLE
                        health.error_message = "Provider reports unavailable"
                        health.consecutive_failures += 1
                        
                except Exception as e:
                    health.status = ProviderStatus.UNAVAILABLE
                    health.error_message = str(e)
                    health.consecutive_failures += 1
                    
        except Exception as e:
            health.status = ProviderStatus.UNKNOWN
            health.error_message = f"Health check failed: {e}"
            health.consecutive_failures += 1
        
        self._health_status[provider] = health
        self._save_health_status()
        
        logger.info(f"Health check for {provider}: {health.status.value}")
        return health
    
    async def check_all_providers_health(self, force: bool = False) -> Dict[str, ProviderHealth]:
        """
        Check health of all configured providers.
        
        Args:
            force: Force health checks
            
        Returns:
            Health status for all providers
        """
        results = {}
        
        for provider in self._configurations.keys():
            try:
                results[provider] = await self.check_provider_health(provider, force)
            except Exception as e:
                logger.error(f"Failed to check health for {provider}: {e}")
                results[provider] = ProviderHealth(
                    provider=provider,
                    status=ProviderStatus.UNKNOWN,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
        
        return results
    
    def get_provider_health(self, provider: str) -> Optional[ProviderHealth]:
        """Get cached health status for provider."""
        return self._health_status.get(provider)
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy providers."""
        return [
            provider for provider, health in self._health_status.items()
            if health.status == ProviderStatus.HEALTHY
        ]
    
    # Backup and Restore
    
    def create_backup(self, name: Optional[str] = None) -> Path:
        """
        Create configuration backup.
        
        Args:
            name: Backup name (uses timestamp if None)
            
        Returns:
            Path to backup file
        """
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_file = self.backup_dir / f"config_backup_{name}.json"
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "configurations": {
                provider: config.dict() for provider, config in self._configurations.items()
            },
            "health_status": {
                provider: health.to_dict() for provider, health in self._health_status.items()
            }
        }
        
        backup_file.write_text(json.dumps(backup_data, indent=2, default=str))
        logger.info(f"Created configuration backup: {backup_file}")
        
        return backup_file
    
    def restore_backup(self, backup_file: Path) -> None:
        """
        Restore configuration from backup.
        
        Args:
            backup_file: Path to backup file
        """
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        backup_data = json.loads(backup_file.read_text())
        
        # Restore configurations
        self._configurations = {}
        for provider, config_data in backup_data.get("configurations", {}).items():
            self._configurations[provider] = ProviderConfiguration(**config_data)
        
        # Restore health status
        self._health_status = {}
        for provider, health_data in backup_data.get("health_status", {}).items():
            self._health_status[provider] = ProviderHealth.from_dict(health_data)
        
        self._save_configurations()
        self._save_health_status()
        
        logger.info(f"Restored configuration from backup: {backup_file}")
    
    def list_backups(self) -> List[Tuple[Path, datetime]]:
        """
        List available backups.
        
        Returns:
            List of (backup_file, timestamp) tuples
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("config_backup_*.json"):
            try:
                backup_data = json.loads(backup_file.read_text())
                timestamp = datetime.fromisoformat(backup_data["timestamp"])
                backups.append((backup_file, timestamp))
            except Exception as e:
                logger.warning(f"Invalid backup file {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x[1], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30) -> None:
        """
        Clean up old backup files.
        
        Args:
            keep_days: Days to keep backups
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup_file, timestamp in self.list_backups():
            if timestamp < cutoff_date:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file}")
    
    # Validation
    
    def validate_configuration(self, provider: str) -> List[str]:
        """
        Validate provider configuration.
        
        Args:
            provider: Provider name
            
        Returns:
            List of validation errors
        """
        errors = []
        
        config = self.get_configuration(provider)
        if not config:
            errors.append("Configuration not found")
            return errors
        
        # Check API key for non-Ollama providers
        if provider != "ollama" and not config.api_key:
            errors.append("API key is required")
        
        # Check base URL if specified
        if config.base_url and not config.base_url.startswith(("http://", "https://")):
            errors.append("Invalid base URL format")
        
        # Check timeout range
        if config.timeout and not (1 <= config.timeout <= 300):
            errors.append("Timeout must be between 1 and 300 seconds")
        
        # Check retry range
        if config.max_retries and not (1 <= config.max_retries <= 10):
            errors.append("Max retries must be between 1 and 10")
        
        return errors
    
    def validate_all_configurations(self) -> Dict[str, List[str]]:
        """
        Validate all provider configurations.
        
        Returns:
            Dictionary of provider -> validation errors
        """
        results = {}
        
        for provider in self._configurations.keys():
            errors = self.validate_configuration(provider)
            if errors:
                results[provider] = errors
        
        return results
    
    # Persistence
    
    def _load_configurations(self) -> None:
        """Load configurations from file."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                for provider, config_data in data.items():
                    self._configurations[provider] = ProviderConfiguration(**config_data)
                logger.info(f"Loaded {len(self._configurations)} configurations")
            except Exception as e:
                logger.error(f"Failed to load configurations: {e}")
                self._configurations = {}
    
    def _save_configurations(self) -> None:
        """Save configurations to file."""
        try:
            data = {
                provider: config.dict() for provider, config in self._configurations.items()
            }
            self.config_file.write_text(json.dumps(data, indent=2, default=str))
            logger.debug(f"Saved {len(self._configurations)} configurations")
        except Exception as e:
            logger.error(f"Failed to save configurations: {e}")
    
    def _load_health_status(self) -> None:
        """Load health status from file."""
        if self.health_file.exists():
            try:
                data = json.loads(self.health_file.read_text())
                for provider, health_data in data.items():
                    self._health_status[provider] = ProviderHealth.from_dict(health_data)
                logger.info(f"Loaded health status for {len(self._health_status)} providers")
            except Exception as e:
                logger.error(f"Failed to load health status: {e}")
                self._health_status = {}
    
    def _save_health_status(self) -> None:
        """Save health status to file."""
        try:
            data = {
                provider: health.to_dict() for provider, health in self._health_status.items()
            }
            self.health_file.write_text(json.dumps(data, indent=2, default=str))
            logger.debug(f"Saved health status for {len(self._health_status)} providers")
        except Exception as e:
            logger.error(f"Failed to save health status: {e}")
    
    # Cleanup
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        logger.info("Cleaning up ProviderConfigurationService")
        self._save_configurations()
        self._save_health_status()


# Convenience functions

def get_config_service(settings: Optional[Settings] = None) -> ProviderConfigurationService:
    """Get a ProviderConfigurationService instance."""
    return ProviderConfigurationService(settings)


async def quick_health_check(provider: str) -> ProviderHealth:
    """Quick health check for a provider."""
    service = get_config_service()
    return await service.check_provider_health(provider, force=True)