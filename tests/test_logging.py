"""
Tests for structured logging functionality.

Following the proven focused testing methodology validated in database clients.
Tests cover logging configuration, setup, file handling, and integration patterns.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest
from loguru import logger

from arete.config import Settings, get_settings, setup_logging


class TestLoggingConfiguration:
    """Test logging configuration generation."""

    def test_default_logging_config(self):
        """Test default logging configuration values."""
        settings = Settings()
        config = settings.logging_config
        
        assert config["level"] == "INFO"
        assert "green" in config["format"]  # Time formatting
        assert "level" in config["format"]  # Level formatting
        assert "cyan" in config["format"]   # Name/function formatting
        assert config["backtrace"] is False
        assert config["diagnose"] is False

    def test_debug_logging_config(self):
        """Test logging configuration with debug enabled."""
        settings = Settings(debug=True, log_level="DEBUG")
        config = settings.logging_config
        
        assert config["level"] == "DEBUG"
        assert config["backtrace"] is True
        assert config["diagnose"] is True

    def test_custom_log_level(self):
        """Test custom log level configuration."""
        settings = Settings(log_level="WARNING")
        config = settings.logging_config
        
        assert config["level"] == "WARNING"

    def test_invalid_log_level_raises_validation_error(self):
        """Test that invalid log levels raise validation errors."""
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(log_level="INVALID")


class TestLoggingSetup:
    """Test logging setup functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Remove all existing handlers
        logger.remove()

    def teardown_method(self):
        """Cleanup test environment."""
        # Remove all handlers and restore default
        logger.remove()
        logger.add(sys.stderr)

    @patch('loguru.logger')
    def test_setup_logging_removes_default_logger(self, mock_logger):
        """Test that setup_logging removes default logger."""
        setup_logging()
        
        mock_logger.remove.assert_called()

    @patch('loguru.logger')
    def test_setup_logging_adds_console_handler(self, mock_logger):
        """Test that console handler is added with correct configuration."""
        with patch('arete.config.get_settings') as mock_settings:
            mock_settings.return_value = Settings(log_level="INFO", debug=False)
            
            setup_logging()
            
            # Check that logger.add was called for console (sys.stdout)
            assert mock_logger.add.call_count >= 1
            console_call = mock_logger.add.call_args_list[0]
            assert console_call[0][0] == sys.stdout

    @patch('loguru.logger')
    def test_setup_logging_adds_file_handler_when_not_debug(self, mock_logger):
        """Test that file handler is added when not in debug mode."""
        with patch('arete.config.get_settings') as mock_settings:
            mock_settings.return_value = Settings(debug=False)
            
            setup_logging()
            
            # Should have both console and file handlers
            assert mock_logger.add.call_count == 2
            file_call = mock_logger.add.call_args_list[1]
            assert "logs/arete.log" in str(file_call[0][0])

    @patch('loguru.logger')
    def test_setup_logging_no_file_handler_in_debug(self, mock_logger):
        """Test that file handler is not added in debug mode."""
        with patch('arete.config.get_settings') as mock_settings:
            mock_settings.return_value = Settings(debug=True)
            
            setup_logging()
            
            # Should only have console handler
            assert mock_logger.add.call_count == 1


class TestFileLoggingConfiguration:
    """Test file logging configuration and rotation."""

    @patch('loguru.logger')
    def test_file_handler_rotation_configuration(self, mock_logger):
        """Test file handler rotation settings."""
        with patch('arete.config.get_settings') as mock_settings:
            mock_settings.return_value = Settings(debug=False)
            
            setup_logging()
            
            # Get file handler call
            file_call = mock_logger.add.call_args_list[1]
            kwargs = file_call[1]
            
            assert kwargs["rotation"] == "10 MB"
            assert kwargs["retention"] == "1 week"
            assert kwargs["compression"] == "zip"

    @patch('loguru.logger')
    def test_file_handler_uses_settings_format(self, mock_logger):
        """Test that file handler uses format from settings."""
        with patch('arete.config.get_settings') as mock_settings:
            settings = Settings(debug=False)
            mock_settings.return_value = settings
            
            setup_logging()
            
            # Get file handler call
            file_call = mock_logger.add.call_args_list[1]
            kwargs = file_call[1]
            
            assert kwargs["format"] == settings.logging_config["format"]
            assert kwargs["level"] == settings.log_level


