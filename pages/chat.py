import reflex as rx
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

from state.chat_state import RAGChatState, MessageType
from components.chat_components import (
    enhanced_message_bubble,
    enhanced_typing_indicator,
    performance_stats_panel,
    advanced_search_panel,
    conversation_export_modal,
    citation_detail_modal,
    quick_actions_panel
)


def enhanced_message_input() -> rx.Component:
    """Enhanced message input with keyboard shortcuts and smart features"""
    return rx.box(
        rx.vstack(
            # Input suggestions (when input is focused but empty)
            rx.cond(
                (RAGChatState.current_input == "") & ~RAGChatState.has_messages,
                rx.hstack(
                    rx.text("Try asking:", font_size="sm", color="gray.400"),
                    rx.button(
                        "What is virtue?",
                        size="xs",
                        variant="ghost",
                        color_scheme="blue",
                        on_click=lambda: RAGChatState.set_input("What is virtue?")
                    ),
                    rx.button(
                        "Who was Socrates?",
                        size="xs",
                        variant="ghost", 
                        color_scheme="blue",
                        on_click=lambda: RAGChatState.set_input("Who was Socrates?")
                    ),
                    align="center",
                    spacing="2",
                    mb="2"
                )
            ),
            
            # Main input area
            rx.hstack(
                rx.textarea(
                    placeholder="Ask me about classical philosophy... (Press Ctrl+Enter to send)",
                    value=RAGChatState.current_input,
                    on_change=RAGChatState.set_input,
                    on_key_down=lambda key: rx.cond(
                        (key.key == "Enter") & key.ctrl_key & ~RAGChatState.is_processing,
                        RAGChatState.send_message()
                    ),
                    resize="vertical",
                    min_height="50px",
                    max_height="200px",
                    flex="1",
                    disabled=RAGChatState.is_processing,
                    bg="gray.800",
                    border="1px solid gray.600",
                    _focus={"border_color": "blue.500"},
                    color="white",
                    _placeholder={"color": "gray.500"}
                ),
                rx.vstack(
                    rx.button(
                        rx.cond(
                            RAGChatState.is_processing,
                            rx.spinner(size="sm"),
                            rx.icon("send", size="sm")
                        ),
                        on_click=RAGChatState.send_message,
                        disabled=RAGChatState.is_processing | (RAGChatState.current_input.strip() == ""),
                        color_scheme="blue",
                        size="md",
                        height="50px",
                        min_width="50px"
                    ),
                    # Regenerate button (only show if can regenerate)
                    rx.cond(
                        RAGChatState.can_regenerate & ~RAGChatState.is_processing,
                        rx.button(
                            rx.icon("refresh-cw", size="sm"),
                            on_click=RAGChatState.regenerate_last_response,
                            variant="outline",
                            color_scheme="gray",
                            size="sm",
                            width="50px"
                        )
                    ),
                    spacing="2"
                ),
                spacing="3",
                width="100%",
                align="end"
            ),
            
            # Status indicators
            rx.hstack(
                # Character count
                rx.text(
                    f"{len(RAGChatState.current_input)}/2000",
                    font_size="xs",
                    color="gray.500" if len(RAGChatState.current_input) < 1800 else "orange.400"
                ),
                rx.spacer(),
                # Keyboard shortcut hint
                rx.text(
                    "Ctrl+Enter to send",
                    font_size="xs",
                    color="gray.500"
                ),
                width="100%",
                mt="1"
            ),
            
            spacing="2"
        ),
        p="4",
        bg="gray.900",
        border_top="1px solid gray.700"
    )


