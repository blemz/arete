"""
Base service interfaces and error classes for Arete system.

Provides abstract base classes and common error types for all service layer
components. Enables consistent error handling and service patterns across
the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ServiceError(Exception):
    """Base exception for service layer errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize service error.
        
        Args:
            message: Error message
            details: Additional error details and context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    pass


class InitializationError(ServiceError):
    """Raised when service initialization fails."""
    pass


class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass


class ProcessingError(ServiceError):
    """Raised when data processing fails."""
    pass


class BaseService(ABC):
    """
    Abstract base service class defining common service patterns.
    
    Provides standard initialization, configuration, and error handling
    patterns for all service implementations.
    """
    
    def __init__(self, settings: Optional[Any] = None):
        """
        Initialize base service.
        
        Args:
            settings: Configuration settings for the service
        """
        self.settings = settings
        self._is_initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is properly initialized."""
        return self._is_initialized
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service (must be implemented by subclasses)."""
        pass
    
    def validate_initialization(self) -> None:
        """Validate that service is properly initialized."""
        if not self.is_initialized:
            raise InitializationError(
                f"{self.__class__.__name__} is not initialized. Call initialize() first."
            )
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status (must be implemented by subclasses)."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup service resources (override if needed)."""
        pass