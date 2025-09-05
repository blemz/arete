import reflex as rx

# Reflex configuration for Arete Classical Philosophy Chat
config = rx.Config(
    app_name="arete",
    
    # Database configuration (if using Reflex built-in DB)
    db_url="sqlite:///reflex.db",
    
    # Performance settings
    compile_timeout=60,  # Extended timeout for complex components
    
    # Development settings
    debug=True,
    
    # Frontend settings
    frontend_port=3000,
    backend_port=8000,
    
    # API settings
    api_url="http://localhost:8000",
    
    # Deployment settings
    deploy_url=None,
    
    # Styling
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        scaling="100%"
    ),
    
    # Additional static files
    assets_path="assets",
    
    # Performance optimizations
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
                    }
                },
                "fontFamily": {
                    "sans": ["Inter", "system-ui", "sans-serif"],
                    "mono": ["JetBrains Mono", "monospace"]
                },
                "animation": {
                    "fade-in": "fadeIn 0.5s ease-in-out",
                    "slide-up": "slideUp 0.3s ease-out",
                    "pulse-slow": "pulse 3s infinite"
                }
            }
        }
    },
    
    # Environment variables
    env_file=".env",
    
    # CORS settings for API integration
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    
    # Memory settings for large conversations
    max_upload_size="50MB",
    
    # Logging
    loglevel="INFO"
)