import os
import gi
gi.require_version('Gtk', '4.0')

# Try to import Adw (libadwaita) - optional for responsive features
try:
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Gdk, GLib, Adw
    ADW_AVAILABLE = True
except (ValueError, ImportError):
    from gi.repository import Gtk, Gdk, GLib
    Adw = None
    ADW_AVAILABLE = False

from nanochat.ui.header_bar import HeaderBar
from nanochat.ui.sidebar import Sidebar
from nanochat.ui.chat_view import ChatView
from nanochat.ui.settings_dialog import SettingsDialog
from nanochat.ui.project_dialog import ProjectDialog, MoveToProjectDialog


# Determine base class based on Adw availability
_BaseWindow = Adw.ApplicationWindow if ADW_AVAILABLE else Gtk.ApplicationWindow


class MainWindow(_BaseWindow):
    """Main application window"""

    def __init__(self, app):
        super().__init__(application=app)

        # Window properties
        self.set_title("NanoChat Desktop")
        self.set_default_size(1200, 800)
        self.set_size_request(600, 500)

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
        # Header bar
        self.header_bar = HeaderBar()

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.connect('new-chat', self.on_new_chat)
        self.sidebar.connect('conversation-selected', self.on_conversation_selected)
        self.sidebar.connect('conversation-deleted', self.on_conversation_deleted)
        self.sidebar.connect('conversation-renamed', self.on_conversation_renamed)
        self.sidebar.connect('conversation-move-to-project', self.on_move_to_project)
        self.sidebar.connect('project-created', self.on_create_project)
        self.sidebar.connect('project-selected', self.on_project_selected)
        self.sidebar.connect('project-deleted', self.on_project_deleted)
        self.sidebar.connect('settings-clicked', self.on_settings)

        # Chat view
        self.chat_view = ChatView()
        self.chat_view.connect('message-send', self.on_message_send)
        self.chat_view.connect('web-search-toggled', self.on_web_search_toggled)
        self.chat_view.connect('conversation-mode-changed', self.on_conversation_mode_changed)
        self.chat_view.connect('regenerate-requested', self.on_regenerate_requested)
        self.chat_view.connect('message-deleted', self.on_message_deleted)

        if ADW_AVAILABLE:
            # Use Adw.ToolbarView to wrap content with header bar
            toolbar_view = Adw.ToolbarView()
            toolbar_view.add_top_bar(self.header_bar)

            # Use Adw.OverlaySplitView for responsive sidebar
            self.split_view = Adw.OverlaySplitView()
            self.split_view.set_collapsed(False)
            self.split_view.set_min_sidebar_width(280)
            self.split_view.set_max_sidebar_width(400)

            # Set up split view
            self.split_view.set_sidebar(self.sidebar)
            self.split_view.set_content(self.chat_view)

            # Add split view to toolbar view
            toolbar_view.set_content(self.split_view)
            self.set_content(toolbar_view)

            # Add responsive breakpoint - collapse sidebar below 800px
            breakpoint = Adw.Breakpoint(
                condition=Adw.BreakpointCondition.parse("max-width: 800px")
            )
            breakpoint.add_setter(self.split_view, "collapsed", True)
            self.add_breakpoint(breakpoint)

            # Add toggle button to header bar for showing/hiding sidebar when collapsed
            self.sidebar_toggle = Gtk.ToggleButton(active=True)
            self.sidebar_toggle.set_icon_name("view-list-symbolic")
            self.sidebar_toggle.set_tooltip_text("Toggle Sidebar")
            self.sidebar_toggle.connect("toggled", self._on_sidebar_toggle)
            self.header_bar.pack_start(self.sidebar_toggle)
        else:
            # Fallback: simple horizontal layout without responsive features
            self.set_titlebar(self.header_bar)

            main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.set_child(main_box)
            main_box.append(self.sidebar)

            separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
            main_box.append(separator)

            main_box.append(self.chat_view)

        # Show welcome screen
        self.chat_view.show_welcome()

        # Add keyboard shortcuts
        self.setup_shortcuts()

    def _on_sidebar_toggle(self, button):
        """Toggle sidebar visibility"""
        if ADW_AVAILABLE and hasattr(self, 'split_view'):
            self.split_view.set_show_sidebar(button.get_active())

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
            current_model=config.model,
            current_title_model=config.title_model
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

    def on_regenerate_requested(self, chat_view):
        """Handle regenerate request from message row"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("MainWindow: Received regenerate-requested signal")

        # Check app_state directly instead of cached value
        # because conversation might be created during message send
        if not self.app_state or not self.app_state.current_conversation_id:
            logger.error("Cannot regenerate: No active conversation")
            return

        # Sync the cached value
        self.current_conversation_id = self.app_state.current_conversation_id
        logger.info(f"Using conversation ID: {self.current_conversation_id}")
        # Remove the last assistant message from UI (it will be deleted from DB during regeneration)
        # Find and remove the last assistant message row
        import threading
        import asyncio

        def run_regeneration():
            async def regenerate():
                try:
                    logger.info("Removing last assistant message from UI")
                    # First, remove the last assistant message from UI
                    child = chat_view.messages_box.get_last_child()
                    while child:
                        from nanochat.ui.chat_view import MessageRow
                        if isinstance(child, MessageRow) and child.role == 'assistant':
                            def remove_msg(child=child):
                                chat_view.messages_box.remove(child)
                                logger.info("Removed assistant message from UI")
                            GLib.idle_add(remove_msg)
                            break
                        child = child.get_prev_sibling()

                    logger.info("Calling app_state.regenerate_last_response()")
                    # Now regenerate the response
                    # Accumulate content and update the message incrementally
                    # First create empty message
                    def create_empty_msg():
                        chat_view.add_message('assistant', "", update_last=False)
                        logger.info("Created empty assistant message for regeneration")
                    GLib.idle_add(create_empty_msg)

                    # Accumulate content and update periodically
                    accumulated = ""
                    async for role, content, web_sources in self.app_state.regenerate_last_response():
                        if role == 'assistant':
                            if content:
                                accumulated += content
                                # Update UI with accumulated content
                                content_copy = accumulated
                                def add_msg(c=content_copy):
                                    chat_view.add_message('assistant', c, update_last=True)
                                    logger.info(f"Updated regenerated message (total {len(c)} chars)")
                                GLib.idle_add(add_msg)
                            if web_sources:
                                def add_src(ws=web_sources):
                                    chat_view.add_message('assistant', "", web_sources=ws, update_last=True)
                                    logger.info("Added web sources to UI")
                                GLib.idle_add(add_src)

                    # Refresh sidebar to update conversation preview
                    logger.info("Refreshing sidebar")
                    GLib.idle_add(self.refresh_projects_and_conversations)
                    logger.info("Regeneration complete")

                except Exception as e:
                    logger.error(f"Error during regeneration: {e}")
                    import traceback
                    traceback.print_exc()
                    def show_error(msg=str(e)):
                        # Try to show error dialog
                        try:
                            self.show_error_dialog(f"Regeneration failed: {msg}")
                        except:
                            pass
                    GLib.idle_add(show_error)

            asyncio.run(regenerate())

        # Run in background thread
        thread = threading.Thread(target=run_regeneration, daemon=True)
        thread.start()
        logger.info("Started regeneration thread")

    def on_message_deleted(self, chat_view):
        """Handle message deletion from chat view"""
        print("Message deleted from UI")
        # The UI has already been updated by the chat_view
        # We could add database cleanup here if needed
        # For now, messages are only deleted from UI, not from database
        # (full message deletion from DB would require tracking which message was deleted)

    def on_new_chat(self, sidebar):
        """Handle new chat button"""
        print("New chat requested")

        # Create new conversation in database
        if self.app_state:
            new_id = self.app_state.create_conversation()
            self.current_conversation_id = new_id

            # Reload sidebar to show new conversation and update counts
            self.refresh_projects_and_conversations()
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
                # Delete successful
                if self.current_conversation_id == conversation_id:
                    self.current_conversation_id = None
                    self.chat_view.show_welcome()
                
                # Refresh entire sidebar to update conversation list AND project counts
                self.refresh_projects_and_conversations()

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
            # Sync current_conversation_id with app_state after message send
            # This ensures regenerate works for newly created conversations
            if self.app_state:
                self.current_conversation_id = self.app_state.current_conversation_id
                print(f"DEBUG: Synced current_conversation_id to {self.current_conversation_id}")
        else:
            print("DEBUG: No app controller available")

    # ==================== Project Management ====================

    def refresh_projects_and_conversations(self):
        """Refresh both projects and conversations in sidebar"""
        if self.app_state:
            # Load conversations first so project counts are correct
            conversations = self.app_state.get_all_conversations()
            self.sidebar.populate_conversations(conversations)
            # Then load projects
            projects = self.app_state.get_all_projects()
            self.sidebar.populate_projects(projects)

    def on_create_project(self, sidebar):
        """Handle create project button click"""
        dialog = ProjectDialog(parent=self)

        def on_response(dialog, response_id):
            if response_id == Gtk.ResponseType.OK:
                project_data = dialog.get_project_data()
                if self.app_state and project_data['name']:
                    try:
                        self.app_state.create_project(
                            name=project_data['name'],
                            color=project_data['color'],
                            description=project_data['description']
                        )
                        self.refresh_projects_and_conversations()
                    except Exception as e:
                        print(f"Error creating project: {e}")
            dialog.destroy()

        dialog.connect('response', on_response)
        dialog.present()

    def on_project_selected(self, sidebar, project_id):
        """Handle project selection for filtering"""
        print(f"Filtering by project: {project_id}")
        self.sidebar.filter_by_project(project_id)

    def on_project_deleted(self, sidebar, project_id):
        """Handle project deletion"""
        print(f"Deleting project: {project_id}")
        if self.app_state:
            success = self.app_state.delete_project(project_id)
            if success:
                self.refresh_projects_and_conversations()

    def on_move_to_project(self, sidebar, conversation_id):
        """Handle move conversation to project"""
        if not self.app_state:
            return

        # Get current project for the conversation
        conversations = self.app_state.get_all_conversations()
        current_project_id = None
        for conv in conversations:
            if conv['id'] == conversation_id:
                current_project_id = conv.get('project_id')
                break

        # Get all projects
        projects = self.app_state.get_all_projects()

        dialog = MoveToProjectDialog(
            parent=self,
            projects=projects,
            current_project_id=current_project_id
        )

        def on_response(dialog, response_id):
            if response_id == Gtk.ResponseType.OK:
                new_project_id = dialog.get_selected_project_id()
                if self.app_state:
                    self.app_state.move_conversation_to_project(
                        conversation_id,
                        new_project_id
                    )
                    self.refresh_projects_and_conversations()
            dialog.destroy()

        dialog.connect('response', on_response)
        dialog.present()
