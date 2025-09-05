"""Advanced layout controls and configuration interface."""

import reflex as rx
from typing import Dict, Any, List
from ...state.layout_state import LayoutState
from .panel_manager import LayoutPresetManager


class LayoutControlPanel(rx.Component):
    """Advanced layout control panel with presets and configuration."""
    
    def render(self) -> rx.Component:
        return rx.box(
            # Main layout controls
            rx.box(
                rx.heading(
                    "Layout Controls",
                    size="sm",
                    class_name="text-gray-700 dark:text-gray-300 mb-3"
                ),
                
                # Primary layout mode buttons
                rx.button_group(
                    rx.button(
                        rx.icon("message-square", size=16),
                        rx.text("Chat", class_name="ml-2"),
                        on_click=lambda: LayoutState.set_layout_mode("chat"),
                        variant=rx.cond(
                            LayoutState.layout_mode == "chat",
                            "solid",
                            "outline"
                        ),
                        size="sm",
                        class_name="flex items-center px-3 py-2"
                    ),
                    rx.button(
                        rx.icon("columns", size=16),
                        rx.text("Split", class_name="ml-2"),
                        on_click=lambda: LayoutState.set_layout_mode("split"),
                        variant=rx.cond(
                            LayoutState.layout_mode == "split",
                            "solid",
                            "outline"
                        ),
                        size="sm",
                        class_name="flex items-center px-3 py-2"
                    ),
                    rx.button(
                        rx.icon("file-text", size=16),
                        rx.text("Document", class_name="ml-2"),
                        on_click=lambda: LayoutState.set_layout_mode("document"),
                        variant=rx.cond(
                            LayoutState.layout_mode == "document",
                            "solid",
                            "outline"
                        ),
                        size="sm",
                        class_name="flex items-center px-3 py-2"
                    ),
                    class_name="flex w-full"
                ),
                
                class_name="mb-4"
            ),
            
            # Split view configuration
            rx.cond(
                LayoutState.layout_mode == "split",
                rx.box(
                    rx.heading(
                        "Split Configuration",
                        size="xs",
                        class_name="text-gray-600 dark:text-gray-400 mb-2"
                    ),
                    
                    # Orientation toggle
                    rx.box(
                        rx.text("Orientation:", class_name="text-sm text-gray-600 dark:text-gray-400 mb-1"),
                        rx.button_group(
                            rx.button(
                                rx.icon("split-square-horizontal", size=14),
                                rx.text("Horizontal", class_name="ml-1 text-xs"),
                                on_click=lambda: setattr(LayoutState, "split_orientation", "horizontal"),
                                variant=rx.cond(
                                    LayoutState.split_orientation == "horizontal",
                                    "solid",
                                    "outline"
                                ),
                                size="xs",
                                class_name="flex items-center"
                            ),
                            rx.button(
                                rx.icon("split-square-vertical", size=14),
                                rx.text("Vertical", class_name="ml-1 text-xs"),
                                on_click=lambda: setattr(LayoutState, "split_orientation", "vertical"),
                                variant=rx.cond(
                                    LayoutState.split_orientation == "vertical",
                                    "solid",
                                    "outline"
                                ),
                                size="xs",
                                class_name="flex items-center"
                            ),
                            class_name="flex w-full"
                        ),
                        class_name="mb-3"
                    ),
                    
                    # Panel size controls
                    rx.cond(
                        LayoutState.split_orientation == "horizontal",
                        rx.box(
                            rx.text("Chat Panel Width:", class_name="text-sm text-gray-600 dark:text-gray-400 mb-1"),
                            rx.slider(
                                value=LayoutState.chat_panel_width,
                                min=20,
                                max=80,
                                step=5,
                                on_value_change=LayoutState.set_chat_panel_width,
                                class_name="w-full"
                            ),
                            rx.text(
                                f"{LayoutState.chat_panel_width}%",
                                class_name="text-xs text-gray-500 text-center mt-1"
                            ),
                            class_name="mb-3"
                        ),
                        rx.box(
                            rx.text("Chat Panel Height:", class_name="text-sm text-gray-600 dark:text-gray-400 mb-1"),
                            rx.slider(
                                value=LayoutState.chat_panel_height,
                                min=20,
                                max=80,
                                step=5,
                                on_value_change=LayoutState.set_chat_panel_height,
                                class_name="w-full"
                            ),
                            rx.text(
                                f"{LayoutState.chat_panel_height}%",
                                class_name="text-xs text-gray-500 text-center mt-1"
                            ),
                            class_name="mb-3"
                        )
                    ),
                    
                    # Panel expansion controls
                    rx.box(
                        rx.text("Quick Actions:", class_name="text-sm text-gray-600 dark:text-gray-400 mb-2"),
                        rx.button_group(
                            rx.button(
                                rx.icon("maximize", size=12),
                                rx.text("Expand Chat", class_name="ml-1 text-xs"),
                                on_click=LayoutState.toggle_chat_expanded,
                                variant=rx.cond(
                                    LayoutState.chat_panel_expanded,
                                    "solid",
                                    "outline"
                                ),
                                size="xs",
                                class_name="flex items-center"
                            ),
                            rx.button(
                                rx.icon("maximize", size=12),
                                rx.text("Expand Doc", class_name="ml-1 text-xs"),
                                on_click=LayoutState.toggle_document_expanded,
                                variant=rx.cond(
                                    LayoutState.document_panel_expanded,
                                    "solid",
                                    "outline"
                                ),
                                size="xs",
                                class_name="flex items-center"
                            ),
                            class_name="flex gap-1 w-full"
                        ),
                        class_name="mb-4"
                    ),
                    
                    class_name="border-t border-gray-200 dark:border-gray-700 pt-4"
                ),
                rx.box()
            ),
            
            # Layout presets
            rx.box(
                rx.heading(
                    "Layout Presets",
                    size="xs",
                    class_name="text-gray-600 dark:text-gray-400 mb-2"
                ),
                
                rx.box(
                    *[
                        self._render_preset_button(preset)
                        for preset in LayoutPresetManager.get_preset_list()
                    ],
                    class_name="grid grid-cols-2 gap-2"
                ),
                
                class_name="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4"
            ),
            
            # Advanced settings
            rx.box(
                rx.heading(
                    "Advanced Settings",
                    size="xs",
                    class_name="text-gray-600 dark:text-gray-400 mb-2"
                ),
                
                rx.button_group(
                    rx.button(
                        rx.icon("refresh-ccw", size=12),
                        rx.text("Reset", class_name="ml-1 text-xs"),
                        on_click=LayoutState.reset_layout_preferences,
                        variant="outline",
                        size="xs",
                        class_name="flex items-center"
                    ),
                    rx.button(
                        rx.icon("save", size=12),
                        rx.text("Save", class_name="ml-1 text-xs"),
                        on_click=LayoutState.save_layout_preferences,
                        variant="outline",
                        size="xs",
                        class_name="flex items-center"
                    ),
                    class_name="flex gap-1"
                ),
                
                class_name="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4"
            ),
            
            class_name="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 w-80"
        )
    
    def _render_preset_button(self, preset: Dict[str, str]) -> rx.Component:
        """Render a preset button."""
        return rx.button(
            rx.box(
                rx.text(
                    preset["name"].title(),
                    class_name="text-xs font-medium"
                ),
                rx.text(
                    preset["description"],
                    class_name="text-xs text-gray-500 mt-1"
                ),
                class_name="text-left"
            ),
            on_click=lambda: LayoutPresetManager.apply_preset(preset["name"]),
            variant="outline",
            size="sm",
            class_name="p-2 h-auto w-full"
        )


