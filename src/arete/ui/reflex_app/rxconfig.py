"""
Reflex configuration for Arete project.
"""

import reflex as rx

config = rx.Config(
    app_name="arete",
    
    # Development settings
    port=3001,
    backend_port=8001,
    
    # Build settings
    env=rx.Env.DEV,
    
    # Disable sitemap plugin to avoid warnings
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"]
)