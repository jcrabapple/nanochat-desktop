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
        self.set_titlebar(self.header_bar)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.connect('new-chat', self.on_new_chat)
        self.sidebar.connect('conversation-selected', self.on_conversation_selected)
        self.sidebar.connect('conversation-deleted', self.on_conversation_deleted)
        self.sidebar.connect('conversation-renamed', self.on_conversation_renamed)
        self.sidebar.connect('settings-clicked', self.on_settings)
        main_box.append(self.sidebar)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(separator)

        # Chat view
        self.chat_view = ChatView()
        self.chat_view.connect('message-send', self.on_message_send)
        self.chat_view.connect('web-search-toggled', self.on_web_search_toggled)
        self.chat_view.connect('conversation-mode-changed', self.on_conversation_mode_changed)
        main_box.append(self.chat_view)

        # Show welcome screen
        self.chat_view.show_welcome()

        # Add keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts"""
        # Check for Ctrl modifier
        ctrl_pressed = (state & Gdk.ModifierType.CONTROL_MASK) != 0

        if ctrl_pressed:
            # Ctrl+N - New Chat
            if keyval == Gdk.KEY_n:
                self.on_new_chat(None)
                return True

            # Ctrl+W - Toggle Web Search
            elif keyval == Gdk.KEY_w:
                self.chat_view.toggle_web_search()
                return True

            # Ctrl+, - Settings
            elif keyval == Gdk.KEY_comma:
                self.on_settings(None)
                return True

            # Ctrl+Q - Quit
            elif keyval == Gdk.KEY_q:
                self.close()
                return True

        return False  # Let other handlers process the key

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

        print("DEBUG: Presenting settings dialog (GTK4 API)")
        dialog.present()
        print("DEBUG: Dialog presented (non-blocking)")

    def on_web_search_toggled(self, chat_view, enabled: bool):
        """Handle web search toggle from chat view"""
        self.web_search_enabled = enabled
        print(f"Web search: {'enabled' if enabled else 'disabled'}")

        # Save preference to current conversation
        if self.app_state and self.current_conversation_id:
            self.app_state.set_web_search_enabled(self.current_conversation_id, enabled)

    def on_conversation_mode_changed(self, chat_view, mode):
        """Handle conversation mode change from chat view"""
        from nanochat.state.conversation_mode import ConversationMode

        if self.app_state:
            self.app_state.set_conversation_mode(mode)
            print(f"Conversation mode changed to: {mode.value}")

    def on_new_chat(self, sidebar):
        """Handle new chat button"""
        print("New chat requested")

        # Create new conversation in database
        if self.app_state:
            new_id = self.app_state.create_conversation()
            self.current_conversation_id = new_id

            # Reload sidebar to show new conversation
            conversations = self.app_state.get_all_conversations()
            self.sidebar.populate_conversations(conversations)
            self.sidebar.set_active_conversation(new_id)

            # Reset web search to default (disabled) for new chat
            self.chat_view.set_web_search_enabled(False)
            self.web_search_enabled = False

        # Show welcome screen
        self.chat_view.show_welcome()

    def on_conversation_selected(self, sidebar, conversation_id):
        """Handle conversation selection"""
        print(f"Selected conversation: {conversation_id}")
        self.current_conversation_id = conversation_id
        # Load messages if controller exists
        if self.app_state:
            messages = self.app_state.get_conversation_messages(conversation_id)
            self.chat_view.clear()
            for msg in messages:
                self.chat_view.add_message(
                    msg['role'],
                    msg['content'],
                    msg.get('timestamp'),
                    msg.get('web_sources')  # Include web_sources
                )

            # Load web search preference for this conversation
            web_search_enabled = self.app_state.get_web_search_enabled(conversation_id)
            self.chat_view.set_web_search_enabled(web_search_enabled)
            self.web_search_enabled = web_search_enabled

    def on_conversation_deleted(self, sidebar, conversation_id):
        """Handle conversation deletion"""
        print(f"Deleting conversation: {conversation_id}")
        if self.app_state:
            success = self.app_state.delete_conversation(conversation_id)
            if success:
                # Clear chat view if deleted conversation was current
                if self.current_conversation_id == conversation_id:
                    self.current_conversation_id = None
                    self.chat_view.show_welcome()
                # Reload conversation list
                conversations = self.app_state.get_all_conversations()
                self.sidebar.populate_conversations(conversations)

    def on_conversation_renamed(self, sidebar, conversation_id, new_title):
        """Handle conversation rename"""
        print(f"Renaming conversation {conversation_id} to: {new_title}")
        if self.app_state:
            success = self.app_state.rename_conversation(conversation_id, new_title)
            if success:
                # Reload conversation list to show updated title
                conversations = self.app_state.get_all_conversations()
                self.sidebar.populate_conversations(conversations)
                # Keep the current conversation selected
                if self.current_conversation_id:
                    self.sidebar.set_active_conversation(self.current_conversation_id)

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
