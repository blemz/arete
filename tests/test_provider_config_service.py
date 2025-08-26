"""
Tests for Provider Configuration Management Service.

Comprehensive test suite for provider configuration, validation, health monitoring,
and backup/restore functionality.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from arete.services.provider_config_service import (
    ProviderConfigurationService,
    ProviderConfiguration,
    ProviderHealth,
    ProviderStatus,
    ConfigurationSource
)
from arete.config import Settings


class TestProviderConfiguration:
    """Test provider configuration model."""
    
    def test_provider_configuration_creation(self):
        """Test creating a provider configuration."""
        config = ProviderConfiguration(
            provider="ollama",
            api_key="test-key",
            base_url="http://localhost:11434",
            timeout=30,
            enabled=True
        )
        
        assert config.provider == "ollama"
        assert config.api_key == "test-key"
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 30
        assert config.enabled is True
        assert config.priority == 1  # default
    
    def test_provider_configuration_validation(self):
        """Test provider configuration validation."""
        # Valid provider
        config = ProviderConfiguration(provider="anthropic")
        assert config.provider == "anthropic"
        
        # Invalid provider should raise validation error
        with pytest.raises(ValueError, match="Invalid provider"):
            ProviderConfiguration(provider="invalid_provider")
    
    def test_provider_configuration_defaults(self):
        """Test default values for provider configuration."""
        config = ProviderConfiguration(provider="openai")
        
        assert config.enabled is True
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.priority == 1
        assert config.models == []
        assert config.tags == []
        assert config.metadata == {}
    
    def test_provider_configuration_json_serialization(self):
        """Test JSON serialization of provider configuration."""
        config = ProviderConfiguration(
            provider="gemini",
            api_key="test-key",
            models=["gemini-pro", "gemini-1.5-pro"],
            tags=["fast", "multimodal"]
        )
        
        config_dict = config.dict()
        assert config_dict["provider"] == "gemini"
        assert config_dict["api_key"] == "test-key"
        assert config_dict["models"] == ["gemini-pro", "gemini-1.5-pro"]
        assert config_dict["tags"] == ["fast", "multimodal"]


class TestProviderHealth:
    """Test provider health monitoring."""
    
    def test_provider_health_creation(self):
        """Test creating provider health record."""
        now = datetime.now()
        health = ProviderHealth(
            provider="ollama",
            status=ProviderStatus.HEALTHY,
            last_check=now,
            response_time=0.15,
            consecutive_failures=0
        )
        
        assert health.provider == "ollama"
        assert health.status == ProviderStatus.HEALTHY
        assert health.last_check == now
        assert health.response_time == 0.15
        assert health.consecutive_failures == 0
    
    def test_provider_health_serialization(self):
        """Test provider health to/from dictionary conversion."""
        now = datetime.now()
        health = ProviderHealth(
            provider="anthropic",
            status=ProviderStatus.UNAVAILABLE,
            last_check=now,
            error_message="API key invalid"
        )
        
        health_dict = health.to_dict()
        assert health_dict["provider"] == "anthropic"
        assert health_dict["status"] == "unavailable"
        assert health_dict["error_message"] == "API key invalid"
        
        # Test round-trip conversion
        restored_health = ProviderHealth.from_dict(health_dict)
        assert restored_health.provider == health.provider
        assert restored_health.status == health.status
        assert restored_health.error_message == health.error_message


class TestProviderConfigurationService:
    """Test provider configuration service."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_service(self, temp_config_dir):
        """Create configuration service with temporary directory."""
        settings = Settings()
        return ProviderConfigurationService(settings, temp_config_dir)
    
    def test_service_initialization(self, config_service, temp_config_dir):
        """Test configuration service initialization."""
        assert config_service.config_dir == temp_config_dir
        assert config_service.config_file == temp_config_dir / "providers.json"
        assert config_service.health_file == temp_config_dir / "health.json"
        assert config_service.backup_dir == temp_config_dir / "backups"
        
        # Check directories were created
        assert config_service.config_dir.exists()
        assert config_service.backup_dir.exists()
    
    def test_create_configuration(self, config_service):
        """Test creating provider configuration."""
        config = config_service.create_configuration(
            "ollama",
            api_key="test-key",
            timeout=60,
            enabled=True
        )
        
        assert config.provider == "ollama"
        assert config.api_key == "test-key"
        assert config.timeout == 60
        assert config.enabled is True
        
        # Check it's stored in service
        stored_config = config_service.get_configuration("ollama")
        assert stored_config is not None
        assert stored_config.provider == "ollama"
    
    def test_update_configuration(self, config_service):
        """Test updating provider configuration."""
        # Create initial configuration
        config_service.create_configuration("anthropic", api_key="old-key")
        
        # Update configuration
        updated_config = config_service.update_configuration(
            "anthropic",
            api_key="new-key",
            timeout=45
        )
        
        assert updated_config.api_key == "new-key"
        assert updated_config.timeout == 45
        
        # Verify stored configuration was updated
        stored_config = config_service.get_configuration("anthropic")
        assert stored_config.api_key == "new-key"
        assert stored_config.timeout == 45
    
    def test_update_nonexistent_configuration(self, config_service):
        """Test updating non-existent configuration raises error."""
        with pytest.raises(ValueError, match="Configuration not found"):
            config_service.update_configuration("nonexistent", api_key="key")
    
    def test_delete_configuration(self, config_service):
        """Test deleting provider configuration."""
        # Create configuration
        config_service.create_configuration("openai", api_key="test-key")
        assert config_service.get_configuration("openai") is not None
        
        # Delete configuration
        config_service.delete_configuration("openai")
        assert config_service.get_configuration("openai") is None
    
    def test_list_configurations(self, config_service):
        """Test listing all configurations."""
        # Initially empty
        configs = config_service.list_configurations()
        assert len(configs) == 0
        
        # Add configurations
        config_service.create_configuration("ollama", api_key="key1")
        config_service.create_configuration("anthropic", api_key="key2")
        
        configs = config_service.list_configurations()
        assert len(configs) == 2
        
        providers = [config.provider for config in configs]
        assert "ollama" in providers
        assert "anthropic" in providers
    
    def test_get_enabled_providers(self, config_service):
        """Test getting enabled providers."""
        # Create enabled and disabled providers
        config_service.create_configuration("ollama", enabled=True)
        config_service.create_configuration("anthropic", enabled=False)
        config_service.create_configuration("openai", enabled=True)
        
        enabled_providers = config_service.get_enabled_providers()
        
        assert len(enabled_providers) == 2
        assert "ollama" in enabled_providers
        assert "openai" in enabled_providers
        assert "anthropic" not in enabled_providers
    
    @patch.dict('os.environ', {
        'SELECTED_LLM_PROVIDER': 'anthropic',
        'ANTHROPIC_API_KEY': 'sk-test-123',
        'OPENAI_API_KEY': 'sk-openai-456'
    })
    def test_sync_with_environment(self, config_service):
        """Test synchronizing with environment variables."""
        config_service.sync_with_environment()
        
        # Check configurations were created from environment
        anthropic_config = config_service.get_configuration("anthropic")
        assert anthropic_config is not None
        assert anthropic_config.api_key == "sk-test-123"
        
        openai_config = config_service.get_configuration("openai")
        assert openai_config is not None
        assert openai_config.api_key == "sk-openai-456"
    
    def test_set_active_provider(self, config_service):
        """Test setting active provider."""
        # Create configuration
        config_service.create_configuration("ollama", enabled=True)
        
        with patch.dict('os.environ', {}, clear=True):
            config_service.set_active_provider("ollama")
            
            # Check environment variable was set
            import os
            assert os.environ.get("SELECTED_LLM_PROVIDER") == "ollama"
    
    def test_set_active_provider_with_model(self, config_service):
        """Test setting active provider with model."""
        config_service.create_configuration("anthropic", enabled=True)
        
        with patch.dict('os.environ', {}, clear=True):
            config_service.set_active_provider("anthropic", model="claude-3-opus")
            
            import os
            assert os.environ.get("SELECTED_LLM_PROVIDER") == "anthropic"
            assert os.environ.get("SELECTED_LLM_MODEL") == "claude-3-opus"
    
    def test_set_active_provider_unconfigured(self, config_service):
        """Test setting unconfigured provider raises error."""
        with pytest.raises(ValueError, match="Provider not configured"):
            config_service.set_active_provider("unconfigured")
    
    def test_set_active_provider_disabled(self, config_service):
        """Test setting disabled provider raises error."""
        config_service.create_configuration("ollama", enabled=False)
        
        with pytest.raises(ValueError, match="Provider is disabled"):
            config_service.set_active_provider("ollama")


