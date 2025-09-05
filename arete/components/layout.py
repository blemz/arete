"""Responsive layout components with multiple view modes and accessibility support."""

import reflex as rx
from ..state import NavigationState, ChatState, DocumentState
from .navigation import navigation_bar, keyboard_navigation_shortcuts
from .sidebar import sidebar
from .footer import footer


def chat_interface() -> rx.Component:
    """Chat interface component."""
    return rx.box(
        rx.flex(
            # Chat header
            rx.flex(
                rx.text("Philosophical Assistant", font_weight="semibold", font_size="lg"),
                rx.text("Ask questions about classical philosophy", 
                       font_size="sm", color=rx.color("gray", 10)),
                direction="column",
                gap="1"
            ),
            
            # Messages area
            rx.box(
                rx.cond(
                    ChatState.messages.length() == 0,
                    rx.flex(
                        rx.icon("message-circle", size=48, color=rx.color("gray", 8)),
                        rx.text(
                            "Start a conversation about classical philosophy",
                            font_size="lg",
                            color=rx.color("gray", 10),
                            text_align="center"
                        ),
                        rx.text(
                            "Ask about virtue ethics, Socratic method, Platonic ideals, or any philosophical concept",
                            font_size="sm", 
                            color=rx.color("gray", 9),
                            text_align="center"
                        ),
                        direction="column",
                        align_items="center",
                        gap="4",
                        height="100%",
                        justify_content="center"
                    ),
                    rx.flex(
                        rx.foreach(
                            ChatState.messages,
                            lambda msg: rx.box(
                                rx.flex(
                                    rx.cond(
                                        msg["role"] == "user",
                                        rx.box(
                                            rx.text(msg["content"]),
                                            background=rx.color("accent", 3),
                                            color=rx.color("accent", 12),
                                            padding="3",
                                            border_radius="lg",
                                            max_width="80%",
                                            margin_left="auto"
                                        ),
                                        rx.box(
                                            rx.text(msg["content"]),
                                            background=rx.color("gray", 3),
                                            padding="3", 
                                            border_radius="lg",
                                            max_width="80%"
                                        )
                                    ),
                                    justify_content=rx.cond(
                                        msg["role"] == "user",
                                        "flex-end",
                                        "flex-start"
                                    ),
                                    width="100%"
                                ),
                                margin_bottom="4"
                            )
                        ),
                        direction="column",
                        padding="4",
                        height="100%",
                        overflow_y="auto"
                    )
                ),
                flex="1",
                overflow="hidden"
            ),
            
            # Input area
            rx.flex(
                rx.input(
                    placeholder="Ask about classical philosophy...",
                    value=ChatState.current_message,
                    on_change=ChatState.set_current_message,
                    on_key_down=lambda key: rx.cond(
                        key == "Enter",
                        ChatState.send_message,
                        rx.fragment()
                    ),
                    flex="1"
                ),
                rx.button(
                    rx.cond(
                        ChatState.is_loading,
                        rx.icon("loader-2", class_name="animate-spin"),
                        rx.icon("send")
                    ),
                    on_click=ChatState.send_message,
                    disabled=ChatState.is_loading,
                    size="3"
                ),
                gap="2",
                padding="4"
            ),
            
            direction="column",
            height="100%",
            gap="0"
        ),
        height="100%",
        background=rx.color("gray", 1),
        border_radius="lg",
        border=f"1px solid {rx.color('gray', 6)}"
    )


def document_viewer() -> rx.Component:
    """Document viewer component."""
    return rx.box(
        rx.flex(
            # Document header
            rx.flex(
                rx.text("Document Viewer", font_weight="semibold", font_size="lg"),
                rx.input(
                    placeholder="Search in document...",
                    value=DocumentState.search_query,
                    on_change=DocumentState.set_search_query,
                    on_key_down=lambda key: rx.cond(
                        key == "Enter", 
                        DocumentState.search_document,
                        rx.fragment()
                    ),
                    width="300px"
                ),
                justify_content="space-between",
                align_items="center",
                padding="4",
                border_bottom=f"1px solid {rx.color('gray', 6)}"
            ),
            
            # Document content
            rx.box(
                rx.cond(
                    DocumentState.current_document,
                    rx.box(
                        rx.text(DocumentState.document_content, line_height="1.8"),
                        padding="6"
                    ),
                    rx.flex(
                        rx.icon("book-open", size=48, color=rx.color("gray", 8)),
                        rx.text(
                            "Select a document to view",
                            font_size="lg",
                            color=rx.color("gray", 10),
                            text_align="center"
                        ),
                        rx.text(
                            "Browse classical philosophical texts with interactive features",
                            font_size="sm",
                            color=rx.color("gray", 9), 
                            text_align="center"
                        ),
                        direction="column",
                        align_items="center",
                        gap="4",
                        height="100%",
                        justify_content="center"
                    )
                ),
                flex="1",
                overflow_y="auto"
            ),
            
            direction="column",
            height="100%",
            gap="0"
        ),
        height="100%",
        background=rx.color("gray", 1),
        border_radius="lg",
        border=f"1px solid {rx.color('gray', 6)}"
    )