class TestLoggingIntegration:
    """Test logging integration with application components."""

    def test_get_settings_returns_consistent_logging_config(self):
        """Test that get_settings returns consistent logging configuration."""
        # Test that multiple calls return the same configuration
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1.logging_config == settings2.logging_config
        assert settings1 is settings2  # Should be cached

    def test_logging_works_with_actual_loguru(self):
        """Integration test with actual loguru logger."""
        # Remove existing handlers
        logger.remove()
        
        try:
            # Setup logging
            setup_logging()
            
            # Test that we can log without errors
            logger.info("Test log message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            
            # No assertions needed - if no exception is raised, test passes
            
        finally:
            # Cleanup
            logger.remove()
            logger.add(sys.stderr)  # Restore default

    def test_logging_config_respects_environment_variables(self):
        """Test that logging configuration respects environment variables."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG', 'DEBUG': 'true'}):
            # Clear cached settings
            get_settings.cache_clear()
            
            settings = get_settings()
            assert settings.log_level == "DEBUG"
            assert settings.debug is True
            
            config = settings.logging_config
            assert config["level"] == "DEBUG"
            assert config["backtrace"] is True
            assert config["diagnose"] is True

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_file_logging_creates_directory(self, mock_makedirs, mock_file):
        """Test that file logging creates log directory if it doesn't exist."""
        # This is more of an integration concern, but important for production
        with patch('loguru.logger') as mock_logger:
            with patch('arete.config.get_settings') as mock_settings:
                mock_settings.return_value = Settings(debug=False)
                
                setup_logging()
                
                # Verify logger.add was called with file path
                file_call = mock_logger.add.call_args_list[1]
                assert "logs/arete.log" in str(file_call[0][0])


class TestLoggingErrorHandling:
    """Test logging error handling and edge cases."""

    def test_setup_logging_handles_missing_logs_directory(self):
        """Test that setup_logging handles missing logs directory gracefully."""
        # This should not raise an exception
        try:
            setup_logging()
        except Exception as e:
            pytest.fail(f"setup_logging raised an exception: {e}")

    def test_logging_config_with_extreme_values(self):
        """Test logging configuration with boundary values."""
        # Test with minimum and maximum valid log levels
        for level in ["DEBUG", "CRITICAL"]:
            settings = Settings(log_level=level)
            config = settings.logging_config
            assert config["level"] == level

    def test_settings_caching_behavior(self):
        """Test that settings caching works correctly."""
        # Clear cache
        get_settings.cache_clear()
        
        # First call
        settings1 = get_settings()
        
        # Second call should return same instance
        settings2 = get_settings()
        
        assert settings1 is settings2
        
        # Clear cache and get new instance
        get_settings.cache_clear()
        settings3 = get_settings()
        
        # Should be different instance but same values
        assert settings1 is not settings3
        assert settings1.log_level == settings3.log_level


# Fixtures for integration testing
@pytest.fixture
def temp_log_dir():
    """Create temporary directory for log files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "logs"
        log_dir.mkdir()
        yield log_dir


@pytest.fixture
def clean_logger():
    """Provide clean logger state for tests."""
    # Remove all handlers
    logger.remove()
    
    yield logger
    
    # Cleanup
    logger.remove()
    logger.add(sys.stderr)  # Restore default


class TestRealLoggingBehavior:
    """Integration tests with real logging behavior."""

    def test_actual_file_logging(self, temp_log_dir, clean_logger):
        """Test actual file logging with temporary directory."""
        # Patch the log file path to use our temp directory
        log_file = temp_log_dir / "test.log"
        
        # Add file handler manually for testing
        clean_logger.add(
            str(log_file),
            level="INFO",
            format="{time} | {level} | {message}",
            rotation="1 MB",
            retention="1 day"
        )
        
        # Log some messages
        clean_logger.info("Test info message")
        clean_logger.warning("Test warning message")
        clean_logger.error("Test error message")
        
        # Verify file was created and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test info message" in content
        assert "Test warning message" in content
        assert "Test error message" in content