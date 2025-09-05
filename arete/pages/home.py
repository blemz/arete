"""Home page for Arete application."""

import reflex as rx
from ..components.layout import page_layout, main_content_area, base_layout
from ..state import NavigationState


def hero_section() -> rx.Component:
    """Hero section with project introduction."""
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading(
                    "Arete",
                    font_size="4xl",
                    font_weight="bold",
                    color=rx.color("accent", 11),
                    margin_bottom="4"
                ),
                rx.text(
                    "Graph-RAG AI Tutoring System for Classical Philosophy", 
                    font_size="xl",
                    color=rx.color("gray", 11),
                    margin_bottom="6"
                ),
                rx.text(
                    "Explore ancient wisdom through modern AI. Arete combines Neo4j knowledge graphs, "
                    "Weaviate vector embeddings, and advanced language models to provide accurate, "
                    "citation-backed philosophical education rooted in primary classical texts.",
                    font_size="lg",
                    color=rx.color("gray", 10),
                    line_height="1.6",
                    margin_bottom="8"
                ),
                rx.flex(
                    rx.button(
                        rx.flex(
                            rx.icon("message-circle", size=20),
                            rx.text("Start Conversation"),
                            align_items="center",
                            gap="2"
                        ),
                        size="4",
                        on_click=lambda: [
                            NavigationState.set_current_route("/chat"),
                            NavigationState.set_layout_mode("chat")
                        ]
                    ),
                    rx.button(
                        rx.flex(
                            rx.icon("book-open", size=20),
                            rx.text("Browse Library"),
                            align_items="center",
                            gap="2"
                        ),
                        variant="outline",
                        size="4",
                        on_click=NavigationState.set_current_route("/library")
                    ),
                    gap="4",
                    flex_wrap="wrap"
                ),
                flex="1"
            ),
            rx.box(
                rx.image(
                    src="/philosophy-illustration.svg",
                    alt="Classical philosophy illustration",
                    width="100%",
                    height="400px",
                    object_fit="contain"
                ),
                flex="1",
                display=["none", "none", "block"]
            ),
            gap="8",
            align_items="center"
        ),
        background=rx.color("gray", 1),
        padding="8",
        border_radius="xl",
        margin_bottom="8"
    )


def features_section() -> rx.Component:
    """Key features showcase."""
    features = [
        {
            "icon": "brain",
            "title": "Graph-RAG Technology",
            "description": "Advanced retrieval-augmented generation with Neo4j knowledge graphs for precise philosophical analysis."
        },
        {
            "icon": "search",
            "title": "Vector Semantic Search", 
            "description": "Weaviate-powered semantic search through 227+ curated chunks of classical philosophical texts."
        },
        {
            "icon": "quote",
            "title": "Citation-Backed Responses",
            "description": "Every answer includes proper citations from primary sources with passage previews and context."
        },
        {
            "icon": "network",
            "title": "Entity Relationship Mapping",
            "description": "83+ philosophical entities with 109+ relationships mapped for comprehensive understanding."
        },
        {
            "icon": "zap",
            "title": "Multi-Provider LLM Support",
            "description": "GPT-5-mini, OpenRouter, Gemini, Anthropic, and local Ollama models for diverse AI perspectives."
        },
        {
            "icon": "shield-check",
            "title": "Academic Quality Assurance",
            "description": "Rigorous validation ensuring scholarly accuracy and proper attribution of classical sources."
        }
    ]
    
    return rx.box(
        rx.heading(
            "Powered by Advanced AI & Classical Wisdom",
            font_size="2xl",
            font_weight="semibold",
            text_align="center",
            margin_bottom="8"
        ),
        rx.grid(
            *[
                rx.box(
                    rx.flex(
                        rx.icon(feature["icon"], size=32, color=rx.color("accent", 11)),
                        rx.heading(feature["title"], font_size="lg", font_weight="semibold"),
                        rx.text(
                            feature["description"],
                            color=rx.color("gray", 10),
                            line_height="1.5"
                        ),
                        direction="column",
                        gap="3",
                        align_items="flex-start"
                    ),
                    padding="6",
                    background=rx.color("gray", 1),
                    border_radius="lg",
                    border=f"1px solid {rx.color('gray', 6)}",
                    _hover={"border_color": rx.color("accent", 7)}
                )
                for feature in features
            ],
            template_columns=["1fr", "1fr", "repeat(2, 1fr)", "repeat(3, 1fr)"],
            gap="6",
            margin_bottom="8"
        )
    )


