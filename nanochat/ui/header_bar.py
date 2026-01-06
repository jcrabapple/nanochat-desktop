import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject


class HeaderBar(Gtk.HeaderBar):
    """Application header bar with controls"""

    __gsignals__ = {
        'settings-clicked': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'web-search-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
    }

    def __init__(self):
        super().__init__()

        # Header bar properties
        self.set_show_title_buttons(True)

        # Title widget
        title_label = Gtk.Label(label="NanoChat Desktop")
        title_label.add_css_class("title")
        self.set_title_widget(title_label)

        # Settings button (left side)
        self.settings_button = Gtk.Button(label="Settings")
        self.settings_button.set_tooltip_text("Settings")
        self.settings_button.connect("clicked", self.on_settings_clicked)
        self.pack_start(self.settings_button)

        # Web search toggle (right side)
        self.web_search_toggle = Gtk.ToggleButton(label="Web Search")
        self.web_search_toggle.set_tooltip_text("Enable Web Search")
        self.web_search_toggle.connect("toggled", self.on_web_search_toggled)
        self.pack_end(self.web_search_toggle)

        # Apply styling
        self.add_css_class("headerbar")

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        self.emit('settings-clicked')

    def on_web_search_toggled(self, button):
        """Handle web search toggle"""
        is_active = button.get_active()

        if is_active:
            button.add_css_class("suggested-action")
            button.set_tooltip_text("Web Search Enabled")
        else:
            button.remove_css_class("suggested-action")
            button.set_tooltip_text("Enable Web Search")

        self.emit('web-search-toggled', is_active)

    def set_web_search_enabled(self, enabled: bool):
        """Programmatically set web search state"""
        self.web_search_toggle.set_active(enabled)

    def get_web_search_enabled(self) -> bool:
        """Get current web search state"""
        return self.web_search_toggle.get_active()
