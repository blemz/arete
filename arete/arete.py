"""Main Arete Reflex application."""

import reflex as rx
from .pages.home import home_page
from .pages.chat import chat_page
from .components.layout import base_layout, main_content_area
from .state import NavigationState


# Global styles for accessibility and theming
style = {
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "line_height": "1.6",
    "color": "var(--color-foreground)",
    "background": "var(--color-background)",
    
    # Focus styles for accessibility
    "*:focus": {
        "outline": f"2px solid {rx.color('accent', 8)}",
        "outline_offset": "2px",
    },
    
    # High contrast mode support
    "@media (prefers-contrast: high)": {
        "*": {
            "border_color": rx.color("gray", 12),
        }
    },
    
    # Reduced motion support
    "@media (prefers-reduced-motion: reduce)": {
        "*": {
            "animation_duration": "0.01ms !important",
            "animation_iteration_count": "1 !important",
            "transition_duration": "0.01ms !important",
        }
    }
}


def library_page() -> rx.Component:
    """Library page placeholder."""
    return base_layout(
        rx.box(
            rx.heading("Document Library", font_size="2xl", margin_bottom="6"),
            rx.text("Browse and search classical philosophical texts.", margin_bottom="4"),
            rx.text("Coming soon: Interactive document viewer with highlighting and annotations."),
            padding="6"
        )
    )


def analytics_page() -> rx.Component:
    """Analytics page placeholder.""" 
    return base_layout(
        rx.box(
            rx.heading("Knowledge Graph Analytics", font_size="2xl", margin_bottom="6"),
            rx.text("Visualize relationships between philosophers, concepts, and texts.", margin_bottom="4"),
            rx.text("Coming soon: Interactive network graphs and centrality analysis."),
            padding="6"
        )
    )


def about_page() -> rx.Component:
    """About page placeholder."""
    return base_layout(
        rx.box(
            rx.heading("About Arete", font_size="2xl", margin_bottom="6"),
            rx.text(
                "Arete is a Graph-RAG AI tutoring system that combines ancient philosophical wisdom "
                "with modern artificial intelligence to provide accurate, citation-backed education "
                "in classical philosophy.",
                margin_bottom="4",
                line_height="1.8"
            ),
            rx.text(
                "Built with Neo4j knowledge graphs, Weaviate vector embeddings, and multi-provider "
                "LLM support for comprehensive philosophical analysis.",
                line_height="1.8"
            ),
            padding="6"
        )
    )


# Main app with routing
app = rx.App(
    style=style,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ]
)

# Add routes
app.add_page(home_page, route="/", title="Arete - AI Philosophy Tutor")
app.add_page(chat_page, route="/chat", title="Chat - Arete") 
app.add_page(library_page, route="/library", title="Library - Arete")
app.add_page(analytics_page, route="/analytics", title="Analytics - Arete")
app.add_page(about_page, route="/about", title="About - Arete")

# Compile the app
app.compile()