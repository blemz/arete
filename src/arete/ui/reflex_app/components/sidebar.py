"""Enhanced sidebar component with collapsible functionality and quick access."""

import reflex as rx
from typing import List, Dict
from ..state import NavigationState, ChatState, DocumentState


def recent_item(title: str, subtitle: str = None, icon: str = "file-text", on_click=None) -> rx.Component:
    """Create a recent item component for sidebar."""
    return rx.button(
        rx.flex(
            rx.icon(icon, size=16, color=rx.color("gray", 10)),
            rx.box(
                rx.text(
                    title,
                    font_size="sm", 
                    font_weight="medium",
                    line_height="1.2",
                    text_overflow="ellipsis",
                    overflow="hidden",
                    white_space="nowrap"
                ),
                rx.cond(
                    subtitle,
                    rx.text(
                        subtitle,
                        font_size="xs",
                        color=rx.color("gray", 10),
                        text_overflow="ellipsis",
                        overflow="hidden",
                        white_space="nowrap"
                    ),
                    rx.fragment()
                ),
                flex="1",
                min_width="0"
            ),
            align_items="flex-start",
            gap="3",
            width="100%"
        ),
        variant="ghost",
        justify="start",
        width="100%",
        padding="3",
        height="auto",
        on_click=on_click,
        _hover={"background": rx.color("gray", 3)}
    )


def sidebar_section(title: str, children: List[rx.Component], collapsible: bool = True) -> rx.Component:
    """Create a collapsible sidebar section."""
    return rx.box(
        rx.flex(
            rx.text(
                title,
                font_size="sm",
                font_weight="semibold",
                color=rx.color("gray", 11)
            ),
            rx.cond(
                collapsible & ~NavigationState.is_sidebar_collapsed,
                rx.icon("chevron-down", size=16, color=rx.color("gray", 10)),
                rx.cond(
                    collapsible,
                    rx.icon("chevron-right", size=16, color=rx.color("gray", 10)),
                    rx.fragment()
                )
            ),
            justify_content="space-between",
            align_items="center",
            padding="2",
            margin_bottom="1"
        ),
        rx.cond(
            NavigationState.is_sidebar_collapsed,
            rx.fragment(),
            rx.flex(
                *children,
                direction="column",
                gap="1"
            )
        ),
        margin_bottom="4"
    )


def quick_actions() -> rx.Component:
    """Quick action buttons for common tasks."""
    return sidebar_section(
        "Quick Actions",
        [
            rx.button(
                rx.flex(
                    rx.icon("plus", size=16),
                    rx.text("New Chat"),
                    align_items="center",
                    gap="2"
                ),
                variant="soft",
                size="2",
                width="100%"
            ),
            rx.button(
                rx.flex(
                    rx.icon("search", size=16),
                    rx.text("Search Library"),
                    align_items="center",
                    gap="2"
                ),
                variant="ghost",
                size="2",
                width="100%"
            ),
            rx.button(
                rx.flex(
                    rx.icon("bookmark", size=16),
                    rx.text("Saved Passages"),
                    align_items="center",
                    gap="2"
                ),
                variant="ghost",
                size="2",
                width="100%"
            ),
        ],
        collapsible=False
    )


def recent_conversations() -> rx.Component:
    """Display recent conversations with truncated titles."""
    return sidebar_section(
        "Recent Conversations",
        [
            rx.foreach(
                NavigationState.recent_conversations,
                lambda conv: recent_item(
                    conv["title"],
                    conv["date"],
                    "message-circle",
                    # on_click would navigate to conversation
                )
            )
        ]
    )


def recent_documents() -> rx.Component:
    """Display recent documents with type indicators."""
    return sidebar_section(
        "Recent Documents", 
        [
            rx.foreach(
                NavigationState.recent_documents,
                lambda doc: recent_item(
                    doc["title"],
                    doc["type"].title(),
                    rx.cond(
                        doc["type"] == "dialogue",
                        "users",
                        "scroll"
                    ),
                    # on_click would load document
                )
            )
        ]
    )


def philosophical_tools() -> rx.Component:
    """Quick access to philosophical analysis tools."""
    return sidebar_section(
        "Analysis Tools",
        [
            recent_item(
                "Argument Mapper",
                "Visualize logical structures", 
                "git-branch"
            ),
            recent_item(
                "Concept Explorer",
                "Browse philosophical concepts",
                "compass"
            ),
            recent_item(
                "Citation Builder", 
                "Generate proper citations",
                "quote"
            ),
            recent_item(
                "Timeline View",
                "Historical context",
                "calendar"
            ),
        ]
    )


def sidebar_footer() -> rx.Component:
    """Footer section of sidebar with help and feedback."""
    return rx.flex(
        rx.separator(margin="2"),
        rx.flex(
            rx.button(
                rx.flex(
                    rx.icon("help-circle", size=16),
                    rx.text("Help & Guide"),
                    align_items="center",
                    gap="2"
                ),
                variant="ghost",
                size="2",
                width="100%"
            ),
            rx.button(
                rx.flex(
                    rx.icon("message-square", size=16),
                    rx.text("Feedback"),
                    align_items="center",
                    gap="2"
                ),
                variant="ghost", 
                size="2",
                width="100%"
            ),
            direction="column",
            gap="1"
        ),
        direction="column",
        margin_top="auto"
    )


def sidebar() -> rx.Component:
    """Main collapsible sidebar with recent items and quick access."""
    return rx.box(
        # Collapse/expand button
        rx.button(
            rx.icon(
                rx.cond(
                    NavigationState.is_sidebar_collapsed,
                    "chevron-right",
                    "chevron-left"
                ),
                size=16
            ),
            variant="ghost",
            size="1",
            position="absolute",
            right="-10px",
            top="20px",
            z_index="10",
            border_radius="full",
            background=rx.color("gray", 2),
            border=f"1px solid {rx.color('gray', 6)}",
            on_click=NavigationState.toggle_sidebar,
            aria_label="Toggle sidebar"
        ),
        
        # Sidebar content
        rx.flex(
            rx.cond(
                NavigationState.is_sidebar_collapsed,
                # Collapsed sidebar - icons only
                rx.flex(
                    rx.button(
                        rx.icon("plus", size=20),
                        variant="ghost",
                        size="3",
                        aria_label="New chat"
                    ),
                    rx.button(
                        rx.icon("search", size=20),
                        variant="ghost", 
                        size="3",
                        aria_label="Search"
                    ),
                    rx.button(
                        rx.icon("bookmark", size=20),
                        variant="ghost",
                        size="3", 
                        aria_label="Bookmarks"
                    ),
                    rx.button(
                        rx.icon("help-circle", size=20),
                        variant="ghost",
                        size="3",
                        aria_label="Help"
                    ),
                    direction="column",
                    gap="2",
                    padding="3"
                ),
                # Expanded sidebar - full content
                rx.flex(
                    quick_actions(),
                    recent_conversations(),
                    recent_documents(),
                    philosophical_tools(),
                    sidebar_footer(),
                    direction="column",
                    gap="0",
                    padding="3",
                    height="100%",
                    overflow_y="auto"
                )
            ),
            direction="column",
            height="100%"
        ),
        
        width=rx.cond(
            NavigationState.is_sidebar_collapsed,
            "60px",
            "280px"
        ),
        height="100vh",
        background=rx.color("gray", 1),
        border_right=f"1px solid {rx.color('gray', 6)}",
        position="relative",
        transition="width 0.3s ease",
        flex_shrink="0",
        display=["none", "none", "block"]  # Hidden on mobile
    )