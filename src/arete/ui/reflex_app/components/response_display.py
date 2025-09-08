"""
Response Display Components

Beautiful, structured display components for philosophical responses
from the enhanced prompt system.
"""

import reflex as rx
from typing import List, Dict
from response_parser import ParsedResponse, ResponseParser

def direct_answer_card(content: str) -> rx.Component:
    """Display the direct answer section."""
    if not content:
        return rx.fragment()
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("💡", font_size="xl", opacity="0.8"),
                rx.heading("Direct Answer", size="5", color="blue.700", font_weight="600"),
                spacing="3",
                align="center"
            ),
            rx.text(
                content,
                font_size="lg",
                line_height="1.7",
                color="gray.800",
                font_weight="400",
                letter_spacing="0.01em"
            ),
            spacing="4",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(239, 246, 255, 0.8), rgba(219, 234, 254, 0.6))",
        border_left="5px solid",
        border_color="blue.500",
        p="6",
        border_radius="lg",
        box_shadow="0 2px 8px rgba(59, 130, 246, 0.1)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 4px 12px rgba(59, 130, 246, 0.15)"}
    )

def detailed_explanation_card(content: str) -> rx.Component:
    """Display the detailed explanation section."""
    if not content:
        return rx.fragment()
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📚", font_size="xl", opacity="0.8"),
                rx.heading("Detailed Explanation", size="5", color="green.700", font_weight="600"),
                spacing="3",
                align="center"
            ),
            rx.text(
                content,
                font_size="md",
                line_height="1.8",
                color="gray.800",
                white_space="pre-wrap",
                font_weight="400",
                letter_spacing="0.01em"
            ),
            spacing="4",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(240, 253, 244, 0.8), rgba(220, 252, 231, 0.6))",
        border_left="5px solid",
        border_color="green.500",
        p="6",
        border_radius="lg",
        box_shadow="0 2px 8px rgba(34, 197, 94, 0.1)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 4px 12px rgba(34, 197, 94, 0.15)"}
    )

def broader_connections_card(content: str) -> rx.Component:
    """Display the broader connections section."""
    if not content:
        return rx.fragment()
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🌐", font_size="xl", opacity="0.8"),
                rx.heading("Broader Connections", size="5", color="purple.700", font_weight="600"),
                spacing="3",
                align="center"
            ),
            rx.text(
                content,
                font_size="md",
                line_height="1.7",
                color="gray.800",
                white_space="pre-wrap",
                font_weight="400",
                letter_spacing="0.01em"
            ),
            spacing="4",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(250, 245, 255, 0.8), rgba(233, 213, 255, 0.6))",
        border_left="5px solid",
        border_color="purple.500",
        p="6",
        border_radius="lg",
        box_shadow="0 2px 8px rgba(147, 51, 234, 0.1)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 4px 12px rgba(147, 51, 234, 0.15)"}
    )

def references_card(content: str) -> rx.Component:
    """Display the references section with citations."""
    if not content:
        return rx.fragment()
    
    # Parse citations
    citations = ResponseParser.extract_citations(content)
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📖", font_size="xl", opacity="0.8"),
                rx.heading("References", size="5", color="orange.700", font_weight="600"),
                spacing="3",
                align="center"
            ),
            rx.cond(
                len(citations) > 0,
                rx.vstack(
                    *[citation_item(citation) for citation in citations],
                    spacing="3",
                    width="100%"
                ),
                rx.text(
                    content,
                    font_size="sm",
                    line_height="1.6",
                    color="gray.700",
                    white_space="pre-wrap",
                    font_weight="400",
                    letter_spacing="0.01em"
                )
            ),
            spacing="4",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(255, 251, 235, 0.8), rgba(254, 243, 199, 0.6))",
        border_left="5px solid",
        border_color="orange.500",
        p="6",
        border_radius="lg",
        box_shadow="0 2px 8px rgba(249, 115, 22, 0.1)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 4px 12px rgba(249, 115, 22, 0.15)"}
    )

def citation_item(citation: Dict[str, str]) -> rx.Component:
    """Display a single citation."""
    return rx.box(
        rx.vstack(
            rx.text(
                citation.get('source', 'Citation'),
                font_size="sm",
                font_weight="600",
                color="orange.800",
                letter_spacing="0.01em"
            ),
            rx.text(
                citation.get('text', ''),
                font_size="sm",
                line_height="1.6",
                color="gray.700",
                font_style="italic",
                font_weight="400"
            ),
            spacing="2",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(254, 249, 195, 0.3))",
        p="4",
        border_radius="md",
        border="1px solid",
        border_color="orange.300",
        box_shadow="0 1px 3px rgba(249, 115, 22, 0.08)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 2px 6px rgba(249, 115, 22, 0.12)", "border_color": "orange.400"}
    )

def formatted_response(response_text: str) -> rx.Component:
    """Main component to display a formatted philosophical response."""
    
    # For now, let's simplify and just show the response as a styled box
    # We'll enhance this with XML parsing later once the basic structure works
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🏛️", font_size="xl", opacity="0.8"),
                rx.heading("Arete Response", size="5", color="gray.700", font_weight="600"),
                spacing="3",
                align="center"
            ),
            rx.text(
                response_text,
                font_size="md",
                line_height="1.7",
                color="gray.800",
                white_space="pre-wrap",
                font_weight="400",
                letter_spacing="0.01em"
            ),
            spacing="4",
            align="start"
        ),
        bg="linear-gradient(135deg, rgba(249, 250, 251, 0.8), rgba(243, 244, 246, 0.6))",
        border="1px solid",
        border_color="gray.300",
        p="6",
        border_radius="lg",
        box_shadow="0 2px 8px rgba(107, 114, 128, 0.08)",
        width="100%",
        transition="all 0.2s ease",
        _hover={"box_shadow": "0 4px 12px rgba(107, 114, 128, 0.12)"}
    )

def simple_message(message: str, is_user: bool = False) -> rx.Component:
    """Simple message component for user messages and fallbacks."""
    
    return rx.cond(
        is_user,
        # User message
        rx.box(
            rx.hstack(
                rx.text("👤", font_size="lg", opacity="0.7"),
                rx.text(
                    message,
                    font_size="md",
                    line_height="1.6",
                    color="blue.900",
                    font_weight="400",
                    letter_spacing="0.01em"
                ),
                spacing="3",
                align="start",
                width="100%"
            ),
            bg="linear-gradient(135deg, rgba(239, 246, 255, 0.7), rgba(219, 234, 254, 0.5))",
            border="1px solid",
            border_color="blue.200",
            p="4",
            border_radius="lg",
            box_shadow="0 1px 3px rgba(59, 130, 246, 0.08)",
            width="100%",
            transition="all 0.2s ease",
            _hover={"box_shadow": "0 2px 6px rgba(59, 130, 246, 0.12)"}
        ),
        # Assistant fallback message
        rx.box(
            rx.text(
                message,
                font_size="md",
                line_height="1.6",
                color="gray.800",
                font_weight="400",
                letter_spacing="0.01em"
            ),
            bg="linear-gradient(135deg, rgba(249, 250, 251, 0.8), rgba(243, 244, 246, 0.6))",
            border="1px solid",
            border_color="gray.200",
            p="4",
            border_radius="lg",
            box_shadow="0 1px 3px rgba(107, 114, 128, 0.08)",
            width="100%",
            transition="all 0.2s ease",
            _hover={"box_shadow": "0 2px 6px rgba(107, 114, 128, 0.12)"}
        )
    )