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

        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        content.append(self.notebook)

        # API Configuration tab
        api_page = self.create_api_config_page(current_api_key, current_base_url, current_model)
        self.notebook.append_page(api_page, Gtk.Label(label="API Configuration"))

        # Modes tab
        modes_page = self.create_modes_page()
        self.notebook.append_page(modes_page, Gtk.Label(label="Modes"))

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

    def create_api_config_page(self, current_api_key: str, current_base_url: str, current_model: str):
        """Create API Configuration tab page"""
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        form_box.set_margin_start(12)
        form_box.set_margin_end(12)
        form_box.set_margin_top(12)
        form_box.set_margin_bottom(12)

        # API Key section
        api_key_frame = Gtk.Frame(label="API Configuration")
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
        self.base_url_entry.set_editable(False)  # Make read-only (NanoGPT API only)
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

        return form_box

    def create_modes_page(self):
        """Create Modes information tab page"""
        from nanochat.state.conversation_mode import ConversationMode, get_mode_config

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<big><b>Conversation Modes</b></big>")
        title_label.set_halign(Gtk.Align.START)
        main_box.append(title_label)

        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup(
            "NanoChat Desktop offers different conversation modes optimized for specific tasks. "
            "Each mode has custom prompts, temperature settings, and web search preferences."
        )
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.set_width_chars(60)
        main_box.append(desc_label)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(separator)

        # Modes list
        modes_scrolled = Gtk.ScrolledWindow()
        modes_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        modes_scrolled.set_vexpand(True)

        modes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        modes_scrolled.set_child(modes_box)
        main_box.append(modes_scrolled)

        # Add each mode
        for mode in [
            ConversationMode.STANDARD,
            ConversationMode.CREATE,
            ConversationMode.EXPLORE,
            ConversationMode.CODE,
            ConversationMode.LEARN
        ]:
            config = get_mode_config(mode)

            # Mode frame
            mode_frame = Gtk.Frame()
            mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            mode_box.set_margin_start(16)
            mode_box.set_margin_end(16)
            mode_box.set_margin_top(12)
            mode_box.set_margin_bottom(12)
            mode_frame.set_child(mode_box)

            # Mode header (icon + name + shortcut)
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            icon = Gtk.Image.new_from_icon_name(config.icon)
            icon.set_pixel_size(20)
            header_box.append(icon)

            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{config.name}</b>")
            name_label.set_halign(Gtk.Align.START)
            name_label.set_hexpand(True)
            header_box.append(name_label)

            # Show keyboard shortcut
            if mode != ConversationMode.STANDARD:
                shortcuts = {
                    ConversationMode.CREATE: "Ctrl+2",
                    ConversationMode.EXPLORE: "Ctrl+3",
                    ConversationMode.CODE: "Ctrl+4",
                    ConversationMode.LEARN: "Ctrl+5"
                }
                shortcut_label = Gtk.Label(label=shortcuts.get(mode, ""))
                shortcut_label.add_css_class("dim-label")
                header_box.append(shortcut_label)

            mode_box.append(header_box)

            # Mode description
            desc = Gtk.Label(label=config.description)
            desc.set_halign(Gtk.Align.START)
            desc.set_wrap(True)
            desc.set_width_chars(50)
            desc.add_css_class("dim-label")
            mode_box.append(desc)

            # Mode details
            details_text = f"Temperature: {config.temperature}"
            if config.enable_web_search:
                details_text += " | Web Search: Enabled"
            else:
                details_text += " | Web Search: Disabled"

            details = Gtk.Label(label=details_text)
            details.set_halign(Gtk.Align.START)
            details.add_css_class("dim-label")
            details.set_margin_top(4)
            mode_box.append(details)

            modes_box.append(mode_frame)

        return main_box

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
