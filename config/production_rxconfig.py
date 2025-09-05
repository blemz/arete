"""Production configuration for Reflex Arete application."""

import os
import reflex as rx
from typing import List, Dict, Any


def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment."""
    if os.getenv("ENVIRONMENT") == "production":
        return [
            "https://arete.philosophy.edu",
            "https://www.arete.philosophy.edu",
            # Add your production domains here
        ]
    elif os.getenv("ENVIRONMENT") == "staging":
        return [
            "https://staging.arete.philosophy.edu",
            "https://preview.arete.philosophy.edu",
        ]
    else:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000"
        ]


def get_database_url() -> str:
    """Get database URL based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return os.getenv("PRODUCTION_DB_URL", "postgresql://user:pass@localhost:5432/arete_prod")
    elif env == "staging":
        return os.getenv("STAGING_DB_URL", "postgresql://user:pass@localhost:5432/arete_staging")
    else:
        return os.getenv("DEV_DB_URL", "sqlite:///reflex_dev.db")


def get_api_url() -> str:
    """Get API URL based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return os.getenv("PRODUCTION_API_URL", "https://api.arete.philosophy.edu")
    elif env == "staging":
        return os.getenv("STAGING_API_URL", "https://api-staging.arete.philosophy.edu")
    else:
        return os.getenv("DEV_API_URL", "http://localhost:8000")


def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "compile_timeout": 180,  # 3 minutes for production builds
            "max_upload_size": "100MB",  # Larger for production
            "enable_compression": True,
            "enable_caching": True,
            "cache_max_age": 3600,  # 1 hour
            "minify_js": True,
            "minify_css": True,
            "optimize_images": True,
        }
    elif env == "staging":
        return {
            "compile_timeout": 120,  # 2 minutes for staging
            "max_upload_size": "75MB",
            "enable_compression": True,
            "enable_caching": False,  # Disable for testing
            "minify_js": True,
            "minify_css": True,
        }
    else:
        return {
            "compile_timeout": 60,  # 1 minute for development
            "max_upload_size": "50MB",
            "enable_compression": False,
            "enable_caching": False,
            "minify_js": False,
            "minify_css": False,
        }


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "loglevel": "WARNING",
            "log_file": "/var/log/arete/app.log",
            "log_rotation": True,
            "log_max_size": "100MB",
            "log_backup_count": 5,
            "structured_logging": True,
        }
    elif env == "staging":
        return {
            "loglevel": "INFO",
            "log_file": "/var/log/arete/staging.log",
            "structured_logging": True,
        }
    else:
        return {
            "loglevel": "DEBUG",
            "console_logging": True,
        }


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return {
        "secure_cookies": os.getenv("ENVIRONMENT") == "production",
        "session_timeout": int(os.getenv("SESSION_TIMEOUT", "3600")),  # 1 hour default
        "csrf_protection": True,
        "content_security_policy": {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https:",
            "connect-src": "'self' " + get_api_url(),
        },
        "force_https": os.getenv("ENVIRONMENT") == "production",
    }


# Production Reflex Configuration
config = rx.Config(
    app_name="arete",
    
    # Database configuration
    db_url=get_database_url(),
    
    # Performance settings
    **get_performance_config(),
    
    # Development/Production mode
    debug=os.getenv("ENVIRONMENT") != "production",
    
    # Frontend settings
    frontend_port=int(os.getenv("FRONTEND_PORT", "3000")),
    backend_port=int(os.getenv("BACKEND_PORT", "8000")),
    
    # API settings
    api_url=get_api_url(),
    
    # Deployment settings
    deploy_url=os.getenv("DEPLOY_URL"),
    
    # Theme configuration
    theme=rx.theme(
        appearance=os.getenv("DEFAULT_THEME", "light"),
        has_background=True,
        radius="medium",
        scaling="100%",
        accent_color=os.getenv("ACCENT_COLOR", "blue"),
    ),
    
    # Static assets
    assets_path="assets",
    
    # Enhanced Tailwind configuration for production
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    "arete": {
                        "50": "#eff6ff",
                        "100": "#dbeafe",
                        "200": "#bfdbfe", 
                        "300": "#93c5fd",
                        "400": "#60a5fa",
                        "500": "#3b82f6",
                        "600": "#2563eb",
                        "700": "#1d4ed8",
                        "800": "#1e40af",
                        "900": "#1e3a8a"
                    },
                    "primary": {
                        "50": os.getenv("PRIMARY_50", "#eff6ff"),
                        "500": os.getenv("PRIMARY_500", "#3b82f6"),
                        "900": os.getenv("PRIMARY_900", "#1e3a8a"),
                    }
                },
                "fontFamily": {
                    "sans": [
                        "Inter",
                        "-apple-system", 
                        "BlinkMacSystemFont",
                        '"Segoe UI"',
                        "Roboto",
                        "sans-serif"
                    ],
                    "mono": [
                        '"JetBrains Mono"',
                        '"Fira Code"',
                        '"Consolas"',
                        "monospace"
                    ],
                    "serif": [
                        '"Crimson Text"',
                        '"Times New Roman"',
                        "serif"
                    ]
                },
                "animation": {
                    "fade-in": "fadeIn 0.5s ease-in-out",
                    "slide-up": "slideUp 0.3s ease-out",
                    "slide-down": "slideDown 0.3s ease-out",
                    "pulse-slow": "pulse 3s infinite",
                    "bounce-subtle": "bounceSubtle 2s infinite",
                },
                "screens": {
                    "xs": "375px",
                    "sm": "640px",
                    "md": "768px", 
                    "lg": "1024px",
                    "xl": "1280px",
                    "2xl": "1536px",
                },
                "spacing": {
                    "18": "4.5rem",
                    "88": "22rem",
                    "128": "32rem",
                },
                "maxWidth": {
                    "8xl": "88rem",
                    "9xl": "96rem",
                },
            }
        },
        "plugins": [
            "@tailwindcss/forms",
            "@tailwindcss/typography", 
            "@tailwindcss/aspect-ratio",
        ] if os.getenv("ENVIRONMENT") == "production" else [],
    },
    
    # Environment variables
    env_file=".env",
    
    # CORS settings
    cors_allowed_origins=get_cors_origins(),
    
    # Security settings
    **get_security_config(),
    
    # Logging
    **get_logging_config(),
    
    # Production optimizations
    bun_path=os.getenv("BUN_PATH", "/usr/local/bin/bun") if os.getenv("ENVIRONMENT") == "production" else None,
    node_path=os.getenv("NODE_PATH", "/usr/local/bin/node") if os.getenv("ENVIRONMENT") == "production" else None,
    
    # Memory and resource limits
    memory_limit=os.getenv("MEMORY_LIMIT", "1GB"),
    
    # Custom webpack configuration for production
    webpack_config={
        "optimization": {
            "minimize": os.getenv("ENVIRONMENT") == "production",
            "splitChunks": {
                "chunks": "all",
                "cacheGroups": {
                    "vendor": {
                        "test": "/node_modules/",
                        "name": "vendors",
                        "chunks": "all",
                    },
                    "common": {
                        "name": "common",
                        "minChunks": 2,
                        "chunks": "all",
                    }
                }
            }
        },
        "resolve": {
            "alias": {
                "@components": "./components",
                "@assets": "./assets",
                "@utils": "./utils",
            }
        }
    } if os.getenv("ENVIRONMENT") == "production" else {},
    
    # Health check configuration
    health_check={
        "enabled": True,
        "endpoint": "/health",
        "checks": [
            "database_connectivity",
            "rag_service_status", 
            "memory_usage",
            "disk_space",
        ]
    },
    
    # Monitoring and metrics
    monitoring={
        "enabled": os.getenv("ENVIRONMENT") == "production",
        "metrics_endpoint": "/metrics",
        "prometheus_integration": True,
        "custom_metrics": [
            "chat_response_time",
            "rag_query_latency",
            "document_load_time",
            "citation_accuracy",
        ]
    },
    
    # Rate limiting
    rate_limiting={
        "enabled": True,
        "requests_per_minute": int(os.getenv("RATE_LIMIT", "60")),
        "burst_limit": int(os.getenv("BURST_LIMIT", "100")),
    },
    
    # Caching configuration
    caching={
        "enabled": get_performance_config()["enable_caching"],
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "default_timeout": 3600,  # 1 hour
        "rag_cache_timeout": 7200,  # 2 hours for RAG responses
    },
)


# Environment-specific configurations
if os.getenv("ENVIRONMENT") == "production":
    # Additional production-only settings
    config.timeout = 30
    config.keep_alive = True
    config.worker_processes = int(os.getenv("WORKER_PROCESSES", "4"))
    config.max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
    config.preload_app = True

elif os.getenv("ENVIRONMENT") == "staging":
    # Staging-specific settings
    config.timeout = 60
    config.worker_processes = 2

else:
    # Development settings
    config.hot_reload = True
    config.auto_restart = True