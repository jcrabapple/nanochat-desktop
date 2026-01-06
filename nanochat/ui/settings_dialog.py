import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class SettingsDialog(Gtk.Dialog):
    """Settings dialog for API configuration"""

    def __init__(self, parent, current_api_key: str = "", current_base_url: str = "", current_model: str = ""):
        super().__init__(title="Settings")

        self.set_default_size(500, 400)
        self.set_modal(True)
        self.set_transient_for(parent)

        # Store parent reference for callbacks
        self.parent_window = parent

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

        # Add buttons to header bar
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", self.on_cancel_clicked)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_save_clicked)

        # Add buttons to dialog
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)

        # Connect response signal
        self.connect("response", self.on_response)

    def on_response(self, dialog, response):
        """Handle dialog response"""
        print(f"DEBUG: Dialog response signal received: {response}")
        if response == Gtk.ResponseType.OK:
            values = self.get_values()
            print(f"DEBUG: Saving config via callback")
            # Save configuration
            from nanochat.config import config
            config.save_to_file(
                values['api_key'],
                values['api_base_url'],
                values['model']
            )

            # Reinitialize API client if controller exists
            if hasattr(self.parent_window, 'app_state') and self.parent_window.app_state:
                self.parent_window.app_state.init_api_client(
                    values['api_key'],
                    values['api_base_url'],
                    values['model']
                )
            print("DEBUG: Configuration saved successfully")

        self.destroy()
        print("DEBUG: Dialog destroyed")

    def on_save_clicked(self, button):
        """Handle save button click"""
        self.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, button):
        """Handle cancel button click"""
        self.response(Gtk.ResponseType.CANCEL)

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
