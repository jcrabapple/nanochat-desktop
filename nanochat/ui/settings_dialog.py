import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class SettingsDialog(Gtk.Dialog):
    """Settings dialog for API configuration"""

    def __init__(self, parent, current_api_key: str = "", current_base_url: str = "", current_model: str = ""):
        super().__init__(
            title="Settings",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                "Cancel", Gtk.ResponseType.CANCEL,
                "Save", Gtk.ResponseType.OK
            )
        )

        self.set_default_size(500, 400)

        # Main content
        content = self.get_content_area()
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)

        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.append(form_box)

        # API Key section
        api_key_frame = Gtk.Frame(label="API Configuration")
        api_key_frame.set_margin_bottom(12)
        form_box.append(api_key_frame)

        api_key_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        api_key_box.set_margin_start(12)
        api_key_box.set_margin_end(12)
        api_key_box.set_margin_top(12)
        api_key_box.set_margin_bottom(12)
        api_key_frame.set_child(api_key_box)

        # API Key input
        api_key_label = Gtk.Label(label="API Key:")
        api_key_label.set_halign(Gtk.Align.START)
        api_key_box.append(api_key_label)

        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_text(current_api_key)
        self.api_key_entry.set_visibility(False)  # Mask password
        self.api_key_entry.set_placeholder_text("Enter your NanoGPT API key")
        api_key_box.append(self.api_key_entry)

        # Show/hide API key toggle
        show_api_key = Gtk.CheckButton(label="Show API key")
        show_api_key.connect("toggled", self.on_show_api_key)
        api_key_box.append(show_api_key)

        # Base URL input
        base_url_label = Gtk.Label(label="API Base URL:")
        base_url_label.set_halign(Gtk.Align.START)
        api_key_box.append(base_url_label)

        self.base_url_entry = Gtk.Entry()
        self.base_url_entry.set_text(current_base_url or "https://nano-gpt.com/api")
        api_key_box.append(self.base_url_entry)

        # Model input
        model_label = Gtk.Label(label="Model:")
        model_label.set_halign(Gtk.Align.START)
        api_key_box.append(model_label)

        self.model_entry = Gtk.Entry()
        self.model_entry.set_text(current_model or "gpt-4")
        api_key_box.append(self.model_entry)

        # Instructions
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        info_label = Gtk.Label(label="Get your API key from https://nano-gpt.com")
        info_label.add_css_class("dim-label")
        info_label.set_wrap(True)
        info_box.append(info_label)
        form_box.append(info_box)

    def on_show_api_key(self, checkbox):
        """Toggle API key visibility"""
        self.api_key_entry.set_visibility(checkbox.get_active())

    def get_values(self):
        """Get form values"""
        return {
            'api_key': self.api_key_entry.get_text(),
            'api_base_url': self.base_url_entry.get_text(),
            'model': self.model_entry.get_text()
        }