def stats_section() -> rx.Component:
    """Current system statistics."""
    return rx.box(
        rx.flex(
            rx.flex(
                rx.text("227", font_size="3xl", font_weight="bold", color=rx.color("accent", 11)),
                rx.text("Text Chunks", font_size="sm", color=rx.color("gray", 10)),
                direction="column",
                align_items="center"
            ),
            rx.flex(
                rx.text("83", font_size="3xl", font_weight="bold", color=rx.color("accent", 11)),
                rx.text("Entities", font_size="sm", color=rx.color("gray", 10)),
                direction="column", 
                align_items="center"
            ),
            rx.flex(
                rx.text("109", font_size="3xl", font_weight="bold", color=rx.color("accent", 11)),
                rx.text("Relationships", font_size="sm", color=rx.color("gray", 10)),
                direction="column",
                align_items="center"
            ),
            rx.flex(
                rx.text("51K", font_size="3xl", font_weight="bold", color=rx.color("accent", 11)),
                rx.text("Words Processed", font_size="sm", color=rx.color("gray", 10)),
                direction="column",
                align_items="center"
            ),
            justify_content="center",
            gap="8",
            flex_wrap="wrap"
        ),
        background=rx.color("accent", 2),
        border=f"1px solid {rx.color('accent', 6)}",
        border_radius="lg",
        padding="6",
        margin_bottom="8"
    )


def quick_start_section() -> rx.Component:
    """Quick start guide."""
    return rx.box(
        rx.heading(
            "Get Started",
            font_size="2xl", 
            font_weight="semibold",
            margin_bottom="6"
        ),
        rx.flex(
            rx.box(
                rx.flex(
                    rx.box(
                        rx.text("1", font_size="xl", font_weight="bold", 
                               color=rx.color("accent", 11)),
                        width="32px",
                        height="32px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        background=rx.color("accent", 3),
                        border_radius="full"
                    ),
                    rx.box(
                        rx.text("Ask a Question", font_weight="semibold", margin_bottom="2"),
                        rx.text("Start with fundamental concepts like 'What is virtue?' or 'Explain Socratic method'"),
                        flex="1"
                    ),
                    gap="4",
                    align_items="flex-start"
                ),
                padding="4",
                border_left=f"3px solid {rx.color('accent', 6)}",
                margin_bottom="4"
            ),
            rx.box(
                rx.flex(
                    rx.box(
                        rx.text("2", font_size="xl", font_weight="bold",
                               color=rx.color("accent", 11)), 
                        width="32px",
                        height="32px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        background=rx.color("accent", 3),
                        border_radius="full"
                    ),
                    rx.box(
                        rx.text("Explore Citations", font_weight="semibold", margin_bottom="2"),
                        rx.text("Click on source citations to read original passages and build deeper understanding"),
                        flex="1"
                    ),
                    gap="4",
                    align_items="flex-start"
                ),
                padding="4",
                border_left=f"3px solid {rx.color('accent', 6)}",
                margin_bottom="4"
            ),
            rx.box(
                rx.flex(
                    rx.box(
                        rx.text("3", font_size="xl", font_weight="bold",
                               color=rx.color("accent", 11)),
                        width="32px", 
                        height="32px",
                        display="flex",
                        align_items="center",
                        justify_content="center", 
                        background=rx.color("accent", 3),
                        border_radius="full"
                    ),
                    rx.box(
                        rx.text("Discover Connections", font_weight="semibold", margin_bottom="2"),
                        rx.text("Use analytics to visualize relationships between philosophers, concepts, and texts"),
                        flex="1"
                    ),
                    gap="4",
                    align_items="flex-start"
                ),
                padding="4",
                border_left=f"3px solid {rx.color('accent', 6)}"
            ),
            direction="column"
        )
    )


def home_page() -> rx.Component:
    """Home page with hero, features, and quick start."""
    return base_layout(
        rx.box(
            hero_section(),
            stats_section(),
            features_section(), 
            quick_start_section(),
            padding="6",
            max_width="1200px",
            margin="0 auto"
        )
    )