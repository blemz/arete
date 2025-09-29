"""Chat page for the Arete application - Fixed version."""

import reflex as rx
from typing import List
from ..components.layout import create_base_layout
from ..components.chat import chat_interface
from ..components.sidebar import create_sidebar
from ..state.chat_state import ChatState
from ..state.ui_state import UIState


def create_chat_header() -> rx.Component:
    """Create the chat header with actions."""
    return rx.hstack(
        rx.heading("Chat", size="6"),
        rx.spacer(),
        # Fixed menu implementation using popover instead of non-existent menu_button
        rx.popover.root(
            rx.popover.trigger(
                rx.icon_button(
                    rx.icon("more_vertical", size=20),
                    variant="ghost",
                    size="sm",
                )
            ),
            rx.popover.content(
                rx.vstack(
                    rx.button(
                        "Export Conversation",
                        variant="ghost",
                        width="100%",
                        justify="start",
                    ),
                    rx.button(
                        "Settings",
                        variant="ghost",
                        width="100%",
                        justify="start",
                    ),
                    spacing="1",
                    padding="2",
                ),
                side="bottom",
                align="end",
            ),
        ),
        justify="between",
        align="center",
        width="100%",
        padding_bottom="4",
    )


def chat_page() -> rx.Component:
    """Main chat page component."""
    return create_base_layout(
        rx.vstack(
            create_chat_header(),
            chat_interface(),
            spacing="4",
            width="100%",
            height="100%",
        ),
        page_title="Chat - Arete",
        show_sidebar=True,
    )