class TestProviderHealthMonitoring:
    """Test provider health monitoring functionality."""
    
    @pytest.fixture
    def config_service(self, temp_config_dir):
        """Create configuration service with mocked factory."""
        settings = Settings()
        service = ProviderConfigurationService(settings, temp_config_dir)
        
        # Mock the factory
        mock_factory = Mock()
        service._factory = mock_factory
        
        return service, mock_factory
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_check_provider_health_unconfigured(self, config_service):
        """Test health check for unconfigured provider."""
        service, _ = config_service
        
        health = await service.check_provider_health("unconfigured")
        
        assert health.provider == "unconfigured"
        assert health.status == ProviderStatus.UNCONFIGURED
        assert health.error_message == "Provider not configured"
    
    @pytest.mark.asyncio
    async def test_check_provider_health_disabled(self, config_service):
        """Test health check for disabled provider."""
        service, _ = config_service
        
        # Create disabled configuration
        service.create_configuration("ollama", enabled=False)
        
        health = await service.check_provider_health("ollama")
        
        assert health.provider == "ollama"
        assert health.status == ProviderStatus.UNAVAILABLE
        assert health.error_message == "Provider disabled"
    
    @pytest.mark.asyncio
    async def test_check_provider_health_success(self, config_service):
        """Test successful health check."""
        service, mock_factory = config_service
        
        # Create configuration
        service.create_configuration("ollama", enabled=True)
        
        # Mock successful provider
        mock_provider = Mock()
        mock_provider.is_available = True
        mock_factory.create_provider.return_value = mock_provider
        
        health = await service.check_provider_health("ollama")
        
        assert health.provider == "ollama"
        assert health.status == ProviderStatus.HEALTHY
        assert health.response_time is not None
        assert health.consecutive_failures == 0
        assert health.last_success is not None
        
        mock_factory.create_provider.assert_called_once_with("ollama")
        mock_provider.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_provider_health_unavailable(self, config_service):
        """Test health check for unavailable provider."""
        service, mock_factory = config_service
        
        # Create configuration
        service.create_configuration("anthropic", enabled=True)
        
        # Mock unavailable provider
        mock_provider = Mock()
        mock_provider.is_available = False
        mock_factory.create_provider.return_value = mock_provider
        
        health = await service.check_provider_health("anthropic")
        
        assert health.provider == "anthropic"
        assert health.status == ProviderStatus.UNAVAILABLE
        assert health.error_message == "Provider reports unavailable"
        assert health.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_check_provider_health_exception(self, config_service):
        """Test health check when provider raises exception."""
        service, mock_factory = config_service
        
        # Create configuration
        service.create_configuration("openai", enabled=True)
        
        # Mock provider that raises exception
        mock_factory.create_provider.side_effect = Exception("Connection failed")
        
        health = await service.check_provider_health("openai")
        
        assert health.provider == "openai"
        assert health.status == ProviderStatus.UNAVAILABLE
        assert "Connection failed" in health.error_message
        assert health.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_check_all_providers_health(self, config_service):
        """Test checking health of all providers."""
        service, mock_factory = config_service
        
        # Create configurations
        service.create_configuration("ollama", enabled=True)
        service.create_configuration("anthropic", enabled=True)
        
        # Mock providers
        mock_provider1 = Mock()
        mock_provider1.is_available = True
        mock_provider2 = Mock()
        mock_provider2.is_available = False
        
        mock_factory.create_provider.side_effect = lambda p: (
            mock_provider1 if p == "ollama" else mock_provider2
        )
        
        health_results = await service.check_all_providers_health()
        
        assert len(health_results) == 2
        assert health_results["ollama"].status == ProviderStatus.HEALTHY
        assert health_results["anthropic"].status == ProviderStatus.UNAVAILABLE
    
    def test_get_healthy_providers(self, config_service):
        """Test getting list of healthy providers."""
        service, _ = config_service
        
        # Manually set health status
        service._health_status = {
            "healthy1": ProviderHealth("healthy1", ProviderStatus.HEALTHY, datetime.now()),
            "healthy2": ProviderHealth("healthy2", ProviderStatus.HEALTHY, datetime.now()),
            "unhealthy": ProviderHealth("unhealthy", ProviderStatus.UNAVAILABLE, datetime.now())
        }
        
        healthy_providers = service.get_healthy_providers()
        
        assert len(healthy_providers) == 2
        assert "healthy1" in healthy_providers
        assert "healthy2" in healthy_providers
        assert "unhealthy" not in healthy_providers


