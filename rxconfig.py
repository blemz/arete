import reflex as rx

config = rx.Config(
    app_name="arete_ui",
    # Tailwind CSS configuration with DaisyUI support
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    # Philosophical color palette
                    "philosophical": {
                        "deep-blue": "#1e3a8a",  # Deep blue for philosophical depth
                        "warm-gold": "#f59e0b",  # Warm gold for classical references  
                        "sage-green": "#10b981", # Sage green for wisdom/nature
                        "classic-grey": "#6b7280", # Classic grey for readability
                    }
                }
            }
        },
        "plugins": ["daisyui"],
        "daisyui": {
            "themes": [
                "corporate",  # Professional academic theme
                "business",   # Alternative professional theme
                {
                    "arete": {  # Custom Arete theme
                        "primary": "#1e3a8a",    # Deep blue
                        "secondary": "#f59e0b",  # Warm gold
                        "accent": "#10b981",     # Sage green
                        "neutral": "#6b7280",    # Classic grey
                        "base-100": "#ffffff",   # White background
                        "info": "#3abff8",
                        "success": "#36d399",
                        "warning": "#fbbd23",
                        "error": "#f87272",
                    }
                }
            ],
            "base": True,
            "styled": True,
            "utils": True,
            "rtl": False,
            "prefix": "",
            "logs": True,
        }
    },
    plugins=[
        rx.plugins.SitemapPlugin(),
    ]
)