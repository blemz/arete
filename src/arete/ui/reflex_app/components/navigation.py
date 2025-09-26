"""Enhanced navigation components for Arete Reflex app."""

import reflex as rx
from typing import List, Dict
from ..state import NavigationState


def nav_link(text: str, href: str, icon: str = None) -> rx.Component:
    """Create a navigation link with optional icon and active state highlighting."""
    return rx.link(
        rx.flex(
            rx.cond(
                icon,
                rx.icon(icon, size=18),
                rx.fragment()
            ),
            rx.text(text, font_weight="medium"),
            align_items="center",
            gap="2",
            padding="2",
            border_radius="md",
            transition="all 0.2s",
            _hover={
                "background": rx.color("gray", 2),
                "color": rx.color("accent", 11)
            },
            background=rx.cond(
                NavigationState.current_route == href,
                rx.color("accent", 3),
                "transparent"
            ),
            color=rx.cond(
                NavigationState.current_route == href,
                rx.color("accent", 11),
                rx.color("gray", 11)
            ),
        ),
        href=href,
        text_decoration="none",
        on_click=NavigationState.set_current_route(href)
    )


def mobile_hamburger_button() -> rx.Component:
    """Mobile hamburger menu button."""
    return rx.button(
        rx.icon("menu", size=24),
        variant="ghost",
        size="3",
        display=["flex", "flex", "none"],
        on_click=NavigationState.toggle_mobile_menu,
        aria_label="Toggle navigation menu"
    )


def theme_toggle_button() -> rx.Component:
    """Theme toggle button with icon change."""
    return rx.button(
        rx.cond(
            NavigationState.theme_mode == "dark",
            rx.icon("sun", size=18),
            rx.icon("moon", size=18)
        ),
        variant="ghost",
        size="2",
        on_click=NavigationState.toggle_theme,
        aria_label="Toggle theme"
    )


def user_profile_dropdown() -> rx.Component:
    """User profile dropdown menu (simplified for compatibility)."""
    return rx.button(
        rx.flex(
            rx.text("👤", font_size="lg"),
            rx.text(NavigationState.user_name, font_weight="medium"),
            align_items="center",
            gap="2"
        ),
        variant="ghost",
        size="3"
    )


def layout_mode_selector() -> rx.Component:
    """Layout mode selector buttons."""
    return rx.flex(
        rx.button(
            rx.icon("layout-panel-left", size=16),
            variant=rx.cond(
                NavigationState.layout_mode == "split",
                "soft",
                "ghost"
            ),
            size="2",
            on_click=NavigationState.set_layout_mode("split"),
            aria_label="Split view"
        ),
        rx.button(
            rx.icon("message-circle", size=16),
            variant=rx.cond(
                NavigationState.layout_mode == "chat",
                "soft", 
                "ghost"
            ),
            size="2",
            on_click=NavigationState.set_layout_mode("chat"),
            aria_label="Chat only"
        ),
        rx.button(
            rx.icon("file-text", size=16),
            variant=rx.cond(
                NavigationState.layout_mode == "document",
                "soft",
                "ghost"
            ),
            size="2", 
            on_click=NavigationState.set_layout_mode("document"),
            aria_label="Document only"
        ),
        gap="1",
        display=["none", "none", "flex"]
    )


def navigation_bar() -> rx.Component:
    """Main responsive navigation bar with mobile support."""
    return rx.box(
        # Main navigation bar
        rx.flex(
            # Left section - Logo and brand
            rx.flex(
                mobile_hamburger_button(),
                rx.link(
                    rx.flex(
                        rx.icon("graduation-cap", size=24, color=rx.color("accent", 11)),
                        rx.text(
                            "Arete",
                            font_size="xl",
                            font_weight="bold",
                            color=rx.color("accent", 11)
                        ),
                        align_items="center",
                        gap="2"
                    ),
                    href="/",
                    text_decoration="none",
                    on_click=NavigationState.set_current_route("/")
                ),
                align_items="center",
                gap="3"
            ),
            
            # Center section - Navigation links (desktop)
            rx.flex(
                nav_link("Home", "/", "home"),
                nav_link("Chat", "/chat", "message-circle"),
                nav_link("Library", "/library", "book-open"),
                nav_link("Analytics", "/analytics", "bar-chart-3"),
                nav_link("About", "/about", "info"),
                align_items="center",
                gap="1",
                display=["none", "none", "flex"]
            ),
            
            # Right section - Controls and user menu
            rx.flex(
                layout_mode_selector(),
                theme_toggle_button(),
                user_profile_dropdown(),
                align_items="center",
                gap="2"
            ),
            
            justify_content="space-between",
            align_items="center",
            padding="3",
            max_width="1200px",
            margin="0 auto",
            width="100%"
        ),
        
        # Mobile menu (hidden by default)
        rx.cond(
            NavigationState.is_mobile_menu_open,
            rx.box(
                rx.flex(
                    nav_link("Home", "/", "home"),
                    nav_link("Chat", "/chat", "message-circle"), 
                    nav_link("Library", "/library", "book-open"),
                    nav_link("Analytics", "/analytics", "bar-chart-3"),
                    nav_link("About", "/about", "info"),
                    rx.separator(margin="2"),
                    rx.flex(
                        rx.text("Layout Mode", font_weight="medium", margin_bottom="2"),
                        rx.flex(
                            rx.button(
                                rx.flex(
                                    rx.icon("layout-panel-left", size=16),
                                    rx.text("Split View"),
                                    align_items="center",
                                    gap="2"
                                ),
                                variant=rx.cond(
                                    NavigationState.layout_mode == "split",
                                    "soft",
                                    "ghost"
                                ),
                                justify="start",
                                width="100%",
                                on_click=NavigationState.set_layout_mode("split")
                            ),
                            rx.button(
                                rx.flex(
                                    rx.icon("message-circle", size=16),
                                    rx.text("Chat Only"),
                                    align_items="center",
                                    gap="2"
                                ),
                                variant=rx.cond(
                                    NavigationState.layout_mode == "chat",
                                    "soft",
                                    "ghost"
                                ),
                                justify="start",
                                width="100%",
                                on_click=NavigationState.set_layout_mode("chat")
                            ),
                            rx.button(
                                rx.flex(
                                    rx.icon("file-text", size=16),
                                    rx.text("Document Only"),
                                    align_items="center",
                                    gap="2"
                                ),
                                variant=rx.cond(
                                    NavigationState.layout_mode == "document",
                                    "soft",
                                    "ghost"
                                ),
                                justify="start",
                                width="100%",
                                on_click=NavigationState.set_layout_mode("document")
                            ),
                            direction="column",
                            gap="1"
                        ),
                        direction="column"
                    ),
                    direction="column",
                    gap="2",
                    padding="3"
                ),
                background=rx.color("gray", 1),
                border_top=f"1px solid {rx.color('gray', 6)}",
                display=["block", "block", "none"]
            )
        ),
        
        background=rx.color("gray", 1),
        border_bottom=f"1px solid {rx.color('gray', 6)}",
        position="sticky",
        top="0",
        z_index="50"
    )


def keyboard_navigation_shortcuts() -> rx.Component:
    """Invisible component that handles keyboard shortcuts."""
    return rx.fragment(
        # This would typically use JavaScript event listeners
        # For now, we'll include it as a placeholder for keyboard navigation
    )