class MiniLayoutControls(rx.Component):
    """Compact layout controls for minimal UI footprint."""
    
    def render(self) -> rx.Component:
        return rx.box(
            rx.button_group(
                rx.button(
                    rx.icon("message-square", size=16),
                    on_click=lambda: LayoutState.set_layout_mode("chat"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "chat",
                        "solid",
                        "ghost"
                    ),
                    size="sm",
                    aria_label="Chat mode"
                ),
                rx.button(
                    rx.icon("columns", size=16),
                    on_click=lambda: LayoutState.set_layout_mode("split"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "split",
                        "solid",
                        "ghost"
                    ),
                    size="sm",
                    aria_label="Split mode"
                ),
                rx.button(
                    rx.icon("file-text", size=16),
                    on_click=lambda: LayoutState.set_layout_mode("document"),
                    variant=rx.cond(
                        LayoutState.layout_mode == "document",
                        "solid",
                        "ghost"
                    ),
                    size="sm",
                    aria_label="Document mode"
                ),
                rx.cond(
                    LayoutState.layout_mode == "split",
                    rx.button(
                        rx.icon(
                            rx.cond(
                                LayoutState.split_orientation == "horizontal",
                                "split-square-vertical",
                                "split-square-horizontal"
                            ),
                            size=16
                        ),
                        on_click=LayoutState.toggle_split_orientation,
                        variant="ghost",
                        size="sm",
                        aria_label="Toggle split orientation"
                    ),
                    rx.box()
                ),
                class_name="flex"
            ),
            class_name="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-1"
        )


class ResponsiveLayoutIndicator(rx.Component):
    """Indicator showing current responsive layout state."""
    
    def render(self) -> rx.Component:
        return rx.box(
            rx.cond(
                LayoutState.is_mobile,
                rx.box(
                    rx.icon("smartphone", size=12, class_name="text-blue-500"),
                    rx.text("Mobile", class_name="text-xs text-blue-500 ml-1"),
                    class_name="flex items-center"
                ),
                rx.cond(
                    LayoutState.is_tablet,
                    rx.box(
                        rx.icon("tablet", size=12, class_name="text-green-500"),
                        rx.text("Tablet", class_name="text-xs text-green-500 ml-1"),
                        class_name="flex items-center"
                    ),
                    rx.box(
                        rx.icon("monitor", size=12, class_name="text-purple-500"),
                        rx.text("Desktop", class_name="text-xs text-purple-500 ml-1"),
                        class_name="flex items-center"
                    )
                )
            ),
            class_name="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs"
        )


def layout_control_panel() -> rx.Component:
    """Create layout control panel."""
    return LayoutControlPanel().render()


def mini_layout_controls() -> rx.Component:
    """Create mini layout controls."""
    return MiniLayoutControls().render()


def responsive_layout_indicator() -> rx.Component:
    """Create responsive layout indicator."""
    return ResponsiveLayoutIndicator().render()