"""
Analytics dashboard component for the Arete Reflex application.
"""

import reflex as rx
from ..reflex_app import AreteState


def analytics_card(title: str, value: str, icon: str, description: str = "") -> rx.Component:
    """Analytics metric card component."""
    return rx.div(
        rx.div(
            rx.div(
                rx.text(icon, font_size="2rem", class_name="mb-2"),
                rx.div(
                    rx.text(value, font_size="2rem", font_weight="bold", color="primary"),
                    rx.text(title, font_size="0.875rem", class_name="opacity-70"),
                    class_name="text-left"
                ),
                class_name="flex items-center justify-between"
            ),
            rx.cond(
                description != "",
                rx.text(description, class_name="text-sm opacity-60 mt-2"),
                rx.fragment()
            ),
            class_name="p-6"
        ),
        class_name="card bg-base-100 shadow-lg"
    )


def network_visualization() -> rx.Component:
    """Network visualization placeholder component."""
    return rx.div(
        rx.div(
            rx.heading(
                "Knowledge Graph Network",
                size="md",
                font_weight="semibold", 
                class_name="mb-4"
            ),
            rx.div(
                rx.div(
                    rx.text("🕸️", font_size="4rem", class_name="mb-4"),
                    rx.text(
                        "Interactive Network Visualization",
                        font_weight="semibold",
                        class_name="mb-2"
                    ),
                    rx.text(
                        "Explore relationships between philosophical concepts, "
                        "entities, and texts through an interactive network graph.",
                        class_name="text-sm opacity-70 text-center max-w-md"
                    ),
                    class_name="text-center"
                ),
                class_name="flex items-center justify-center h-96 border border-base-300 rounded-lg bg-base-200"
            ),
            class_name="p-6"
        ),
        class_name="card bg-base-100 shadow-lg"
    )


def concept_analysis() -> rx.Component:
    """Concept analysis component.""" 
    return rx.div(
        rx.div(
            rx.heading(
                "Concept Analysis",
                size="md",
                font_weight="semibold",
                class_name="mb-4"
            ),
            rx.div(
                rx.div(
                    rx.text("🎯", font_weight="semibold", class_name="mb-2"),
                    rx.text("Virtue (ἀρετή)", class_name="font-medium mb-1"),
                    rx.text("Centrality: 0.85", class_name="text-sm opacity-70"),
                    class_name="p-4 bg-base-200 rounded-lg mb-3"
                ),
                rx.div(
                    rx.text("⚖️", font_weight="semibold", class_name="mb-2"),
                    rx.text("Justice (δικαιοσύνη)", class_name="font-medium mb-1"),
                    rx.text("Centrality: 0.78", class_name="text-sm opacity-70"),
                    class_name="p-4 bg-base-200 rounded-lg mb-3"
                ),
                rx.div(
                    rx.text("🧠", font_weight="semibold", class_name="mb-2"),
                    rx.text("Knowledge (ἐπιστήμη)", class_name="font-medium mb-1"),
                    rx.text("Centrality: 0.72", class_name="text-sm opacity-70"),
                    class_name="p-4 bg-base-200 rounded-lg mb-3"
                ),
                class_name="space-y-2"
            ),
            class_name="p-6"
        ),
        class_name="card bg-base-100 shadow-lg"
    )


def historical_timeline() -> rx.Component:
    """Historical development timeline component."""
    return rx.div(
        rx.div(
            rx.heading(
                "Historical Development",
                size="md",
                font_weight="semibold",
                class_name="mb-4"
            ),
            rx.div(
                rx.div(
                    rx.div(
                        rx.text("470 BCE", font_weight="bold", class_name="text-primary mb-1"),
                        rx.text("Birth of Socrates", font_weight="medium", class_name="mb-1"),
                        rx.text("Beginning of systematic philosophical inquiry", class_name="text-sm opacity-70"),
                        class_name="pb-4 border-b border-base-300"
                    ),
                    rx.div(
                        rx.text("428 BCE", font_weight="bold", class_name="text-primary mb-1"),
                        rx.text("Birth of Plato", font_weight="medium", class_name="mb-1"), 
                        rx.text("Development of idealist philosophy", class_name="text-sm opacity-70"),
                        class_name="py-4 border-b border-base-300"
                    ),
                    rx.div(
                        rx.text("384 BCE", font_weight="bold", class_name="text-primary mb-1"),
                        rx.text("Birth of Aristotle", font_weight="medium", class_name="mb-1"),
                        rx.text("Systematic classification of knowledge", class_name="text-sm opacity-70"),
                        class_name="pt-4"
                    ),
                    class_name="space-y-4"
                ),
                class_name="relative"
            ),
            class_name="p-6"
        ),
        class_name="card bg-base-100 shadow-lg"
    )


def analytics_dashboard() -> rx.Component:
    """Complete analytics dashboard component."""
    return rx.div(
        rx.heading(
            "Analytics Dashboard",
            size="xl",
            font_weight="bold",
            class_name="mb-8"
        ),
        
        # Metrics row
        rx.div(
            analytics_card("Documents", "2", "📚", "Classical texts ingested"),
            analytics_card("Entities", "83", "🏷️", "Philosophical concepts tracked"),
            analytics_card("Relationships", "109", "🔗", "Concept connections mapped"),
            analytics_card("Chunks", "227", "📝", "Semantic text segments"),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        ),
        
        # Visualizations row  
        rx.div(
            network_visualization(),
            class_name="mb-8"
        ),
        
        # Analysis row
        rx.div(
            concept_analysis(),
            historical_timeline(),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6"
        ),
        
        class_name="max-w-7xl mx-auto"
    )