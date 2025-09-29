import reflex as rx
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from state.chat_state import RAGChatState, ChatMessage, MessageType


def enhanced_typing_indicator() -> rx.Component:
    """Enhanced typing indicator with animated dots"""
    return rx.cond(
        RAGChatState.typing_indicator,
        rx.hstack(
            rx.avatar(
                src="/arete-logo.png",
                fallback="A",
                size=16,
                color_scheme="blue"
            ),
            rx.hstack(
                rx.text("Arete is analyzing classical texts", color="gray.400"),
                rx.hstack(
                    rx.box(
                        width="4px",
                        height="4px", 
                        bg="gray.500",
                        border_radius="full",
                        class_name="typing-dot"
                    ),
                    rx.box(
                        width="4px",
                        height="4px",
                        bg="gray.500", 
                        border_radius="full",
                        class_name="typing-dot"
                    ),
                    rx.box(
                        width="4px",
                        height="4px",
                        bg="gray.500",
                        border_radius="full",
                        class_name="typing-dot"
                    ),
                    spacing="1",
                    align="center"
                ),
                align="center",
                spacing="2"
            ),
            align="center",
            spacing="3",
            p="4",
            bg="gray.800",
            border_radius="lg",
            max_width="300px"
        )
    )


def advanced_citation_card(citation: Dict[str, Any]) -> rx.Component:
    """Advanced citation card with detailed metadata"""
    return rx.box(
        rx.vstack(
            # Citation header
            rx.hstack(
                rx.hstack(
                    rx.icon("book-open", size=16, color="blue.400"),
                    rx.text(
                        citation.get("source", "Unknown Source"),
                        font_size="sm",
                        font_weight="medium",
                        color="blue.300"
                    ),
                    align="center",
                    spacing="2"
                ),
                rx.hstack(
                    rx.badge(
                        f"{citation.get('relevance_score', 0):.1%}",
                        color_scheme="green",
                        variant="subtle",
                        font_size="xs"
                    ),
                    rx.cond(
                        citation.get("position") is not None,
                        rx.badge(
                            f"Pos: {citation.get('position')}",
                            color_scheme="blue", 
                            variant="outline",
                            font_size="xs"
                        )
                    ),
                    spacing="2"
                ),
                justify="between",
                width="100%"
            ),
            
            # Citation preview text
            rx.text(
                citation.get("text", "")[:300] + "..." if citation.get("text", "").__len__() > 300 else citation.get("text", ""),
                font_size="sm",
                color="gray.300",
                line_height="1.5",
                white_space="pre-wrap"
            ),
            
            # Additional metadata
            rx.cond(
                citation.get("entities"),
                rx.hstack(
                    rx.text("Entities:", font_size="xs", color="gray.500"),
                    rx.hstack(
                        *[
                            rx.badge(entity, color_scheme="purple", variant="outline", font_size="xs")
                            for entity in citation.get("entities", [])[:3]  # Show max 3 entities
                        ],
                        spacing="1",
                        wrap="wrap"
                    ),
                    align="center",
                    spacing="2",
                    width="100%"
                )
            ),
            
            # Actions
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=12),
                    "View Full",
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=RAGChatState.open_citation_modal(citation.get("id"))
                ),
                rx.button(
                    rx.icon("copy", size=12),
                    "Copy",
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=lambda: rx.set_clipboard(citation.get("text", ""))
                ),
                justify="end",
                spacing="2",
                width="100%"
            ),
            
            spacing="3",
            align="stretch"
        ),
        bg="gray.800",
        p="3",
        border_radius="md",
        border="1px solid gray.600",
        cursor="pointer",
        class_name="citation-preview",
        on_click=RAGChatState.open_citation_modal(citation.get("id")),
        _hover={
            "border_color": "blue.500",
            "bg": "gray.750"
        }
    )


def performance_stats_panel() -> rx.Component:
    """Performance statistics panel"""
    return rx.cond(
        RAGChatState.show_retrieval_stats,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("activity", size=16, color="green.400"),
                    rx.text("Performance Stats", font_weight="medium", color="white"),
                    justify="start",
                    align="center",
                    spacing="2"
                ),
                
                rx.grid(
                    rx.box(
                        rx.text("Avg Response Time", color="gray.400", font_size="xs"),
                        rx.text(f"{RAGChatState.average_response_time:.1f}s", font_size="sm", font_weight="bold")
                    ),
                    rx.box(
                        rx.text("Total Queries", color="gray.400", font_size="xs"),
                        rx.text(RAGChatState.total_queries, font_size="sm", font_weight="bold")
                    ),
                    rx.box(
                        rx.text("Messages", color="gray.400", font_size="xs"),
                        rx.text(RAGChatState.conversation_stats["total_messages"], font_size="sm", font_weight="bold")
                    ),
                    rx.box(
                        rx.text("Total Tokens", color="gray.400", font_size="xs"),
                        rx.text(RAGChatState.conversation_stats["total_tokens"], font_size="sm", font_weight="bold")
                    ),
                    columns="4",
                    spacing="4",
                    width="100%"
                ),
                
                spacing="3",
                align="stretch"
            ),
            bg="gray.900",
            p="4",
            border_radius="lg",
            border="1px solid gray.700",
            mb="4"
        )
    )


