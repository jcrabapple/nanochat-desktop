import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject


class HeaderBar(Gtk.HeaderBar):
    """Application header bar with controls"""

    __gsignals__ = {
        'settings-clicked': (GObject.SIGNAL_RUN_FIRST, None, ())
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

        # Apply styling
        self.add_css_class("headerbar")

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        print("DEBUG: Settings button clicked")
        self.emit('settings-clicked')
