"""
Tests for configuration management system.
Following TDD principles - tests written first.
"""
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from arete.config import Settings, get_settings


class TestSettings:
    """Test configuration management with environment variables."""

    def test_settings_defaults(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        
        # Test default values
        assert settings.neo4j_uri == "bolt://localhost:7687"
        assert settings.neo4j_username == "neo4j"
        assert settings.neo4j_password == "password"
        assert settings.weaviate_url == "http://localhost:8080"
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.max_context_tokens == 5000
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 200

    def test_settings_from_environment(self, monkeypatch):
        """Test loading settings from environment variables."""
        # Set environment variables
        monkeypatch.setenv("NEO4J_URI", "bolt://test:7687")
        monkeypatch.setenv("NEO4J_USERNAME", "testuser")
        monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
        monkeypatch.setenv("WEAVIATE_URL", "http://test:8080")
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://test:11434")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("MAX_CONTEXT_TOKENS", "8000")
        
        settings = Settings()
        
        assert settings.neo4j_uri == "bolt://test:7687"
        assert settings.neo4j_username == "testuser"
        assert settings.neo4j_password == "testpass"
        assert settings.weaviate_url == "http://test:8080"
        assert settings.ollama_base_url == "http://test:11434"
        assert settings.log_level == "DEBUG"
        assert settings.debug is True
        assert settings.max_context_tokens == 8000

    def test_settings_validation(self):
        """Test validation of configuration values."""
        # Test invalid log level
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
        
        # Test invalid max_context_tokens (negative)
        with pytest.raises(ValidationError):
            Settings(max_context_tokens=-1)
        
        # Test invalid chunk_size (too small)
        with pytest.raises(ValidationError):
            Settings(chunk_size=50)
        
        # Test invalid chunk_overlap (too large)
        with pytest.raises(ValidationError):
            Settings(chunk_overlap=1500)

    def test_settings_from_env_file(self, tmp_path):
        """Test loading settings from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_content = """
NEO4J_URI=bolt://envfile:7687
NEO4J_USERNAME=envuser
NEO4J_PASSWORD=envpass
LOG_LEVEL=WARNING
DEBUG=false
MAX_CONTEXT_TOKENS=6000
"""
        env_file.write_text(env_content)
        
        # Load settings with custom env_file
        settings = Settings(_env_file=str(env_file))
        
        assert settings.neo4j_uri == "bolt://envfile:7687"
        assert settings.neo4j_username == "envuser"
        assert settings.neo4j_password == "envpass"
        assert settings.log_level == "WARNING"
        assert settings.debug is False
        assert settings.max_context_tokens == 6000

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_settings_repr(self):
        """Test that settings representation doesn't leak sensitive data."""
        settings = Settings(neo4j_password="secret123")
        repr_str = repr(settings)
        
        # Password should not appear in representation (excluded via repr=False)
        assert "secret123" not in repr_str
        assert "neo4j_password" not in repr_str  # Field excluded from repr
        
        # Other fields should be present
        assert "neo4j_uri" in repr_str
        assert "neo4j_username" in repr_str

    def test_database_url_properties(self):
        """Test computed database URL properties."""
        settings = Settings(
            neo4j_uri="bolt://test:7687",
            neo4j_username="testuser",
            neo4j_password="testpass"
        )
        
        assert settings.neo4j_auth == ("testuser", "testpass")


class TestConfigurationIntegration:
    """Integration tests for configuration management."""

    def test_config_directory_structure(self):
        """Test that config directory is properly structured."""
        config_dir = Path("config")
        
        # These directories should exist or be creatable
        expected_dirs = ["development", "production", "testing"]
        for dir_name in expected_dirs:
            dir_path = config_dir / dir_name
            assert dir_path.exists() or dir_path.parent.exists()

    def test_environment_specific_configs(self, tmp_path):
        """Test loading environment-specific configurations."""
        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        dev_config = config_dir / "development.env"
        dev_config.write_text("LOG_LEVEL=DEBUG\nDEBUG=true")
        
        prod_config = config_dir / "production.env"
        prod_config.write_text("LOG_LEVEL=ERROR\nDEBUG=false")
        
        # Test development config
        dev_settings = Settings(_env_file=str(dev_config))
        assert dev_settings.log_level == "DEBUG"
        assert dev_settings.debug is True
        
        # Test production config
        prod_settings = Settings(_env_file=str(prod_config))
        assert prod_settings.log_level == "ERROR"
        assert prod_settings.debug is False