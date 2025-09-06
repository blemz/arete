"""
Reflex configuration for Arete project.
"""

import reflex as rx

config = rx.Config(
    app_name="arete",
    
    # Development settings
    port=3000,
    backend_port=8000,
    
    # Frontend configuration
    frontend_packages=[
        "daisyui@^4.12.14",
        "@tailwindcss/typography@^0.5.15",
        "@tailwindcss/forms@^0.5.9"
    ],
    
    # Tailwind configuration
    tailwind={
        "theme": {
            "extend": {
                "fontFamily": {
                    "sans": ["Inter", "ui-sans-serif", "system-ui"]
                },
                "colors": {
                    "arete": {
                        "primary": "#1e40af",
                        "secondary": "#7c3aed", 
                        "accent": "#059669",
                        "neutral": "#374151",
                        "base": "#f9fafb",
                        "info": "#0ea5e9",
                        "success": "#10b981",
                        "warning": "#f59e0b",
                        "error": "#ef4444"
                    }
                }
            }
        },
        "plugins": ["@tailwindcss/typography", "@tailwindcss/forms", "daisyui"],
        "daisyui": {
            "themes": [
                {
                    "arete": {
                        "primary": "#1e40af",
                        "primary-focus": "#1d4ed8", 
                        "primary-content": "#ffffff",
                        "secondary": "#7c3aed",
                        "secondary-focus": "#8b5cf6",
                        "secondary-content": "#ffffff",
                        "accent": "#059669",
                        "accent-focus": "#047857",
                        "accent-content": "#ffffff",
                        "neutral": "#374151",
                        "neutral-focus": "#1f2937",
                        "neutral-content": "#f3f4f6",
                        "base-100": "#ffffff",
                        "base-200": "#f9fafb",
                        "base-300": "#f3f4f6",
                        "base-content": "#1f2937",
                        "info": "#0ea5e9",
                        "success": "#10b981",
                        "warning": "#f59e0b",
                        "error": "#ef4444"
                    }
                },
                "light",
                "dark",
                "cupcake",
                "corporate"
            ],
            "darkTheme": "dark",
            "base": True,
            "styled": True,
            "utils": True,
            "rtl": False,
            "prefix": "",
            "logs": True
        }
    },
    
    # Build settings
    db_url="sqlite:///arete_reflex.db",
    env=rx.Env.DEV,
    
    # CORS settings for API integration
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ],
    
    # Static files
    assets_path="assets",
    
    # API settings for RAG integration
    api_url="http://localhost:8000",
    
    # Performance settings
    timeout=120,
    
    # Security settings
    secret_key="arete-graph-rag-philosophical-ai-tutor-2024",
    
    # Disable sitemap plugin to avoid warnings
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"]
)