def advanced_search_panel() -> rx.Component:
    """Advanced search and filter panel"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("search", size=16, color="blue.400"),
                rx.text("Search Conversation", font_weight="medium", color="white"),
                justify="start",
                align="center",
                spacing="2"
            ),
            
            # Search input
            rx.hstack(
                rx.input(
                    placeholder="Search messages, citations, or metadata...",
                    value=RAGChatState.search_query,
                    on_change=RAGChatState.set_search_query,
                    flex="1",
                    bg="gray.800",
                    border="1px solid gray.600",
                    _focus={"border_color": "blue.500"}
                ),
                rx.button(
                    rx.icon("x", size=16),
                    size="2",
                    variant="ghost",
                    on_click=RAGChatState.clear_search,
                    disabled=RAGChatState.search_query == ""
                ),
                spacing="2",
                width="100%"
            ),
            
            # Search mode selector
            rx.select(
                ["content", "citations", "metadata"],
                placeholder="Search mode...",
                value=RAGChatState.search_mode,
                on_change=RAGChatState.set_search_mode,
                width="100%"
            ),
            
            # Search results summary
            rx.cond(
                RAGChatState.search_query != "",
                rx.text(
                    f"Found {RAGChatState.filtered_messages.length()} of {RAGChatState.messages.length()} messages",
                    font_size="sm",
                    color="gray.400"
                )
            ),
            
            spacing="3",
            align="stretch"
        ),
        bg="gray.900",
        p="4",
        border_radius="lg",
        border="1px solid gray.700",
        mb="4"
    )


def message_actions_menu(message_id: str) -> rx.Component:
    """Context menu for message actions"""
    return rx.menu(
        rx.menu_button(
            rx.icon("more-vertical", size=16),
            size="2",
            variant="ghost",
            color_scheme="gray"
        ),
        rx.menu_list(
            rx.menu_item(
                rx.icon("copy", size=16, margin_right="0.5rem"),
                "Copy Message",
                on_click=RAGChatState.copy_message_content(message_id)
            ),
            rx.menu_item(
                rx.icon("git-branch", size=16, margin_right="0.5rem"),
                "Branch Conversation",
                on_click=RAGChatState.branch_conversation_from_message(message_id)
            ),
            rx.menu_item(
                rx.icon("trash-2", size=16, margin_right="0.5rem"),
                "Delete Message",
                color="red.400",
                on_click=RAGChatState.remove_message(message_id)
            )
        )
    )


def enhanced_message_bubble(message: ChatMessage) -> rx.Component:
    """Enhanced message bubble with advanced features"""
    is_user = message.message_type == MessageType.USER
    is_error = message.message_type == MessageType.ERROR
    is_system = message.message_type == MessageType.SYSTEM
    
    # Dynamic styling based on message type - using defaults for now
    alignment = "start"  # Will be handled in component
    bg_color = "gray.700"  # Will be handled with rx.cond
    
    return rx.box(
        rx.vstack(
            # Message header with metadata
            rx.hstack(
                rx.hstack(
                    rx.cond(
                        is_user,
                        rx.avatar(fallback="U", size="2", color_scheme="blue"),
                        rx.avatar(fallback="A", size="2", color_scheme="gray")
                    ),
                    rx.vstack(
                        rx.text(
                            message.message_type.title(),
                            font_size="sm",
                            font_weight="medium",
                            color="white"
                        ),
                        rx.text(
                            message.timestamp,
                            font_size="xs",
                            color="gray.300"
                        ),
                        spacing="0",
                        align="start"
                    ),
                    align="center",
                    spacing="2"
                ),
                
                rx.hstack(
                    # Performance indicators
                    rx.cond(
                        message.processing_time is not None,
                        rx.badge(
                            f"{message.processing_time:.1f}s",
                            color_scheme="green",
                            variant="subtle",
                            font_size="xs"
                        )
                    ),
                    rx.cond(
                        message.token_count is not None,
                        rx.badge(
                            f"{int(message.token_count)} tokens",
                            color_scheme="blue",
                            variant="subtle",
                            font_size="xs"
                        )
                    ),
                    message_actions_menu(message.id),
                    spacing="2",
                    align="center"
                ),
                
                justify="between",
                width="100%"
            ),
            
            # Message content
            rx.cond(
                message.is_loading,
                rx.hstack(
                    rx.spinner(size=16, color="blue.400"),
                    rx.text("Processing...", color="gray.300", font_style="italic"),
                    align="center",
                    spacing="2"
                ),
                rx.text(
                    message.content,
                    white_space="pre-wrap",
                    word_break="break-word",
                    line_height="1.6",
                    color="white"
                )
            ),
            
            # Error message display
            rx.cond(
                message.error_message is not None,
                rx.box(
                    rx.text(
                        f"Error: {message.error_message}",
                        font_size="sm",
                        color="red.300",
                        font_family="mono"
                    ),
                    bg="red.900",
                    p="2",
                    border_radius="md",
                    border="1px solid red.700",
                    mt="2"
                )
            ),
            
            # Retrieval statistics
            rx.cond(
                RAGChatState.show_retrieval_stats & (message.retrieval_stats is not None),
                rx.box(
                    rx.vstack(
                        rx.text("Retrieval Stats:", font_size="xs", font_weight="medium", color="gray.400"),
                        rx.hstack(
                            rx.text(f"Chunks: {message.retrieval_stats.get('chunks_retrieved', 0)}", font_size="xs"),
                            rx.text(f"Entities: {message.retrieval_stats.get('entities_found', 0)}", font_size="xs"),
                            rx.text(f"Avg Rel: {message.retrieval_stats.get('avg_relevance', 0):.1%}", font_size="xs"),
                            spacing="3",
                            wrap="wrap"
                        ),
                        spacing="1",
                        align="stretch"
                    ),
                    bg="gray.800",
                    p="2",
                    border_radius="md",
                    border="1px solid gray.600",
                    mt="2"
                )
            ),
            
            # Enhanced citations
            rx.cond(
                RAGChatState.show_citations & (message.citations.length() > 0),
                rx.vstack(
                    rx.divider(border_color="gray.600", my="3"),
                    rx.hstack(
                        rx.icon("quote", size=16, color="purple.400"),
                        rx.text(
                            f"Sources ({message.citations.length()})",
                            font_size="sm",
                            font_weight="medium",
                            color="purple.300"
                        ),
                        align="center",
                        spacing="2"
                    ),
                    rx.vstack(
                        *[advanced_citation_card(cite) for cite in message.citations],
                        spacing="3",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                )
            ),
            
            spacing="3",
            width="100%",
            align="stretch"
        ),
        
        bg=bg_color,
        p="4",
        border_radius="lg",
        max_width="85%",
        align_self="start",
        shadow="lg",
        border="1px solid gray.600",
        class_name="message-bubble",
        id=f"message-{message.id}"
    )


def conversation_export_modal() -> rx.Component:
    """Modal for exporting conversation in different formats"""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header("Export Conversation"),
                rx.modal_body(
                    rx.vstack(
                        rx.text("Choose export format:", font_weight="medium"),
                        rx.radio_group(
                            rx.vstack(
                                rx.radio("json", "JSON (Complete data)"),
                                rx.radio("markdown", "Markdown (Readable)"),
                                rx.radio("text", "Plain Text (Simple)"),
                                spacing="2",
                                align="start"
                            ),
                            value=RAGChatState.export_format,
                            on_change=lambda fmt: RAGChatState.update_settings(export_format=fmt),
                            color_scheme="blue"
                        ),
                        
                        rx.checkbox(
                            "Include citations and metadata",
                            is_checked=RAGChatState.include_citations_in_export,
                            on_change=lambda checked: RAGChatState.update_settings(include_citations_in_export=checked),
                            color_scheme="blue"
                        ),
                        
                        rx.text(
                            f"Conversation: {RAGChatState.conversation_metadata.title}",
                            font_size="sm",
                            color="gray.600"
                        ),
                        rx.text(
                            f"Messages: {RAGChatState.messages.length()} | Tokens: {RAGChatState.conversation_metadata.total_tokens}",
                            font_size="sm",
                            color="gray.600"
                        ),
                        
                        spacing="4",
                        align="stretch"
                    )
                ),
                rx.modal_footer(
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            variant="outline",
                            on_click=lambda: None  # Close modal logic would go here
                        ),
                        rx.button(
                            rx.icon("download", size=16, margin_right="0.5rem"),
                            "Export",
                            color_scheme="blue",
                            on_click=lambda: rx.download(
                                data=RAGChatState.export_conversation(),
                                filename=f"arete_conversation_{RAGChatState.current_conversation_id}.{RAGChatState.export_format}"
                            )
                        ),
                        spacing="3"
                    )
                )
            )
        ),
        size="6"
    )


def citation_detail_modal() -> rx.Component:
    """Detailed citation modal with full text and metadata"""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(
                    rx.hstack(
                        rx.icon("book-open", size=16, color="blue.400"),
                        "Citation Details",
                        align="center",
                        spacing="2"
                    )
                ),
                rx.modal_body(
                    rx.cond(
                        RAGChatState.selected_citation is not None,
                        rx.vstack(
                            # Citation metadata
                            rx.grid(
                                rx.stat(
                                    rx.stat_label("Source", color="gray.500"),
                                    rx.stat_number(
                                        RAGChatState.selected_citation["source"],
                                        font_size="6",
                                        color="blue.400"
                                    )
                                ),
                                rx.stat(
                                    rx.stat_label("Relevance", color="gray.500"),
                                    rx.stat_number(
                                        f"{RAGChatState.selected_citation['relevance_score']:.1%}",
                                        font_size="6",
                                        color="green.400"
                                    )
                                ),
                                rx.cond(
                                    RAGChatState.selected_citation.get("position") is not None,
                                    rx.stat(
                                        rx.stat_label("Position", color="gray.500"),
                                        rx.stat_number(
                                            RAGChatState.selected_citation["position"],
                                            font_size="6"
                                        )
                                    )
                                ),
                                columns="3",
                                spacing="4",
                                width="100%"
                            ),
                            
                            rx.divider(my="4"),
                            
                            # Full citation text
                            rx.box(
                                rx.text(
                                    RAGChatState.selected_citation.get("full_text", 
                                        RAGChatState.selected_citation.get("text", "")
                                    ),
                                    white_space="pre-wrap",
                                    line_height="1.6",
                                    font_size="sm"
                                ),
                                max_height="400px",
                                overflow_y="auto",
                                p="4",
                                bg="gray.50",
                                border_radius="md",
                                border="1px solid gray.200"
                            ),
                            
                            # Entities if available
                            rx.cond(
                                RAGChatState.selected_citation.get("entities"),
                                rx.vstack(
                                    rx.text("Related Entities:", font_weight="medium", font_size="sm"),
                                    rx.wrap(
                                        *[
                                            rx.badge(
                                                entity,
                                                color_scheme="purple",
                                                variant="outline"
                                            )
                                            for entity in RAGChatState.selected_citation.get("entities", [])
                                        ],
                                        spacing="2"
                                    ),
                                    spacing="2",
                                    align="stretch"
                                )
                            ),
                            
                            spacing="4",
                            align="stretch",
                            width="100%"
                        )
                    )
                ),
                rx.modal_footer(
                    rx.hstack(
                        rx.button(
                            rx.icon("copy", size=16, margin_right="0.5rem"),
                            "Copy Text",
                            variant="outline",
                            on_click=lambda: rx.set_clipboard(
                                RAGChatState.selected_citation.get("full_text",
                                    RAGChatState.selected_citation.get("text", "")
                                )
                            )
                        ),
                        rx.button(
                            "Close",
                            on_click=RAGChatState.close_citation_modal
                        ),
                        spacing="3"
                    )
                ),
                max_width="800px"
            )
        ),
        is_open=RAGChatState.citation_modal_open,
        size="9"
    )


def quick_actions_panel() -> rx.Component:
    """Quick action buttons for common philosophical queries"""
    sample_questions = [
        "What is virtue according to Plato?",
        "How does Socrates define knowledge?",
        "What is the allegory of the cave?",
        "Explain Aristotelian ethics",
        "What is the difference between sophia and phronesis?",
        "How does Plato view justice in the Republic?"
    ]
    
    return rx.cond(
        ~RAGChatState.has_messages,
        rx.box(
            rx.vstack(
                rx.heading("Explore Classical Philosophy", size="8", color="white", mb="4"),
                rx.text(
                    "Select a question below or ask your own to begin exploring ancient wisdom:",
                    color="gray.400",
                    text_align="center",
                    mb="6"
                ),
                rx.grid(
                    *[
                        rx.button(
                            question,
                            variant="outline",
                            color_scheme="blue",
                            size="2",
                            white_space="normal",
                            height="auto",
                            py="3",
                            px="4",
                            on_click=lambda q=question: RAGChatState.set_input(q),
                            text_align="left",
                            _hover={"bg": "blue.700", "border_color": "blue.500"}
                        )
                        for question in sample_questions
                    ],
                    columns=["1", "2", "3"],
                    spacing="3",
                    width="100%"
                ),
                spacing="4",
                align="center"
            ),
            p="6",
            border_radius="lg",
            bg="gray.800",
            border="1px solid gray.600"
        )
    )