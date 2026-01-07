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
        self.current_assistant_message = ""  # Accumulate streaming response
        self.current_message_row = None  # Track the message row widget

        # Force dark theme
        self._setup_dark_theme()

    def _setup_dark_theme(self):
        """Configure application to use dark theme"""
        # Set prefer-dark-theme for this application
        Gtk.Settings.get_default().set_property('gtk-application-prefer-dark-theme', True)

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

                # Fetch models on startup (in background)
                self._fetch_models_on_startup()

                # Load conversations
                self.load_conversations()

                logger.info("Application activated successfully")

    def show_settings_on_startup(self):
        """Show settings dialog on first run"""
        # Trigger settings dialog
        self.window.on_settings(None)
        return False  # Don't repeat

    def load_conversations(self):
        """Load conversations and projects into sidebar"""
        try:
            # Load conversations first (so project counts are correct)
            conversations = self.app_state.get_all_conversations()
            self.window.sidebar.populate_conversations(conversations)
            logger.info(f"Loaded {len(conversations)} conversations")

            # Then load projects (with correct counts)
            projects = self.app_state.get_all_projects()
            self.window.sidebar.populate_projects(projects)
            logger.info(f"Loaded {len(projects)} projects")
        except Exception as e:
            logger.error(f"Failed to load sidebar data: {e}")

    def _fetch_models_on_startup(self):
        """Fetch models on startup if cache is empty"""
        # Check if we have cached models
        cached_models = self.app_state.get_cached_models()

        if cached_models:
            logger.info(f"Using {len(cached_models)} cached models")
            return

        # No cache, fetch in background
        logger.info("No model cache found, fetching from API...")

        def fetch_models_thread():
            """Run model fetching in background thread"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                models = loop.run_until_complete(self.app_state.fetch_models())
                logger.info(f"Successfully fetched and cached {len(models)} models")
            except Exception as e:
                logger.warning(f"Failed to fetch models on startup: {e}")
            finally:
                loop.close()

        # Start background thread
        thread = threading.Thread(target=fetch_models_thread, daemon=True)
        thread.start()

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
        # Reset accumulated message
        self.current_assistant_message = ""
        self.current_web_sources = None
        first_chunk = True

        # Create generator and ensure it's properly closed
        gen = self.app_state.send_message(message, use_web_search)

        try:
            # Stream response (now returns 3-tuple: role, content, web_sources)
            async for role, content, web_sources in gen:
                if role == 'user':
                    # User message - add immediately
                    GLib.idle_add(self._update_chat_with_message, role, content, None, False)

                    # Show typing indicator AFTER user message is added
                    GLib.idle_add(self.window.chat_view.show_typing_indicator)
                elif role == 'assistant':
                    # Hide typing indicator on first assistant chunk
                    if first_chunk:
                        GLib.idle_add(self.window.chat_view.hide_typing_indicator)

                    # Assistant message
                    if content:
                        # Accumulate content chunks
                        self.current_assistant_message += content
                        if first_chunk:
                            # Create message row on first chunk
                            GLib.idle_add(self._update_chat_with_message, role, self.current_assistant_message, None, False)
                            first_chunk = False
                        else:
                            # Update existing message row
                            GLib.idle_add(self._update_chat_with_message, role, self.current_assistant_message, None, True)

                    if web_sources:
                        # Store sources for final update
                        self.current_web_sources = web_sources
                        # Add/update sources in UI
                        GLib.idle_add(self._update_chat_with_message, role, None, self.current_web_sources, True)

            # Reload conversations (updated timestamp)
            GLib.idle_add(self.load_conversations)

            # Auto-generate title for new conversations (first exchange)
            if self.app_state.current_conversation_id:
                messages = self.app_state.get_conversation_messages(
                    self.app_state.current_conversation_id
                )
                # Check if this is the first exchange (exactly 2 messages)
                if len(messages) == 2:
                    logger.info("First exchange complete, generating title...")
                    await self._generate_title_async()

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            # Show error in UI
            GLib.idle_add(self._show_error, str(e))
        finally:
            # Ensure typing indicator is hidden
            GLib.idle_add(self.window.chat_view.hide_typing_indicator)
            # Close the generator to clean up resources
            try:
                await gen.aclose()
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")

    def _update_chat_with_message(self, role: str, content: str = None, web_sources: list = None, update_last: bool = False):
        """Update chat view with message (called on main thread)"""
        self.window.chat_view.add_message(
            role=role,
            content=content or "",
            web_sources=web_sources,
            update_last=update_last
        )
        return False  # Don't repeat

    def _show_error(self, error_message: str):
        """Show error message to user"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK
        )
        dialog.set_property("text", "Error")
        dialog.set_property("secondary-text", error_message)
        dialog.present()
        return False  # Don't repeat

    async def _generate_title_async(self):
        """Generate a title for the current conversation"""
        try:
            conversation_id = self.app_state.current_conversation_id
            if conversation_id:
                title = await self.app_state.generate_conversation_title(conversation_id)
                if title:
                    logger.info(f"Auto-generated title: {title}")
                    # Refresh sidebar to show new title
                    GLib.idle_add(self.load_conversations)
        except Exception as e:
            logger.error(f"Failed to auto-generate title: {e}")


def main():
    """Application entry point"""
    app = NanoChatApplication()
    app.run(None)


if __name__ == "__main__":
    main()
