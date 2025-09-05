"""Accessibility components and keyboard navigation support."""

import reflex as rx
from ..state import NavigationState


def keyboard_shortcuts_modal() -> rx.Component:
    """Modal displaying available keyboard shortcuts."""
    shortcuts = [
        {"key": "Alt + H", "description": "Go to Home page"},
        {"key": "Alt + C", "description": "Open Chat interface"}, 
        {"key": "Alt + L", "description": "Browse Library"},
        {"key": "Alt + A", "description": "View Analytics"},
        {"key": "Alt + ?", "description": "Show keyboard shortcuts"},
        {"key": "Alt + T", "description": "Toggle theme"},
        {"key": "Alt + S", "description": "Toggle sidebar"},
        {"key": "Alt + M", "description": "Toggle mobile menu"},
        {"key": "Ctrl + /", "description": "Focus search"},
        {"key": "Escape", "description": "Close dialogs/menus"},
        {"key": "Tab", "description": "Navigate forward"},
        {"key": "Shift + Tab", "description": "Navigate backward"},
        {"key": "Enter", "description": "Activate focused element"},
        {"key": "Space", "description": "Toggle buttons/checkboxes"},
        {"key": "Arrow Keys", "description": "Navigate lists/menus"}
    ]
    
    return rx.dialog(
        rx.dialog_trigger(
            rx.button(
                rx.icon("keyboard", size=16),
                variant="ghost",
                size="2",
                aria_label="Keyboard shortcuts"
            )
        ),
        rx.dialog_content(
            rx.dialog_header(
                rx.dialog_title("Keyboard Shortcuts"),
                rx.dialog_description("Navigate Arete efficiently with these keyboard shortcuts")
            ),
            rx.flex(
                *[
                    rx.flex(
                        rx.kbd(
                            shortcut["key"],
                            font_family="mono",
                            padding="1",
                            background=rx.color("gray", 3),
                            border_radius="sm",
                            font_size="sm"
                        ),
                        rx.text(shortcut["description"], flex="1"),
                        justify_content="space-between",
                        align_items="center",
                        padding="2",
                        border_bottom=f"1px solid {rx.color('gray', 4)}"
                    )
                    for shortcut in shortcuts
                ],
                direction="column",
                gap="0",
                margin="4 0"
            ),
            rx.dialog_close(
                rx.button("Close", variant="soft")
            ),
            max_width="500px"
        )
    )


def skip_to_content_link() -> rx.Component:
    """Skip to content link for screen readers."""
    return rx.link(
        "Skip to main content",
        href="#main-content",
        position="absolute",
        left="-10000px", 
        top="auto",
        width="1px",
        height="1px", 
        overflow="hidden",
        background=rx.color("accent", 11),
        color="white",
        padding="2",
        border_radius="md",
        font_weight="semibold",
        text_decoration="none",
        z_index="9999",
        _focus={
            "position": "static",
            "left": "auto",
            "width": "auto", 
            "height": "auto",
            "overflow": "visible"
        }
    )


def aria_live_region() -> rx.Component:
    """ARIA live region for dynamic content announcements."""
    return rx.box(
        id="aria-live-region",
        aria_live="polite",
        aria_atomic="true",
        position="absolute",
        left="-10000px",
        width="1px",
        height="1px",
        overflow="hidden"
    )


def focus_trap(children: rx.Component) -> rx.Component:
    """Focus trap for modal dialogs and dropdowns."""
    return rx.box(
        children,
        # Focus trap would be implemented with JavaScript
        # This is a placeholder for the concept
        on_key_down=lambda e: rx.cond(
            e.key == "Tab",
            # Handle focus trapping logic
            rx.fragment(),
            rx.fragment()
        )
    )


def accessible_button(
    text: str,
    icon: str = None,
    variant: str = "solid",
    size: str = "2",
    aria_label: str = None,
    on_click = None,
    disabled: bool = False
) -> rx.Component:
    """Accessible button with proper ARIA attributes."""
    return rx.button(
        rx.cond(
            icon,
            rx.flex(
                rx.icon(icon, size=16),
                rx.text(text),
                align_items="center",
                gap="2"
            ),
            rx.text(text)
        ),
        variant=variant,
        size=size,
        disabled=disabled,
        on_click=on_click,
        aria_label=aria_label or text,
        role="button",
        tabindex="0",
        _focus_visible={
            "outline": f"2px solid {rx.color('accent', 8)}",
            "outline_offset": "2px"
        }
    )


def accessible_navigation() -> rx.Component:
    """Navigation with proper ARIA landmarks and structure."""
    return rx.box(
        role="navigation",
        aria_label="Main navigation",
        # Navigation content would go here
    )


def screen_reader_text(text: str) -> rx.Component:
    """Text that's only visible to screen readers."""
    return rx.text(
        text,
        position="absolute",
        left="-10000px",
        top="auto", 
        width="1px",
        height="1px",
        overflow="hidden",
        class_name="sr-only"
    )


def keyboard_navigation_handler() -> rx.Component:
    """Global keyboard navigation event handler."""
    return rx.fragment(
        # This would typically be implemented with custom JavaScript
        # For now, we include it as a conceptual placeholder
        rx.script(
            """
            document.addEventListener('keydown', function(e) {
                // Alt + H: Home
                if (e.altKey && e.key === 'h') {
                    e.preventDefault();
                    window.location.href = '/';
                }
                
                // Alt + C: Chat
                if (e.altKey && e.key === 'c') {
                    e.preventDefault();
                    window.location.href = '/chat';
                }
                
                // Alt + L: Library
                if (e.altKey && e.key === 'l') {
                    e.preventDefault();
                    window.location.href = '/library';
                }
                
                // Alt + A: Analytics  
                if (e.altKey && e.key === 'a') {
                    e.preventDefault();
                    window.location.href = '/analytics';
                }
                
                // Alt + ?: Help/Shortcuts
                if (e.altKey && e.key === '?') {
                    e.preventDefault();
                    // Open keyboard shortcuts modal
                }
                
                // Escape: Close modals/menus
                if (e.key === 'Escape') {
                    // Close any open modals or menus
                }
            });
            """
        )
    )


def accessibility_provider(children: rx.Component) -> rx.Component:
    """Provider that wraps the app with accessibility features."""
    return rx.box(
        skip_to_content_link(),
        aria_live_region(),
        keyboard_navigation_handler(),
        children,
        # Global accessibility styles
        style={
            # Ensure sufficient color contrast
            "--color-contrast-ratio": "4.5:1",
            
            # Focus indicators
            "*:focus": {
                "outline": f"2px solid {rx.color('accent', 8)}",
                "outline_offset": "2px"
            },
            
            # High contrast mode support
            "@media (prefers-contrast: high)": {
                "*": {
                    "border_color": rx.color("gray", 12),
                    "color": rx.color("gray", 12)
                }
            },
            
            # Reduced motion support  
            "@media (prefers-reduced-motion: reduce)": {
                "*": {
                    "animation_duration": "0.01ms !important",
                    "animation_iteration_count": "1 !important", 
                    "transition_duration": "0.01ms !important"
                }
            },
            
            # Large text support
            "@media (min-resolution: 192dpi)": {
                "font_size": "110%"
            }
        }
    )