def enhanced_chat_header() -> rx.Component:
    """Enhanced chat header with comprehensive controls"""
    return rx.box(
        rx.vstack(
            # Main header
            rx.hstack(
                rx.hstack(
                    rx.icon("brain", size="lg", color="blue.400"),
                    rx.vstack(
                        rx.heading("Arete", size="lg", color="white"),
                        rx.text(
                            "Classical Philosophy Tutor",
                            font_size="sm",
                            color="gray.400"
                        ),
                        spacing="0",
                        align="start"
                    ),
                    align="center",
                    spacing="3"
                ),
                
                # Status indicators
                rx.hstack(
                    rx.cond(
                        RAGChatState._services_initialized,
                        rx.badge("RAG Online", color_scheme="green", variant="solid"),
                        rx.badge("Initializing...", color_scheme="yellow", variant="solid")
                    ),
                    rx.badge(
                        f"{len(RAGChatState.messages)} msgs",
                        color_scheme="blue",
                        variant="outline"
                    ),
                    rx.cond(
                        RAGChatState.conversation_stats["total_tokens"] > 0,
                        rx.badge(
                            f"{RAGChatState.conversation_stats['total_tokens']} tokens",
                            color_scheme="purple",
                            variant="outline"
                        )
                    ),
                    spacing="2"
                ),
                
                # Action buttons
                rx.hstack(
                    rx.button(
                        rx.icon("search", size="sm"),
                        size="sm",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=lambda: None  # Toggle search panel
                    ),
                    rx.button(
                        rx.icon("bar-chart", size="sm"),
                        size="sm",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=RAGChatState.toggle_retrieval_stats
                    ),
                    rx.button(
                        rx.icon("eye" if RAGChatState.show_citations else "eye-off", size="sm"),
                        size="sm",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=RAGChatState.toggle_citations
                    ),
                    rx.menu(
                        rx.menu_button(
                            rx.icon("more-vertical", size="sm"),
                            size="sm",
                            variant="ghost",
                            color_scheme="gray"
                        ),
                        rx.menu_list(
                            rx.menu_item(
                                rx.icon("download", margin_right="0.5rem"),
                                "Export Conversation",
                                on_click=lambda: None  # Open export modal
                            ),
                            rx.menu_item(
                                rx.icon("settings", margin_right="0.5rem"),
                                "Settings"
                            ),
                            rx.menu_divider(),
                            rx.menu_item(
                                rx.icon("trash-2", margin_right="0.5rem"),
                                "Clear Conversation",
                                color="red.400",
                                on_click=RAGChatState.clear_conversation
                            )
                        )
                    ),
                    spacing="2"
                ),
                
                justify="space-between",
                align="center",
                width="100%"
            ),
            
            # Conversation title (editable)
            rx.cond(
                RAGChatState.conversation_metadata is not None,
                rx.hstack(
                    rx.editable(
                        rx.editable_preview(
                            RAGChatState.conversation_metadata.title,
                            color="gray.300",
                            font_size="sm"
                        ),
                        rx.editable_input(
                            font_size="sm",
                            bg="gray.800",
                            color="white"
                        ),
                        value=RAGChatState.conversation_metadata.title,
                        on_submit=lambda title: RAGChatState.conversation_metadata.update(title=title),
                        flex="1"
                    ),
                    rx.text(
                        RAGChatState.conversation_metadata.created_at.strftime("%Y-%m-%d %H:%M"),
                        font_size="xs",
                        color="gray.500"
                    ),
                    justify="space-between",
                    width="100%",
                    mt="2"
                )
            ),
            
            spacing="3"
        ),
        p="4",
        bg="gray.900",
        border_bottom="1px solid gray.700"
    )


def main_chat_interface() -> rx.Component:
    """Main chat interface with advanced layout"""
    return rx.box(
        rx.vstack(
            # Messages area with auto-scroll
            rx.box(
                rx.cond(
                    RAGChatState.has_messages,
                    rx.vstack(
                        # Performance stats panel (collapsible)
                        performance_stats_panel(),
                        
                        # Messages
                        *[enhanced_message_bubble(message) for message in RAGChatState.filtered_messages],
                        
                        # Typing indicator
                        enhanced_typing_indicator(),
                        
                        spacing="4",
                        width="100%",
                        align="stretch",
                        px="4",
                        py="6"
                    ),
                    # Quick actions when no messages
                    quick_actions_panel()
                ),
                flex="1",
                overflow_y="auto",
                bg="gray.900",
                width="100%",
                id="chat-messages-container",
                class_name="messages-container"
            ),
            
            spacing="0",
            height="100%"
        ),
        height="100%",
        width="100%"
    )


def sidebar_panel() -> rx.Component:
    """Optional sidebar with advanced features"""
    return rx.box(
        rx.vstack(
            # Advanced search
            advanced_search_panel(),
            
            # Conversation management
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("message-square", size="sm", color="purple.400"),
                        rx.text("Conversations", font_weight="medium", color="white"),
                        justify="flex-start",
                        align="center",
                        spacing="2"
                    ),
                    
                    # Saved conversations list
                    rx.vstack(
                        *[
                            rx.button(
                                rx.hstack(
                                    rx.text(
                                        conv.title[:30] + "..." if len(conv.title) > 30 else conv.title,
                                        font_size="sm",
                                        text_align="left"
                                    ),
                                    rx.text(
                                        f"{conv.message_count} msgs",
                                        font_size="xs",
                                        color="gray.500"
                                    ),
                                    justify="space-between",
                                    width="100%"
                                ),
                                variant="ghost",
                                color_scheme="gray",
                                width="100%",
                                height="auto",
                                py="2",
                                on_click=RAGChatState.load_conversation(conv.id)
                            )
                            for conv in RAGChatState.saved_conversations[-10:]  # Last 10 conversations
                        ],
                        spacing="1",
                        width="100%"
                    ) if RAGChatState.saved_conversations else rx.text(
                        "No saved conversations",
                        font_size="sm",
                        color="gray.500",
                        text_align="center"
                    ),
                    
                    spacing="3",
                    align="stretch"
                ),
                bg="gray.900",
                p="4",
                border_radius="lg",
                border="1px solid gray.700"
            ),
            
            spacing="4",
            height="100%",
            width="300px"
        ),
        display=["none", "none", "block"],  # Hide on mobile/tablet
        bg="gray.950",
        border_right="1px solid gray.700",
        height="100%"
    )