class TestBackupAndRestore:
    """Test backup and restore functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_service(self, temp_config_dir):
        """Create configuration service with test data."""
        settings = Settings()
        service = ProviderConfigurationService(settings, temp_config_dir)
        
        # Add test configurations
        service.create_configuration("ollama", api_key="key1", enabled=True)
        service.create_configuration("anthropic", api_key="key2", enabled=False)
        
        # Add test health data
        service._health_status = {
            "ollama": ProviderHealth("ollama", ProviderStatus.HEALTHY, datetime.now()),
            "anthropic": ProviderHealth("anthropic", ProviderStatus.UNCONFIGURED, datetime.now())
        }
        
        return service
    
    def test_create_backup(self, config_service):
        """Test creating configuration backup."""
        backup_path = config_service.create_backup("test_backup")
        
        assert backup_path.exists()
        assert backup_path.name.startswith("config_backup_test_backup")
        assert backup_path.suffix == ".json"
        
        # Verify backup content
        backup_data = json.loads(backup_path.read_text())
        
        assert "timestamp" in backup_data
        assert "configurations" in backup_data
        assert "health_status" in backup_data
        
        assert len(backup_data["configurations"]) == 2
        assert "ollama" in backup_data["configurations"]
        assert "anthropic" in backup_data["configurations"]
    
    def test_create_backup_automatic_name(self, config_service):
        """Test creating backup with automatic name generation."""
        backup_path = config_service.create_backup()
        
        assert backup_path.exists()
        # Should contain timestamp in name
        assert len(backup_path.stem.split("_")) >= 3  # config_backup_TIMESTAMP
    
    def test_restore_backup(self, config_service, temp_config_dir):
        """Test restoring configuration from backup."""
        # Create backup
        backup_path = config_service.create_backup("restore_test")
        
        # Clear current configurations
        config_service._configurations.clear()
        config_service._health_status.clear()
        
        # Restore from backup
        config_service.restore_backup(backup_path)
        
        # Verify restoration
        configs = config_service.list_configurations()
        assert len(configs) == 2
        
        providers = [config.provider for config in configs]
        assert "ollama" in providers
        assert "anthropic" in providers
        
        # Verify health status restored
        assert len(config_service._health_status) == 2
        assert "ollama" in config_service._health_status
        assert "anthropic" in config_service._health_status
    
    def test_restore_nonexistent_backup(self, config_service, temp_config_dir):
        """Test restoring from non-existent backup raises error."""
        nonexistent_path = temp_config_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            config_service.restore_backup(nonexistent_path)
    
    def test_list_backups(self, config_service):
        """Test listing available backups."""
        # Create multiple backups
        backup1 = config_service.create_backup("backup1")
        backup2 = config_service.create_backup("backup2")
        
        backups = config_service.list_backups()
        
        assert len(backups) >= 2
        
        backup_files = [backup[0] for backup in backups]
        assert backup1 in backup_files
        assert backup2 in backup_files
        
        # Check timestamps
        for backup_file, timestamp in backups:
            assert isinstance(timestamp, datetime)
    
    def test_cleanup_old_backups(self, config_service):
        """Test cleanup of old backup files."""
        # Create backup
        backup_path = config_service.create_backup("old_backup")
        
        # Manually modify timestamp to make it old
        old_timestamp = datetime.now() - timedelta(days=35)
        backup_data = json.loads(backup_path.read_text())
        backup_data["timestamp"] = old_timestamp.isoformat()
        backup_path.write_text(json.dumps(backup_data))
        
        # Cleanup old backups (keep 30 days)
        config_service.cleanup_old_backups(keep_days=30)
        
        # Verify old backup was removed
        assert not backup_path.exists()


class TestConfigurationValidation:
    """Test configuration validation functionality."""
    
    @pytest.fixture
    def config_service(self):
        """Create configuration service for validation testing."""
        with TemporaryDirectory() as temp_dir:
            settings = Settings()
            yield ProviderConfigurationService(settings, Path(temp_dir))
    
    def test_validate_configuration_success(self, config_service):
        """Test successful configuration validation."""
        # Create valid configuration
        config_service.create_configuration(
            "anthropic",
            api_key="sk-test-key",
            base_url="https://api.anthropic.com",
            timeout=30,
            max_retries=3
        )
        
        errors = config_service.validate_configuration("anthropic")
        assert len(errors) == 0
    
    def test_validate_configuration_missing_api_key(self, config_service):
        """Test validation with missing API key."""
        # Create configuration without API key (non-Ollama)
        config_service.create_configuration("anthropic")
        
        errors = config_service.validate_configuration("anthropic")
        assert len(errors) == 1
        assert "API key is required" in errors[0]
    
    def test_validate_configuration_ollama_no_api_key_required(self, config_service):
        """Test validation for Ollama doesn't require API key."""
        config_service.create_configuration("ollama")
        
        errors = config_service.validate_configuration("ollama")
        assert len(errors) == 0  # No API key required for Ollama
    
    def test_validate_configuration_invalid_base_url(self, config_service):
        """Test validation with invalid base URL."""
        config_service.create_configuration(
            "openai",
            api_key="sk-test",
            base_url="invalid-url"
        )
        
        errors = config_service.validate_configuration("openai")
        assert any("Invalid base URL format" in error for error in errors)
    
    def test_validate_configuration_invalid_timeout(self, config_service):
        """Test validation with invalid timeout."""
        # Since Pydantic validates ranges at model creation, test that validation catches this
        from pydantic_core import ValidationError
        
        with pytest.raises(ValidationError):
            config_service.create_configuration(
                "gemini",
                api_key="test-key",
                timeout=500  # Too high
            )
    
    def test_validate_configuration_invalid_retries(self, config_service):
        """Test validation with invalid retry count."""
        # Since Pydantic validates ranges at model creation, test that validation catches this
        from pydantic_core import ValidationError
        
        with pytest.raises(ValidationError):
            config_service.create_configuration(
                "openrouter",
                api_key="test-key",
                max_retries=15  # Too high
            )
    
    def test_validate_configuration_not_found(self, config_service):
        """Test validation of non-existent configuration."""
        errors = config_service.validate_configuration("nonexistent")
        assert len(errors) == 1
        assert "Configuration not found" in errors[0]
    
    def test_validate_all_configurations(self, config_service):
        """Test validating all configurations."""
        # Create valid and invalid configurations
        config_service.create_configuration("ollama")  # Valid
        config_service.create_configuration("anthropic")  # Invalid (no API key)
        
        validation_results = config_service.validate_all_configurations()
        
        # Should only return configurations with errors
        assert "anthropic" in validation_results
        assert "ollama" not in validation_results  # Valid, so not included
        
        assert len(validation_results["anthropic"]) > 0


