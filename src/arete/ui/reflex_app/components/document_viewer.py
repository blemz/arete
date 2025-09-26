"""Document viewer component with interactive citation system for classical philosophical texts."""

import reflex as rx
from typing import List, Dict, Optional, Any
from ..state.document_state import DocumentState, Citation, DocumentMetadata
from ..state.ui_state import UIState


def document_header(document: DocumentMetadata) -> rx.Component:
    """Document header with metadata and controls."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.heading(document.title, size="lg", color="gray.900"),
                rx.text(f"By {document.author}", color="gray.600", font_weight="medium"),
                rx.hstack(
                    rx.text(f"{document.word_count:,} words", color="gray.500", font_size="sm"),
                    rx.text("•", color="gray.400"),
                    rx.text(document.date, color="gray.500", font_size="sm"),
                    rx.text("•", color="gray.400"),
                    rx.text(document.type, color="gray.500", font_size="sm"),
                    spacing="2"
                ),
                align_items="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("search"),
                    "Search",
                    variant="outline",
                    size="sm",
                    on_click=DocumentState.toggle_search
                ),
                rx.button(
                    rx.icon("bookmark"),
                    "Bookmarks",
                    variant="outline", 
                    size="sm",
                    on_click=DocumentState.toggle_bookmarks
                ),
                rx.button(
                    rx.icon("download"),
                    "Export",
                    variant="outline",
                    size="sm",
                    on_click=DocumentState.toggle_export_menu
                ),
                spacing="2"
            ),
            width="100%",
            align_items="start"
        ),
        padding="6",
        border_bottom="1px solid #e2e8f0",
        background="white"
    )


def search_panel() -> rx.Component:
    """Document search panel with highlighting controls."""
    return rx.cond(
        DocumentState.show_search,
        rx.box(
            rx.hstack(
                rx.input(
                    placeholder="Search document content...",
                    value=DocumentState.search_query,
                    on_change=DocumentState.set_search_query,
                    on_key_down=DocumentState.handle_search_keydown,
                    width="100%"
                ),
                rx.button(
                    rx.icon("search"),
                    on_click=DocumentState.search_document,
                    variant="solid",
                    color_scheme="blue"
                ),
                rx.button(
                    rx.icon("x"),
                    on_click=DocumentState.clear_search,
                    variant="outline"
                ),
                spacing="2",
                width="100%"
            ),
            rx.cond(
                DocumentState.search_results.length() > 0,
                rx.vstack(
                    rx.text(
                        f"{DocumentState.search_results.length()} results found",
                        color="gray.600",
                        font_size="sm"
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("chevron-up"),
                            "Previous",
                            size="sm",
                            variant="outline",
                            on_click=DocumentState.previous_search_result,
                            disabled=DocumentState.current_search_index == 0
                        ),
                        rx.text(
                            f"{DocumentState.current_search_index + 1} of {DocumentState.search_results.length()}",
                            font_size="sm",
                            color="gray.600"
                        ),
                        rx.button(
                            rx.icon("chevron-down"),
                            "Next", 
                            size="sm",
                            variant="outline",
                            on_click=DocumentState.next_search_result,
                            disabled=DocumentState.current_search_index >= DocumentState.search_results.length() - 1
                        ),
                        spacing="2"
                    ),
                    spacing="2",
                    align_items="start"
                )
            ),
            padding="4",
            border_bottom="1px solid #e2e8f0",
            background="gray.50"
        )
    )


def table_of_contents() -> rx.Component:
    """Table of contents navigation."""
    return rx.box(
        rx.vstack(
            rx.heading("Contents", size="sm", color="gray.700"),
            rx.foreach(
                DocumentState.current_document.sections,
                lambda section: rx.button(
                    section.title,
                    variant="ghost",
                    size="sm",
                    width="100%",
                    justify_content="start",
                    color="gray.600",
                    _hover={"background": "gray.100"},
                    on_click=lambda: DocumentState.jump_to_section(section.id)
                )
            ),
            spacing="1",
            align_items="start",
            width="100%"
        ),
        padding="4",
        width="250px",
        height="100%",
        border_right="1px solid #e2e8f0",
        overflow_y="auto"
    )


def citation_preview(citation: Citation) -> rx.Component:
    """Citation hover preview component."""
    return rx.tooltip(
        rx.text(
            citation.text,
            color="blue.600",
            text_decoration="underline",
            cursor="pointer",
            _hover={"color": "blue.800"},
            on_click=lambda: DocumentState.open_citation_modal(citation.id)
        ),
        label=rx.box(
            rx.text(citation.preview_text, font_size="sm"),
            rx.text(f"Source: {citation.source}", font_size="xs", color="gray.600"),
            max_width="300px",
            padding="2"
        ),
        placement="top"
    )


def citation_modal() -> rx.Component:
    """Detailed citation modal with full context."""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(
                    rx.hstack(
                        rx.heading("Citation Details", size="md"),
                        rx.spacer(),
                        rx.modal_close_button()
                    )
                ),
                rx.modal_body(
                    rx.vstack(
                        rx.text(
                            DocumentState.selected_citation.full_text,
                            line_height="1.6"
                        ),
                        rx.divider(),
                        rx.vstack(
                            rx.text("Source Information", font_weight="bold", color="gray.700"),
                            rx.text(f"Author: {DocumentState.selected_citation.author}"),
                            rx.text(f"Work: {DocumentState.selected_citation.work}"),
                            rx.text(f"Section: {DocumentState.selected_citation.section}"),
                            rx.text(f"Page: {DocumentState.selected_citation.page}"),
                            align_items="start",
                            spacing="1"
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.button(
                                rx.icon("chevron-left"),
                                "Previous Citation",
                                variant="outline",
                                size="sm",
                                on_click=DocumentState.previous_citation,
                                disabled=~DocumentState.has_previous_citation
                            ),
                            rx.button(
                                rx.icon("chevron-right"),
                                "Next Citation",
                                variant="outline", 
                                size="sm",
                                on_click=DocumentState.next_citation,
                                disabled=~DocumentState.has_next_citation
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.icon("copy"),
                                "Copy Citation",
                                variant="outline",
                                size="sm",
                                on_click=DocumentState.copy_citation
                            ),
                            rx.button(
                                rx.icon("share"),
                                "Share",
                                variant="outline",
                                size="sm", 
                                on_click=DocumentState.share_citation
                            ),
                            width="100%"
                        ),
                        spacing="4",
                        align_items="start",
                        width="100%"
                    )
                ),
                max_width="600px"
            )
        ),
        is_open=DocumentState.show_citation_modal,
        on_close=DocumentState.close_citation_modal
    )


def document_content() -> rx.Component:
    """Main document content with citation highlighting."""
    return rx.box(
        rx.foreach(
            DocumentState.current_document.paragraphs,
            lambda paragraph: rx.box(
                rx.foreach(
                    paragraph.content,
                    lambda content: rx.cond(
                        content.type == "citation",
                        citation_preview(content),
                        rx.text(
                            content.text,
                            as_="span",
                            background=rx.cond(
                                content.highlighted,
                                "yellow.200",
                                "transparent"
                            )
                        )
                    )
                ),
                margin_bottom="4",
                line_height="1.7",
                font_size="lg"
            )
        ),
        padding="6",
        max_width="800px",
        margin="0 auto"
    )


def reading_progress() -> rx.Component:
    """Reading progress indicator."""
    return rx.box(
        rx.progress(
            value=DocumentState.reading_progress,
            color_scheme="blue",
            size="sm"
        ),
        rx.text(
            f"{DocumentState.reading_progress}% complete",
            font_size="xs",
            color="gray.600",
            text_align="center",
            margin_top="1"
        ),
        position="fixed",
        top="0",
        left="0",
        right="0",
        background="white",
        border_bottom="1px solid #e2e8f0",
        padding="2",
        z_index="100"
    )


def bookmark_panel() -> rx.Component:
    """Bookmark management panel."""
    return rx.cond(
        DocumentState.show_bookmarks,
        rx.drawer(
            rx.drawer_overlay(
                rx.drawer_content(
                    rx.drawer_header(
                        rx.hstack(
                            rx.heading("Bookmarks", size="md"),
                            rx.spacer(),
                            rx.drawer_close_button()
                        )
                    ),
                    rx.drawer_body(
                        rx.vstack(
                            rx.foreach(
                                DocumentState.bookmarks,
                                lambda bookmark: rx.box(
                                    rx.vstack(
                                        rx.text(
                                            bookmark.title,
                                            font_weight="bold",
                                            color="gray.800"
                                        ),
                                        rx.text(
                                            bookmark.preview,
                                            color="gray.600",
                                            font_size="sm"
                                        ),
                                        rx.hstack(
                                            rx.button(
                                                "Go to",
                                                size="xs",
                                                variant="outline",
                                                on_click=lambda: DocumentState.jump_to_bookmark(bookmark.id)
                                            ),
                                            rx.button(
                                                rx.icon("trash"),
                                                size="xs",
                                                variant="outline",
                                                color_scheme="red",
                                                on_click=lambda: DocumentState.remove_bookmark(bookmark.id)
                                            ),
                                            spacing="2"
                                        ),
                                        align_items="start",
                                        spacing="2"
                                    ),
                                    padding="3",
                                    border="1px solid #e2e8f0",
                                    border_radius="md",
                                    width="100%"
                                )
                            ),
                            spacing="3",
                            width="100%"
                        )
                    ),
                    placement="right",
                    size="md"
                )
            ),
            is_open=DocumentState.show_bookmarks,
            on_close=DocumentState.close_bookmarks
        )
    )


def export_menu() -> rx.Component:
    """Document export options menu."""
    return rx.cond(
        DocumentState.show_export_menu,
        rx.menu(
            rx.menu_button(
                rx.button(
                    rx.icon("download"),
                    "Export",
                    variant="outline",
                    size="sm"
                )
            ),
            rx.menu_list(
                rx.menu_item(
                    rx.icon("file-text"),
                    "Plain Text",
                    on_click=lambda: DocumentState.export_document("txt")
                ),
                rx.menu_item(
                    rx.icon("file"),
                    "PDF",
                    on_click=lambda: DocumentState.export_document("pdf")
                ),
                rx.menu_item(
                    rx.icon("book"),
                    "EPUB",
                    on_click=lambda: DocumentState.export_document("epub")
                ),
                rx.menu_item(
                    rx.icon("code"),
                    "HTML",
                    on_click=lambda: DocumentState.export_document("html")
                )
            )
        )
    )


def document_viewer() -> rx.Component:
    """Complete document viewer component."""
    return rx.cond(
        DocumentState.current_document.id != "",
        rx.box(
            reading_progress(),
            rx.hstack(
                table_of_contents(),
                rx.vstack(
                    document_header(DocumentState.current_document),
                    search_panel(),
                    rx.box(
                        document_content(),
                        flex="1",
                        overflow_y="auto",
                        height="calc(100vh - 200px)"
                    ),
                    spacing="0",
                    width="100%"
                ),
                spacing="0",
                width="100%",
                height="100vh"
            ),
            citation_modal(),
            bookmark_panel(),
            export_menu(),
            width="100%"
        ),
        rx.center(
            rx.vstack(
                rx.icon("book-open", size="4xl", color="gray.400"),
                rx.heading("Select a Document", color="gray.600"),
                rx.text("Choose a philosophical text to begin reading", color="gray.500"),
                spacing="4"
            ),
            height="50vh"
        )
    )


def document_library() -> rx.Component:
    """Document library browser."""
    return rx.box(
        rx.vstack(
            rx.heading("Classical Philosophical Texts", size="xl", margin_bottom="6"),
            rx.input(
                placeholder="Search library...",
                value=DocumentState.library_search,
                on_change=DocumentState.set_library_search,
                margin_bottom="4",
                width="100%"
            ),
            rx.grid(
                rx.foreach(
                    DocumentState.filtered_documents,
                    lambda doc: rx.box(
                        rx.vstack(
                            rx.heading(doc.title, size="md", color="gray.800"),
                            rx.text(f"by {doc.author}", color="gray.600", font_weight="medium"),
                            rx.text(doc.description, color="gray.500", font_size="sm"),
                            rx.hstack(
                                rx.text(f"{doc.word_count:,} words", color="gray.400", font_size="xs"),
                                rx.text(doc.date, color="gray.400", font_size="xs"),
                                spacing="4"
                            ),
                            rx.button(
                                "Open Document",
                                on_click=lambda: DocumentState.load_document(doc.id),
                                width="100%",
                                margin_top="3"
                            ),
                            spacing="2",
                            align_items="start"
                        ),
                        padding="4",
                        border="1px solid #e2e8f0",
                        border_radius="md",
                        _hover={"border_color": "blue.300", "shadow": "md"},
                        cursor="pointer"
                    )
                ),
                template_columns="repeat(auto-fit, minmax(300px, 1fr))",
                gap="4",
                width="100%"
            ),
            spacing="4",
            align_items="start"
        ),
        padding="6"
    )