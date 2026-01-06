"""
Action bar widget for selecting conversation modes.

Provides buttons to switch between different AI interaction modes
(Standard, Create, Explore, Code, Learn).
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject

from nanochat.state.conversation_mode import (
    ConversationMode,
    MODE_CONFIGS,
    get_mode_config
)


class ActionBar(Gtk.Box):
    """Action bar with mode selection buttons"""

    __gtype_name__ = "ActionBar"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(12)
        self.set_margin_bottom(12)

        self.current_mode = ConversationMode.STANDARD
        self.mode_buttons = {}

        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self):
        """Build action mode buttons"""
        for mode in [
            ConversationMode.CREATE,
            ConversationMode.EXPLORE,
            ConversationMode.CODE,
            ConversationMode.LEARN
        ]:
            config = get_mode_config(mode)

            btn = Gtk.ToggleButton()
            btn.add_css_class("action-mode-button")
            btn.set_tooltip_text(config.description)

            # Icon + Label box
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            # Icon
            icon = Gtk.Image.new_from_icon_name(config.icon)
            icon.set_pixel_size(16)
            box.append(icon)

            # Label
            label = Gtk.Label(label=config.name)
            box.append(label)

            btn.set_child(box)
            btn.connect("toggled", self._on_mode_toggled, mode)
            self.append(btn)

            self.mode_buttons[mode] = btn

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for modes"""
        # Shortcuts will be handled by main window
        # Ctrl+1: Standard
        # Ctrl+2: Create
        # Ctrl+3: Explore
        # Ctrl+4: Code
        # Ctrl+5: Learn
        pass

    def _on_mode_toggled(self, button, mode):
        """
        Handle mode button toggle.

        Ensures only one mode is active at a time and emits signal when mode changes.
        """
        if not button.get_active():
            # Don't allow deselecting all modes - if deselecting current mode, re-select it
            if self.current_mode == mode:
                button.set_active(True)
            return

        # Deselect other buttons
        for m, btn in self.mode_buttons.items():
            if m != mode:
                btn.set_active(False)

        old_mode = self.current_mode
        self.current_mode = mode

        # Emit signal with new mode
        self.emit("mode-changed", old_mode, mode)

    def get_current_mode(self) -> ConversationMode:
        """Get current active mode"""
        return self.current_mode

    def set_mode(self, mode: ConversationMode):
        """
        Set current mode programmatically.

        Args:
            mode: The mode to switch to
        """
        if mode in self.mode_buttons:
            self.mode_buttons[mode].set_active(True)
        elif mode == ConversationMode.STANDARD:
            # Deselect all mode buttons for standard mode
            for btn in self.mode_buttons.values():
                btn.set_active(False)
            old_mode = self.current_mode
            self.current_mode = ConversationMode.STANDARD
            self.emit("mode-changed", old_mode, mode)

    def get_current_config(self):
        """Get configuration for current mode"""
        return get_mode_config(self.current_mode)


# Register the mode-changed signal
GObject.signal_new(
    "mode-changed",
    ActionBar,
    GObject.SignalFlags.RUN_LAST,
    GObject.TYPE_NONE,
    (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)  # old_mode, new_mode
)
