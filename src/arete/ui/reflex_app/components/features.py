"""
Features section component for the Arete home page.
"""

import reflex as rx


def feature_card(icon: str, title: str, description: str) -> rx.Component:
    """Individual feature card component."""
    return rx.div(
        rx.div(
            rx.text(
                icon,
                font_size="3rem",
                class_name="mb-4"
            ),
            rx.heading(
                title,
                size="lg", 
                font_weight="semibold",
                color="primary",
                class_name="mb-3"
            ),
            rx.text(
                description,
                color="base-content",
                class_name="opacity-70 leading-relaxed"
            ),
            class_name="text-center"
        ),
        class_name="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow duration-300 p-8"
    )


def features_section() -> rx.Component:
    """Features section highlighting key capabilities."""
    return rx.div(
        rx.div(
            rx.heading(
                "Powered by Advanced AI Technology",
                size="2xl",
                font_weight="bold",
                color="base-content",
                class_name="text-center mb-4"
            ),
            rx.text(
                "Arete combines cutting-edge AI technologies to deliver accurate, "
                "contextual, and well-cited philosophical education.",
                font_size="1.125rem",
                color="base-content", 
                class_name="text-center mb-12 opacity-70 max-w-3xl mx-auto"
            ),
            rx.div(
                feature_card(
                    "🧠",
                    "Graph-RAG Technology",
                    "Advanced retrieval system combining Neo4j knowledge graphs "
                    "with Weaviate vector embeddings for precise, contextual responses."
                ),
                feature_card(
                    "📚", 
                    "Classical Text Corpus",
                    "Comprehensive collection of Plato's dialogues and Aristotle's works, "
                    "professionally processed and semantically indexed."
                ),
                feature_card(
                    "🎯",
                    "Accurate Citations",
                    "Every response includes precise citations with passage previews, "
                    "ensuring academic integrity and source verification."
                ),
                feature_card(
                    "🔍",
                    "Interactive Analytics",
                    "Explore philosophical concepts through network visualizations, "
                    "centrality analysis, and historical development tracking."
                ),
                feature_card(
                    "🚀",
                    "Multi-LLM Support",
                    "Compatible with OpenAI GPT models (including GPT-5-mini), "
                    "Anthropic Claude, Google Gemini, and local Ollama models."
                ),
                feature_card(
                    "⚡",
                    "Real-time Processing",
                    "Fast response times with intelligent caching and optimized "
                    "query processing for smooth learning experience."
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            ),
            class_name="max-w-7xl mx-auto px-4"
        ),
        class_name="py-20 bg-base-100"
    )