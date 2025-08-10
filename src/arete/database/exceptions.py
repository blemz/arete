"""Database-specific exceptions for Arete Graph-RAG system."""

from typing import Any, Optional


class DatabaseError(Exception):
    """Base exception for all database-related errors."""
    
    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(DatabaseError):
    """Raised when database query fails."""
    pass


class DatabaseTransactionError(DatabaseError):
    """Raised when database transaction fails."""
    pass


# Extend existing Neo4j exceptions for better error handling
class CypherError(DatabaseQueryError):
    """Raised when Cypher query has syntax errors."""
    pass