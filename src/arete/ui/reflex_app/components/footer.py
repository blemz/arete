"""Comprehensive footer component with project information and academic attribution."""

import reflex as rx
from ..state import NavigationState


def footer_link(text: str, href: str) -> rx.Component:
    """Create a footer link with hover effects."""
    return rx.link(
        text,
        href=href,
        color=rx.color("gray", 11),
        text_decoration="none",
        font_size="sm",
        _hover={
            "color": rx.color("accent", 11),
            "text_decoration": "underline"
        }
    )


def footer_section(title: str, links: list) -> rx.Component:
    """Create a footer section with title and links."""
    return rx.flex(
        rx.text(
            title,
            font_weight="semibold",
            font_size="sm",
            color=rx.color("gray", 12),
            margin_bottom="3"
        ),
        rx.flex(
            *[footer_link(link["text"], link["href"]) for link in links],
            direction="column",
            gap="2"
        ),
        direction="column"
    )


def social_links() -> rx.Component:
    """Social and external links with icons."""
    return rx.flex(
        rx.link(
            rx.icon("github", size=20),
            href="https://github.com/arete-project",
            aria_label="GitHub repository",
            color=rx.color("gray", 11),
            _hover={"color": rx.color("accent", 11)}
        ),
        rx.link(
            rx.icon("twitter", size=20),
            href="https://twitter.com/arete-project", 
            aria_label="Twitter",
            color=rx.color("gray", 11),
            _hover={"color": rx.color("accent", 11)}
        ),
        rx.link(
            rx.icon("mail", size=20),
            href="mailto:contact@arete-project.org",
            aria_label="Email contact",
            color=rx.color("gray", 11),
            _hover={"color": rx.color("accent", 11)}
        ),
        rx.link(
            rx.icon("rss", size=20),
            href="/feed.xml",
            aria_label="RSS feed",
            color=rx.color("gray", 11), 
            _hover={"color": rx.color("accent", 11)}
        ),
        gap="4",
        align_items="center"
    )


def academic_attribution() -> rx.Component:
    """Academic attribution and methodology information."""
    return rx.box(
        rx.flex(
            rx.text(
                "Academic Methodology",
                font_weight="semibold",
                font_size="sm",
                color=rx.color("gray", 12),
                margin_bottom="2"
            ),
            rx.text(
                "Arete employs Graph-RAG (Retrieval-Augmented Generation) with Neo4j knowledge graphs "
                "and Weaviate vector embeddings for accurate, citation-backed philosophical education. "
                "All responses are grounded in primary classical texts with proper academic attribution.",
                font_size="xs",
                color=rx.color("gray", 10),
                line_height="1.5",
                margin_bottom="3"
            ),
            rx.flex(
                rx.text("Powered by:", font_size="xs", color=rx.color("gray", 10)),
                rx.badge("Neo4j", variant="soft", size="1"),
                rx.badge("Weaviate", variant="soft", size="1"), 
                rx.badge("RAG Pipeline", variant="soft", size="1"),
                rx.badge("Classical Texts", variant="soft", size="1"),
                align_items="center",
                gap="2",
                flex_wrap="wrap"
            ),
            direction="column"
        ),
        padding="4",
        background=rx.color("gray", 2),
        border_radius="md",
        margin_bottom="6"
    )


def project_status() -> rx.Component:
    """Current project status and version information."""
    return rx.flex(
        rx.flex(
            rx.icon("graduation-cap", size=16, color=rx.color("accent", 11)),
            rx.text(
                "Arete v7.5 - Production RAG System",
                font_weight="semibold",
                font_size="sm"
            ),
            align_items="center",
            gap="2"
        ),
        rx.flex(
            rx.badge("Production Ready", variant="soft", color_scheme="green"),
            rx.badge("227 Text Chunks", variant="outline", size="1"),
            rx.badge("83 Entities", variant="outline", size="1"),
            rx.badge("GPT-5-mini", variant="outline", size="1"),
            gap="2",
            flex_wrap="wrap"
        ),
        direction="column",
        gap="2",
        align_items="flex-start"
    )


