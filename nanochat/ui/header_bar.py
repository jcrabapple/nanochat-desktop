import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject


class HeaderBar(Gtk.HeaderBar):
    """Application header bar with controls"""

    def __init__(self):
        super().__init__()

        # Header bar properties
        self.set_show_title_buttons(True)

        # Title widget
        title_label = Gtk.Label(label="NanoChat Desktop")
        title_label.add_css_class("title")
        self.set_title_widget(title_label)

        # Apply styling
        self.add_css_class("headerbar")