def split_view_layout() -> rx.Component:
    """Split view layout with chat and document side by side."""
    return rx.flex(
        chat_interface(),
        document_viewer(),
        gap="4",
        height="100%",
        flex_wrap=["wrap", "wrap", "nowrap"]
    )


def main_content_area() -> rx.Component:
    """Main content area that switches based on layout mode."""
    return rx.box(
        rx.cond(
            NavigationState.layout_mode == "split",
            split_view_layout(),
            rx.cond(
                NavigationState.layout_mode == "chat",
                chat_interface(),
                rx.cond(
                    NavigationState.layout_mode == "document",
                    document_viewer(),
                    # Default to split view
                    split_view_layout()
                )
            )
        ),
        flex="1",
        padding="4",
        overflow="hidden"
    )


def mobile_bottom_navigation() -> rx.Component:
    """Bottom navigation for mobile devices."""
    return rx.box(
        rx.flex(
            rx.button(
                rx.flex(
                    rx.icon("home", size=20),
                    rx.text("Home", font_size="xs"),
                    direction="column",
                    align_items="center",
                    gap="1"
                ),
                variant="ghost",
                flex="1",
                height="auto",
                padding="2"
            ),
            rx.button(
                rx.flex(
                    rx.icon("message-circle", size=20),
                    rx.text("Chat", font_size="xs"),
                    direction="column",
                    align_items="center", 
                    gap="1"
                ),
                variant="ghost",
                flex="1",
                height="auto",
                padding="2"
            ),
            rx.button(
                rx.flex(
                    rx.icon("book-open", size=20),
                    rx.text("Library", font_size="xs"),
                    direction="column",
                    align_items="center",
                    gap="1"
                ),
                variant="ghost", 
                flex="1",
                height="auto",
                padding="2"
            ),
            rx.button(
                rx.flex(
                    rx.icon("bar-chart-3", size=20),
                    rx.text("Analytics", font_size="xs"),
                    direction="column",
                    align_items="center",
                    gap="1"
                ),
                variant="ghost",
                flex="1", 
                height="auto",
                padding="2"
            ),
            gap="0",
            width="100%"
        ),
        background=rx.color("gray", 1),
        border_top=f"1px solid {rx.color('gray', 6)}",
        position="fixed",
        bottom="0",
        left="0",
        right="0",
        z_index="40",
        display=["block", "block", "none"],
        safe_area_inset_bottom="env(safe-area-inset-bottom)"
    )


def base_layout(children: rx.Component) -> rx.Component:
    """Base layout wrapper with navigation, sidebar, and footer."""
    return rx.box(
        # Skip to content link for accessibility
        rx.link(
            "Skip to main content",
            href="#main-content",
            position="absolute",
            left="-10000px",
            top="auto",
            width="1px", 
            height="1px",
            overflow="hidden",
            _focus={
                "position": "static",
                "left": "auto",
                "width": "auto",
                "height": "auto",
                "overflow": "visible"
            }
        ),
        
        # Keyboard navigation shortcuts
        keyboard_navigation_shortcuts(),
        
        # Main app structure
        rx.flex(
            # Navigation bar
            navigation_bar(),
            
            # Main content area with sidebar
            rx.flex(
                sidebar(),
                rx.box(
                    rx.box(
                        children,
                        id="main-content",
                        min_height="calc(100vh - 120px)",  # Account for nav and footer
                        padding_bottom=["60px", "60px", "0"]  # Space for mobile nav
                    ),
                    footer(),
                    flex="1",
                    overflow="hidden",
                    display="flex",
                    flex_direction="column"
                ),
                flex="1",
                overflow="hidden"
            ),
            
            direction="column",
            height="100vh",
            overflow="hidden"
        ),
        
        # Mobile bottom navigation
        mobile_bottom_navigation(),
        
        # Theme class for CSS custom properties
        class_name=rx.cond(
            NavigationState.theme_mode == "dark",
            "dark-theme",
            "light-theme"
        ),
        
        # Global styles
        style={
            "--color-background": rx.cond(
                NavigationState.theme_mode == "dark",
                "#0a0a0a",
                "#ffffff"
            ),
            "--color-foreground": rx.cond(
                NavigationState.theme_mode == "dark",
                "#fafafa", 
                "#0a0a0a"
            )
        }
    )


def page_layout(title: str, children: rx.Component) -> rx.Component:
    """Page layout with title and content."""
    return base_layout(
        rx.box(
            rx.heading(title, font_size="2xl", margin_bottom="6"),
            children,
            padding="6",
            max_width="1200px",
            margin="0 auto",
            width="100%"
        )
    )