def footer() -> rx.Component:
    """Comprehensive footer with project information, links, and academic attribution."""
    return rx.box(
        rx.box(
            # Academic attribution section
            academic_attribution(),
            
            # Main footer content
            rx.flex(
                # Left section - Project info and status
                rx.flex(
                    project_status(),
                    rx.text(
                        "Graph-RAG AI tutoring system for classical philosophical texts. "
                        "Combining ancient wisdom with modern AI for authentic philosophical education.",
                        font_size="sm",
                        color=rx.color("gray", 10),
                        line_height="1.6",
                        max_width="400px",
                        margin_top="4"
                    ),
                    direction="column",
                    align_items="flex-start",
                    gap="0"
                ),
                
                # Center sections - Navigation links
                rx.flex(
                    footer_section(
                        "Navigation",
                        [
                            {"text": "Home", "href": "/"},
                            {"text": "Chat Interface", "href": "/chat"},
                            {"text": "Document Library", "href": "/library"},
                            {"text": "Knowledge Graph", "href": "/analytics"},
                            {"text": "About Arete", "href": "/about"}
                        ]
                    ),
                    footer_section(
                        "Resources", 
                        [
                            {"text": "User Guide", "href": "/guide"},
                            {"text": "API Documentation", "href": "/docs"},
                            {"text": "Classical Texts", "href": "/texts"},
                            {"text": "Research Papers", "href": "/research"},
                            {"text": "Methodology", "href": "/methodology"}
                        ]
                    ),
                    footer_section(
                        "Community",
                        [
                            {"text": "Discussion Forum", "href": "/forum"},
                            {"text": "Academic Partners", "href": "/partners"},
                            {"text": "Contribute", "href": "/contribute"},
                            {"text": "Support", "href": "/support"},
                            {"text": "Feedback", "href": "/feedback"}
                        ]
                    ),
                    gap="8",
                    flex_wrap="wrap"
                ),
                
                # Right section - Social links and contact
                rx.flex(
                    rx.text(
                        "Connect",
                        font_weight="semibold",
                        font_size="sm",
                        color=rx.color("gray", 12),
                        margin_bottom="3"
                    ),
                    social_links(),
                    rx.text(
                        "Open Source Project",
                        font_size="xs",
                        color=rx.color("gray", 10),
                        margin_top="4"
                    ),
                    rx.text(
                        "MIT License",
                        font_size="xs",
                        color=rx.color("gray", 10)
                    ),
                    direction="column",
                    align_items="flex-start"
                ),
                
                justify_content="space-between",
                align_items="flex-start",
                gap="8",
                flex_wrap="wrap",
                margin_bottom="6"
            ),
            
            # Bottom section - Copyright and legal
            rx.flex(
                rx.flex(
                    rx.text(
                        "© 2025 Arete Project.",
                        font_size="xs",
                        color=rx.color("gray", 10)
                    ),
                    rx.text(
                        "Classical philosophical texts are in the public domain. "
                        "Modern translations and analysis respect original academic attribution.",
                        font_size="xs",
                        color=rx.color("gray", 10)
                    ),
                    gap="4",
                    flex_wrap="wrap"
                ),
                rx.flex(
                    footer_link("Privacy Policy", "/privacy"),
                    footer_link("Terms of Service", "/terms"),
                    footer_link("Academic Use", "/academic"),
                    gap="4",
                    flex_wrap="wrap"
                ),
                justify_content="space-between",
                align_items="center",
                border_top=f"1px solid {rx.color('gray', 6)}",
                padding_top="4",
                flex_wrap="wrap",
                gap="4"
            ),
            
            max_width="1200px",
            margin="0 auto",
            padding="6"
        ),
        background=rx.color("gray", 1),
        border_top=f"1px solid {rx.color('gray', 6)}",
        margin_top="auto"
    )