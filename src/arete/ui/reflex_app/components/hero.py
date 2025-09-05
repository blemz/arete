"""
Hero section component for the Arete home page.
"""

import reflex as rx


def hero_section() -> rx.Component:
    """Hero section with main value proposition."""
    return rx.div(
        rx.div(
            rx.div(
                rx.text(
                    "🏛️",
                    font_size="4rem",
                    class_name="mb-4"
                ),
                rx.heading(
                    "Arete AI Philosophy Tutor",
                    size="3xl",
                    font_weight="bold",
                    color="primary",
                    class_name="mb-4"
                ),
                rx.text(
                    "Explore classical philosophical texts with AI-powered insights. "
                    "Our Graph-RAG system combines knowledge graphs, vector embeddings, "
                    "and advanced reasoning to provide accurate, well-cited philosophical education.",
                    font_size="1.125rem",
                    color="base-content",
                    class_name="mb-8 max-w-3xl mx-auto opacity-80"
                ),
                rx.hstack(
                    rx.link(
                        "Start Learning",
                        href="/chat",
                        class_name="btn btn-primary btn-lg"
                    ),
                    rx.link(
                        "Explore Documents",
                        href="/documents", 
                        class_name="btn btn-outline btn-lg"
                    ),
                    spacing="4",
                    justify="center",
                    class_name="mb-12"
                ),
                class_name="text-center"
            ),
            class_name="hero-content max-w-6xl mx-auto px-4"
        ),
        class_name="hero bg-gradient-to-br from-base-100 to-base-200 min-h-[80vh] flex items-center"
    )