"""Environment configuration management for Arete."""

import os
from typing import Dict, Any, Optional
from enum import Enum
import logging


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class EnvironmentConfig:
    """Environment configuration manager."""
    
    def __init__(self):
        self.env = Environment(os.getenv("ENVIRONMENT", "development"))
        self._load_environment_variables()
    
    def _load_environment_variables(self):
        """Load environment-specific variables."""
        env_file_map = {
            Environment.DEVELOPMENT: ".env.development",
            Environment.STAGING: ".env.staging", 
            Environment.PRODUCTION: ".env.production",
            Environment.TESTING: ".env.testing",
        }
        
        env_file = env_file_map.get(self.env, ".env")
        
        if os.path.exists(env_file):
            from dotenv import load_dotenv
            load_dotenv(env_file)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == Environment.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.env == Environment.STAGING
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.env == Environment.TESTING
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        if self.is_production:
            return {
                "url": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/arete_prod"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
                "ssl_mode": "require",
            }
        elif self.is_staging:
            return {
                "url": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/arete_staging"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "15")),
                "ssl_mode": "prefer",
            }
        else:
            return {
                "url": os.getenv("DATABASE_URL", "sqlite:///arete_dev.db"),
                "pool_size": 5,
                "max_overflow": 10,
            }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        if self.is_production:
            return {
                "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                "connection_pool_max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
                "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
                "socket_connect_timeout": int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
                "retry_on_timeout": True,
                "ssl": os.getenv("REDIS_SSL", "false").lower() == "true",
            }
        elif self.is_staging:
            return {
                "url": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
                "connection_pool_max_connections": 25,
                "socket_timeout": 10,
            }
        else:
            return {
                "url": os.getenv("REDIS_URL", "redis://localhost:6379/2"),
                "connection_pool_max_connections": 10,
            }
    
    def get_rag_service_config(self) -> Dict[str, Any]:
        """Get RAG service configuration."""
        base_config = {
            "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "neo4j_user": os.getenv("NEO4J_USER", "neo4j"),
            "neo4j_password": os.getenv("NEO4J_PASSWORD", "password"),
            "weaviate_url": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            "weaviate_api_key": os.getenv("WEAVIATE_API_KEY"),
            "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "openai"),
            "kg_llm_provider": os.getenv("KG_LLM_PROVIDER", "openai"),
        }
        
        if self.is_production:
            base_config.update({
                "query_timeout": int(os.getenv("RAG_QUERY_TIMEOUT", "30")),
                "max_concurrent_queries": int(os.getenv("RAG_MAX_CONCURRENT", "10")),
                "cache_ttl": int(os.getenv("RAG_CACHE_TTL", "3600")),
                "retry_attempts": int(os.getenv("RAG_RETRY_ATTEMPTS", "3")),
                "circuit_breaker_threshold": int(os.getenv("RAG_CB_THRESHOLD", "5")),
            })
        elif self.is_staging:
            base_config.update({
                "query_timeout": int(os.getenv("RAG_QUERY_TIMEOUT", "60")),
                "max_concurrent_queries": int(os.getenv("RAG_MAX_CONCURRENT", "5")),
                "cache_ttl": int(os.getenv("RAG_CACHE_TTL", "1800")),
            })
        else:
            base_config.update({
                "query_timeout": int(os.getenv("RAG_QUERY_TIMEOUT", "120")),
                "max_concurrent_queries": int(os.getenv("RAG_MAX_CONCURRENT", "2")),
                "cache_ttl": 0,  # No caching in development
            })
        
        return base_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        if self.is_production:
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "standard": {
                        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    },
                    "json": {
                        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                        "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "level": "INFO",
                        "class": "logging.StreamHandler",
                        "formatter": "json",
                    },
                    "file": {
                        "level": "INFO",
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "/var/log/arete/app.log",
                        "maxBytes": 100 * 1024 * 1024,  # 100MB
                        "backupCount": 5,
                        "formatter": "json",
                    },
                    "error_file": {
                        "level": "ERROR",
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "/var/log/arete/error.log",
                        "maxBytes": 100 * 1024 * 1024,  # 100MB
                        "backupCount": 5,
                        "formatter": "json",
                    },
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["console", "file", "error_file"],
                },
                "loggers": {
                    "arete": {
                        "level": "INFO",
                        "handlers": ["console", "file"],
                        "propagate": False,
                    },
                    "rag": {
                        "level": "INFO",
                        "handlers": ["console", "file"],
                        "propagate": False,
                    },
                    "reflex": {
                        "level": "WARNING",
                        "handlers": ["console"],
                        "propagate": False,
                    },
                },
            }
        elif self.is_staging:
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "standard": {
                        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "level": "DEBUG",
                        "class": "logging.StreamHandler",
                        "formatter": "standard",
                    },
                },
                "root": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                },
            }
        else:
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "standard": {
                        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "level": "DEBUG",
                        "class": "logging.StreamHandler",
                        "formatter": "standard",
                    },
                },
                "root": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                },
            }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "secret_key": os.getenv("SECRET_KEY", self._generate_secret_key()),
            "jwt_secret": os.getenv("JWT_SECRET", self._generate_secret_key()),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_expiration": int(os.getenv("JWT_EXPIRATION", "3600")),  # 1 hour
            "session_timeout": int(os.getenv("SESSION_TIMEOUT", "86400")),  # 24 hours
            "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            "lockout_duration": int(os.getenv("LOCKOUT_DURATION", "900")),  # 15 minutes
            "password_min_length": int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            "require_https": self.is_production,
            "secure_cookies": self.is_production,
            "csrf_protection": True,
            "content_security_policy": self._get_csp_config(),
        }
    
    def _generate_secret_key(self) -> str:
        """Generate a secret key if not provided."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _get_csp_config(self) -> Dict[str, str]:
        """Get Content Security Policy configuration."""
        if self.is_production:
            return {
                "default-src": "'self'",
                "script-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
                "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src": "'self' https://fonts.gstatic.com",
                "img-src": "'self' data: https:",
                "connect-src": f"'self' {os.getenv('API_URL', '')} wss:",
                "frame-ancestors": "'none'",
                "base-uri": "'self'",
                "form-action": "'self'",
            }
        else:
            return {
                "default-src": "'self'",
                "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src": "'self' 'unsafe-inline'",
                "font-src": "'self' data:",
                "img-src": "'self' data:",
                "connect-src": "'self' ws: wss:",
            }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "enabled": not self.is_development,
            "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
            "health_check_port": int(os.getenv("HEALTH_CHECK_PORT", "8080")),
            "prometheus_enabled": self.is_production,
            "sentry_dsn": os.getenv("SENTRY_DSN"),
            "log_level": "INFO" if self.is_production else "DEBUG",
            "custom_metrics": [
                "http_requests_total",
                "http_request_duration_seconds",
                "rag_query_duration_seconds", 
                "rag_query_success_rate",
                "active_conversations",
                "database_connections",
                "cache_hit_ratio",
            ],
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        # Check required environment variables
        required_vars = {
            Environment.PRODUCTION: [
                "DATABASE_URL", "REDIS_URL", "SECRET_KEY", 
                "NEO4J_URI", "WEAVIATE_URL"
            ],
            Environment.STAGING: [
                "DATABASE_URL", "NEO4J_URI", "WEAVIATE_URL"
            ],
        }
        
        if self.env in required_vars:
            for var in required_vars[self.env]:
                if not os.getenv(var):
                    results["errors"].append(f"Required environment variable {var} not set")
                    results["valid"] = False
        
        # Check database connectivity
        try:
            db_config = self.get_database_config()
            # This would test actual database connectivity in a real implementation
        except Exception as e:
            results["warnings"].append(f"Database configuration issue: {e}")
        
        # Check security settings
        if self.is_production:
            if not os.getenv("SECRET_KEY"):
                results["warnings"].append("Using auto-generated secret key in production")
            
            if not os.getenv("SENTRY_DSN"):
                results["warnings"].append("No error tracking configured for production")
        
        return results


# Global environment configuration instance
env_config = EnvironmentConfig()


def get_config() -> EnvironmentConfig:
    """Get the global environment configuration."""
    return env_config