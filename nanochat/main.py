import logging
import threading
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
from nanochat.ui.main_window import MainWindow
from nanochat.state.app_state import ApplicationState
from nanochat.config import config
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NanoChatApplication(Gtk.Application):
    """Main application class"""

    def __init__(self):
        super().__init__(application_id='com.nanochat.desktop')
        self.app_state = None
        self.window = None

    def do_activate(self):
        """Handle application activation"""
        if not self.window:
            # Create window
            self.window = MainWindow(self)
            self.window.present()

            # Initialize application state
            self.app_state = ApplicationState()

            # Set controllers on window
            self.window.set_app_controllers(self, self.app_state)

            # Check if configured
            if not config.is_configured():
                logger.info("API key not configured, showing settings")
                GLib.timeout_add(500, self.show_settings_on_startup)
            else:
                # Initialize API client
                self.app_state.init_api_client()

                # Load conversations
                self.load_conversations()

                logger.info("Application activated successfully")

    def show_settings_on_startup(self):
        """Show settings dialog on first run"""
        # Trigger settings dialog
        self.window.on_settings(None)
        return False  # Don't repeat

    def load_conversations(self):
        """Load conversations into sidebar"""
        try:
            conversations = self.app_state.get_all_conversations()
            self.window.sidebar.populate_conversations(conversations)
            logger.info(f"Loaded {len(conversations)} conversations")
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")

    def send_message_async(self, message: str, use_web_search: bool = False):
        """Send message asynchronously (run from UI thread)"""
        # Run async function in a background thread
        thread = threading.Thread(
            target=self._run_async_task,
            args=(message, use_web_search)
        )
        thread.daemon = True
        thread.start()

    def _run_async_task(self, message: str, use_web_search: bool):
        """Run async task in background thread"""
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the async send_message function
            loop.run_until_complete(
                self._send_message_task(message, use_web_search)
            )
        finally:
            loop.close()

    async def _send_message_task(self, message: str, use_web_search: bool):
        """Async task for sending messages"""
        try:
            # Stream response
            async for role, content in self.app_state.send_message(message, use_web_search):
                # Update UI on main thread
                GLib.idle_add(self._update_chat_with_message, role, content)

            # Reload conversations (updated timestamp)
            GLib.idle_add(self.load_conversations)

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            # Show error in UI
            GLib.idle_add(self._show_error, str(e))

    def _update_chat_with_message(self, role: str, content: str):
        """Update chat view with message (called on main thread)"""
        self.window.chat_view.add_message(role, content)
        return False  # Don't repeat

    def _show_error(self, error_message: str):
        """Show error message to user"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(error_message)
        response = dialog.run()
        dialog.destroy()
        return False  # Don't repeat


def main():
    """Application entry point"""
    app = NanoChatApplication()
    app.run(None)


if __name__ == "__main__":
    main()