class TestServicePersistence:
    """Test configuration and health status persistence."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_configuration_persistence(self, temp_config_dir):
        """Test that configurations are persisted and loaded."""
        # Create service and add configuration
        settings = Settings()
        service1 = ProviderConfigurationService(settings, temp_config_dir)
        service1.create_configuration("ollama", api_key="test-key", timeout=60)
        
        # Create new service instance (simulates restart)
        service2 = ProviderConfigurationService(settings, temp_config_dir)
        
        # Verify configuration was loaded
        config = service2.get_configuration("ollama")
        assert config is not None
        assert config.provider == "ollama"
        assert config.api_key == "test-key"
        assert config.timeout == 60
    
    def test_health_status_persistence(self, temp_config_dir):
        """Test that health status is persisted and loaded."""
        settings = Settings()
        
        # Create service and add health status
        service1 = ProviderConfigurationService(settings, temp_config_dir)
        now = datetime.now()
        health = ProviderHealth("ollama", ProviderStatus.HEALTHY, now, response_time=0.15)
        service1._health_status["ollama"] = health
        service1._save_health_status()
        
        # Create new service instance
        service2 = ProviderConfigurationService(settings, temp_config_dir)
        
        # Verify health status was loaded
        loaded_health = service2.get_provider_health("ollama")
        assert loaded_health is not None
        assert loaded_health.provider == "ollama"
        assert loaded_health.status == ProviderStatus.HEALTHY
        assert loaded_health.response_time == 0.15
    
    def test_cleanup_service(self, temp_config_dir):
        """Test service cleanup saves state."""
        settings = Settings()
        service = ProviderConfigurationService(settings, temp_config_dir)
        
        # Add configuration and health data
        service.create_configuration("ollama", api_key="key")
        service._health_status["ollama"] = ProviderHealth("ollama", ProviderStatus.HEALTHY, datetime.now())
        
        # Cleanup should save data
        service.cleanup()
        
        # Verify data was saved
        assert service.config_file.exists()
        assert service.health_file.exists()
        
        config_data = json.loads(service.config_file.read_text())
        health_data = json.loads(service.health_file.read_text())
        
        assert "ollama" in config_data
        assert "ollama" in health_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])