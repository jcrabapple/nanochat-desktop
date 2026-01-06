import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from nanochat.ui.header_bar import HeaderBar
from nanochat.ui.sidebar import Sidebar
from nanochat.ui.chat_view import ChatView
from nanochat.ui.settings_dialog import SettingsDialog


class MainWindow(Gtk.ApplicationWindow):
    """Main application window"""

    def __init__(self, app):
        super().__init__(application=app)

        # Window properties
        self.set_title("NanoChat Desktop")
        self.set_default_size(1200, 800)
        self.set_size_request(800, 600)

        # Load CSS
        self.load_css()

        # Create UI components
        self.create_ui()

        # State
        self.current_conversation_id = None
        self.web_search_enabled = False
        self.app = None  # NanoChatApplication
        self.app_state = None  # ApplicationState

    def load_css(self):
        """Load application CSS styling"""
        # Load CSS file
        css_file = os.path.join(
            os.path.dirname(__file__),
            'resources',
            'style.css'
        )

        if os.path.exists(css_file):
            with open(css_file, 'r') as f:
                css = f.read()

            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())

            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def create_ui(self):
        """Create main UI layout"""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(main_box)

        # Header bar
        self.header_bar = HeaderBar()
        self.header_bar.connect('settings-clicked', self.on_settings)
        self.header_bar.connect('web-search-toggled', self.on_web_search_toggled)
        self.set_titlebar(self.header_bar)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.connect('new-chat', self.on_new_chat)
        self.sidebar.connect('conversation-selected', self.on_conversation_selected)
        main_box.append(self.sidebar)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(separator)

        # Chat view
        self.chat_view = ChatView()
        self.chat_view.connect('message-send', self.on_message_send)
        main_box.append(self.chat_view)

        # Show welcome screen
        self.chat_view.show_welcome()

    def set_app_controllers(self, app, app_state):
        """Set application and application state controllers"""
        self.app = app
        self.app_state = app_state

    def on_settings(self, header_bar):
        """Show settings dialog"""
        print("DEBUG: on_settings handler called")
        from nanochat.config import config

        dialog = SettingsDialog(
            parent=self,
            current_api_key=config.api_key,
            current_base_url=config.api_base_url,
            current_model=config.model
        )

        print("DEBUG: Showing settings dialog")
        response = dialog.run()
        print(f"DEBUG: Dialog response = {response}")

        if response == Gtk.ResponseType.OK:
            values = dialog.get_values()
            print(f"DEBUG: Saving config: api_key={'*' * len(values['api_key']) if values['api_key'] else 'None'}")
            # Save configuration
            config.save_to_file(
                values['api_key'],
                values['api_base_url'],
                values['model']
            )
            # Reinitialize API client if controller exists
            if self.app_state:
                self.app_state.init_api_client(
                    values['api_key'],
                    values['api_base_url'],
                    values['model']
                )
            print("DEBUG: Configuration saved successfully")

        dialog.destroy()
        print("DEBUG: Dialog destroyed")

    def on_web_search_toggled(self, header_bar, enabled: bool):
        """Handle web search toggle"""
        self.web_search_enabled = enabled
        print(f"Web search: {'enabled' if enabled else 'disabled'}")

    def on_new_chat(self, sidebar):
        """Handle new chat button"""
        print("New chat requested")
        self.chat_view.show_welcome()
        self.current_conversation_id = None

    def on_conversation_selected(self, sidebar, conversation_id):
        """Handle conversation selection"""
        print(f"Selected conversation: {conversation_id}")
        self.current_conversation_id = conversation_id
        # Load messages if controller exists
        if self.app_state:
            messages = self.app_state.get_conversation_messages(conversation_id)
            self.chat_view.clear()
            for msg in messages:
                self.chat_view.add_message(msg['role'], msg['content'], msg.get('timestamp'))

    def on_message_send(self, chat_view, message: str):
        """Handle message send"""
        print(f"DEBUG: on_message_send called with message: '{message[:50]}...'")
        print(f"DEBUG: app = {self.app}, web_search_enabled = {self.web_search_enabled}")
        if self.app:
            print("DEBUG: Calling app.send_message_async")
            self.app.send_message_async(
                message,
                self.web_search_enabled
            )
        else:
            print("DEBUG: No app controller available")
