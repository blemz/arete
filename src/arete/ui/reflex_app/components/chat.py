"""
Chat interface component for the Arete Reflex application.
"""

import reflex as rx
from ..reflex_app import AreteState


def message_bubble(message: dict) -> rx.Component:
    """Individual message bubble component."""
    is_user = message.get("is_user", True)
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")
    
    if is_user:
        return rx.div(
            rx.div(
                rx.text(content, class_name="text-primary-content"),
                rx.text(timestamp, class_name="text-xs opacity-70 mt-1"),
                class_name="chat-bubble chat-bubble-primary max-w-md"
            ),
            class_name="chat chat-end mb-4"
        )
    else:
        return rx.div(
            rx.div(
                rx.text(content, class_name="text-base-content"),
                rx.text(timestamp, class_name="text-xs opacity-70 mt-1"),
                class_name="chat-bubble chat-bubble-secondary max-w-2xl"
            ),
            class_name="chat chat-start mb-4"
        )


def chat_input() -> rx.Component:
    """Chat input component with send button."""
    return rx.div(
        rx.div(
            rx.input(
                placeholder="Ask about virtue, justice, knowledge, or any philosophical concept...",
                value=AreteState.user_query,
                on_change=AreteState.set_user_query,
                class_name="input input-bordered flex-1",
                on_key_down=lambda key: rx.cond(
                    key == "Enter",
                    AreteState.send_message,
                    rx.fragment()
                )
            ),
            rx.button(
                rx.cond(
                    AreteState.is_loading,
                    rx.span(class_name="loading loading-spinner loading-sm"),
                    rx.text("Send")
                ),
                on_click=AreteState.send_message,
                disabled=AreteState.is_loading,
                class_name="btn btn-primary ml-2"
            ),
            class_name="flex items-center gap-2"
        ),
        class_name="p-4 bg-base-100 border-t border-base-200"
    )


def chat_header() -> rx.Component:
    """Chat header with title and controls."""
    return rx.div(
        rx.div(
            rx.heading(
                "Philosophy Chat",
                size="lg",
                font_weight="semibold",
                color="base-content"
            ),
            rx.text(
                "Ask questions about classical philosophical texts",
                class_name="text-sm opacity-70"
            ),
            class_name="flex-1"
        ),
        rx.div(
            rx.button(
                "Clear Chat",
                on_click=AreteState.clear_chat,
                class_name="btn btn-outline btn-sm"
            ),
            class_name="flex items-center"
        ),
        class_name="flex items-center justify-between p-4 bg-base-100 border-b border-base-200"
    )


def chat_messages() -> rx.Component:
    """Chat messages display area."""
    return rx.div(
        rx.cond(
            AreteState.chat_history.length() > 0,
            rx.div(
                rx.foreach(
                    AreteState.chat_history,
                    message_bubble
                ),
                class_name="space-y-4"
            ),
            rx.div(
                rx.div(
                    rx.text(
                        "🏛️",
                        font_size="3rem",
                        class_name="mb-4"
                    ),
                    rx.heading(
                        "Welcome to Arete",
                        size="xl",
                        class_name="mb-2"
                    ),
                    rx.text(
                        "Start a conversation about classical philosophy. "
                        "I can help you explore concepts from Plato, Aristotle, and other ancient thinkers.",
                        class_name="opacity-70 mb-4"
                    ),
                    rx.div(
                        rx.text("Try asking:", class_name="font-semibold mb-2"),
                        rx.ul(
                            rx.li("What is virtue according to Plato?"),
                            rx.li("How does Aristotle define justice?"),
                            rx.li("What is the Socratic method?"),
                            rx.li("Explain the allegory of the cave"),
                            class_name="list-disc list-inside space-y-1 text-sm opacity-70"
                        ),
                        class_name="text-left"
                    ),
                    class_name="text-center max-w-md"
                ),
                class_name="flex items-center justify-center h-full"
            )
        ),
        class_name="flex-1 overflow-auto p-4 bg-base-200"
    )


def chat_interface() -> rx.Component:
    """Complete chat interface component."""
    return rx.div(
        chat_header(),
        chat_messages(), 
        chat_input(),
        class_name="flex flex-col h-full bg-base-200"
    )