@rx.page(route="/chat", title="Arete - Classical Philosophy Chat")
def chat_page() -> rx.Component:
    """Enhanced main chat page with comprehensive RAG integration"""
    
    # Handle URL parameters for quick questions
    def handle_url_query():
        # This would parse URL query parameters like ?q=What+is+virtue
        # and set the initial input - implementation would depend on Reflex routing
        pass
    
    return rx.fragment(
        # Main layout
        rx.hstack(
            # Optional sidebar (desktop only)
            sidebar_panel(),
            
            # Main chat area
            rx.vstack(
                enhanced_chat_header(),
                main_chat_interface(),
                enhanced_message_input(),
                spacing="0",
                height="100vh",
                flex="1"
            ),
            
            spacing="0",
            height="100vh",
            width="100vw",
            bg="gray.900",
            color="white"
        ),
        
        # Modals
        citation_detail_modal(),
        conversation_export_modal(),
        
        # Initialize services on page load
        rx.script("""
            // Auto-scroll to bottom when new messages arrive
            function scrollToBottom() {
                const container = document.getElementById('chat-messages-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }
            
            // Set up auto-scroll observer
            const observer = new MutationObserver(scrollToBottom);
            const container = document.getElementById('chat-messages-container');
            if (container) {
                observer.observe(container, { childList: true, subtree: true });
            }
            
            // Focus input on page load
            setTimeout(() => {
                const input = document.querySelector('textarea[placeholder*="classical philosophy"]');
                if (input) input.focus();
            }, 100);
        """)
    )


# Additional utility pages
@rx.page(route="/chat/settings", title="Chat Settings")
def chat_settings_page() -> rx.Component:
    """Chat settings and configuration page"""
    return rx.container(
        rx.vstack(
            rx.heading("Chat Settings", size="xl", color="white"),
            
            # RAG Configuration
            rx.box(
                rx.vstack(
                    rx.heading("RAG Configuration", size="lg", color="white"),
                    
                    rx.hstack(
                        rx.text("Retrieval Limit:", color="gray.300"),
                        rx.number_input(
                            value=RAGChatState.retrieval_limit,
                            min_value=1,
                            max_value=20,
                            on_change=lambda val: RAGChatState.update_settings(retrieval_limit=val)
                        ),
                        align="center",
                        spacing="3"
                    ),
                    
                    rx.hstack(
                        rx.text("Similarity Threshold:", color="gray.300"),
                        rx.slider(
                            value=RAGChatState.similarity_threshold,
                            min_value=0.1,
                            max_value=1.0,
                            step=0.1,
                            on_change=lambda val: RAGChatState.update_settings(similarity_threshold=val),
                            width="200px"
                        ),
                        rx.text(f"{RAGChatState.similarity_threshold:.1f}", color="gray.400"),
                        align="center",
                        spacing="3"
                    ),
                    
                    rx.hstack(
                        rx.text("Context Messages:", color="gray.300"),
                        rx.number_input(
                            value=RAGChatState.max_context_messages,
                            min_value=1,
                            max_value=50,
                            on_change=lambda val: RAGChatState.update_settings(max_context_messages=val)
                        ),
                        align="center",
                        spacing="3"
                    ),
                    
                    spacing="4",
                    align="stretch"
                ),
                bg="gray.800",
                p="6",
                border_radius="lg",
                border="1px solid gray.600"
            ),
            
            # Display Settings
            rx.box(
                rx.vstack(
                    rx.heading("Display Settings", size="lg", color="white"),
                    
                    rx.checkbox(
                        "Show Citations",
                        is_checked=RAGChatState.show_citations,
                        on_change=RAGChatState.toggle_citations,
                        color_scheme="blue"
                    ),
                    
                    rx.checkbox(
                        "Show Performance Stats",
                        is_checked=RAGChatState.show_retrieval_stats,
                        on_change=RAGChatState.toggle_retrieval_stats,
                        color_scheme="blue"
                    ),
                    
                    rx.checkbox(
                        "Auto-scroll to Latest",
                        is_checked=RAGChatState.auto_scroll,
                        on_change=RAGChatState.toggle_auto_scroll,
                        color_scheme="blue"
                    ),
                    
                    spacing="3",
                    align="stretch"
                ),
                bg="gray.800",
                p="6",
                border_radius="lg",
                border="1px solid gray.600"
            ),
            
            # Reset button
            rx.button(
                "Reset to Defaults",
                color_scheme="red",
                variant="outline",
                on_click=RAGChatState.reset_settings
            ),
            
            # Back to chat
            rx.link(
                rx.button(
                    "Back to Chat",
                    color_scheme="blue"
                ),
                href="/chat"
            ),
            
            spacing="6",
            align="stretch",
            py="8"
        ),
        bg="gray.900",
        min_height="100vh",
        color="white"
    )