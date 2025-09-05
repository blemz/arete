"""
Document viewer component for the Arete Reflex application.
"""

import reflex as rx
from ..reflex_app import AreteState


def document_list() -> rx.Component:
    """Document list sidebar component."""
    return rx.div(
        rx.div(
            rx.heading(
                "Classical Texts",
                size="md",
                font_weight="semibold",
                class_name="mb-4"
            ),
            rx.div(
                rx.div(
                    rx.text("📚", font_size="1.5rem", class_name="mr-3"),
                    rx.div(
                        rx.text("Plato's Apology", font_weight="semibold", class_name="mb-1"),
                        rx.text("First Book", class_name="text-sm opacity-70"),
                        class_name="flex-1"
                    ),
                    class_name="flex items-center p-3 rounded-lg hover:bg-base-200 cursor-pointer border border-base-300 mb-3",
                    on_click=lambda: AreteState.set_document("apology")
                ),
                rx.div(
                    rx.text("📖", font_size="1.5rem", class_name="mr-3"),
                    rx.div(
                        rx.text("Plato's Charmides", font_weight="semibold", class_name="mb-1"),
                        rx.text("Second Book", class_name="text-sm opacity-70"),
                        class_name="flex-1"
                    ),
                    class_name="flex items-center p-3 rounded-lg hover:bg-base-200 cursor-pointer border border-base-300 mb-3",
                    on_click=lambda: AreteState.set_document("charmides")
                ),
                rx.div(
                    rx.text("🏛️", font_size="1.5rem", class_name="mr-3"),
                    rx.div(
                        rx.text("More texts coming soon...", font_weight="medium", class_name="mb-1"),
                        rx.text("Republic, Ethics, Politics", class_name="text-sm opacity-70"),
                        class_name="flex-1"
                    ),
                    class_name="flex items-center p-3 rounded-lg opacity-50 border border-base-300 border-dashed",
                ),
                class_name="space-y-2"
            ),
            class_name="p-4"
        ),
        class_name="w-80 bg-base-100 border-r border-base-200 h-full overflow-auto"
    )


def document_content() -> rx.Component:
    """Document content display area."""
    return rx.div(
        rx.cond(
            AreteState.current_document != "",
            rx.div(
                rx.div(
                    rx.heading(
                        rx.cond(
                            AreteState.current_document == "apology",
                            "Plato's Apology",
                            rx.cond(
                                AreteState.current_document == "charmides",
                                "Plato's Charmides",
                                "Document"
                            )
                        ),
                        size="lg",
                        class_name="mb-2"
                    ),
                    rx.text(
                        "Classical philosophical dialogue",
                        class_name="text-sm opacity-70 mb-4"
                    ),
                    class_name="border-b border-base-200 pb-4 mb-6"
                ),
                rx.div(
                    rx.cond(
                        AreteState.current_document == "apology",
                        rx.div(
                            rx.text(
                                "The Apology of Socrates",
                                font_weight="bold",
                                class_name="mb-4 text-lg"
                            ),
                            rx.text(
                                "How you, O Athenians, have been affected by my accusers, I cannot tell; "
                                "but I know that they almost made me forget who I was—so persuasively did they speak; "
                                "and yet they have hardly uttered a word of truth. But of the many falsehoods told by them, "
                                "there was one which quite amazed me;—I mean when they said that you should be upon your guard "
                                "and not allow yourselves to be deceived by the force of my eloquence.",
                                class_name="mb-4 leading-relaxed prose"
                            ),
                            rx.text(
                                "They certainly did say this. But are they not ashamed of themselves for saying this? "
                                "For I am speaking the truth. Yes, Athenians, that is true, and it is the truth which I shall speak.",
                                class_name="mb-4 leading-relaxed prose"
                            )
                        ),
                        rx.cond(
                            AreteState.current_document == "charmides",
                            rx.div(
                                rx.text(
                                    "Charmides - On Temperance",
                                    font_weight="bold",
                                    class_name="mb-4 text-lg"
                                ),
                                rx.text(
                                    "Yesterday evening I returned from the army at Potidaea, and having been a long time away, "
                                    "I thought that I should like to go and look at my old haunts. So I went into the palaestra of Taureas, "
                                    "which is over against the temple of the Queen, and there I found a number of persons, "
                                    "most of whom I knew, but not all.",
                                    class_name="mb-4 leading-relaxed prose"
                                ),
                                rx.text(
                                    "My entrance caused some surprise, and several of them came up to me and saluted me; "
                                    "and Chaerephon, who is a kind of madman, started up and ran to me, seizing my hand, and saying: "
                                    "How did you escape, Socrates?—I should explain that the battle of Potidaea was fought not long before my departure.",
                                    class_name="mb-4 leading-relaxed prose"
                                )
                            ),
                            rx.div(
                                rx.text("Select a document from the sidebar to view its content."),
                                class_name="text-center opacity-70"
                            )
                        )
                    ),
                    class_name="prose max-w-none"
                ),
                class_name="p-6"
            ),
            rx.div(
                rx.div(
                    rx.text("📚", font_size="4rem", class_name="mb-4"),
                    rx.heading(
                        "Document Viewer",
                        size="xl",
                        class_name="mb-4"
                    ),
                    rx.text(
                        "Select a classical philosophical text from the sidebar to begin reading. "
                        "Navigate through passages, search for specific concepts, and explore citations.",
                        class_name="opacity-70 max-w-md text-center"
                    ),
                    class_name="text-center"
                ),
                class_name="flex items-center justify-center h-full"
            )
        ),
        class_name="flex-1 overflow-auto bg-base-200"
    )


def document_viewer() -> rx.Component:
    """Complete document viewer interface."""
    return rx.div(
        document_list(),
        document_content(),
        class_name="flex h-full"
    )