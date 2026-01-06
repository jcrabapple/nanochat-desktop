import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, Gdk


class Sidebar(Gtk.Box):
    """Sidebar with conversation list"""

    __gsignals__ = {
        'new-chat': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'conversation-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'conversation-deleted': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'conversation-renamed': (GObject.SIGNAL_RUN_FIRST, None, (object, str))
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.set_size_request(280, -1)
        self.add_css_class("sidebar")

        # New Chat button
        self.new_chat_button = Gtk.Button(label="New Chat")
        self.new_chat_button.add_css_class("suggested-action")
        self.new_chat_button.set_margin_start(12)
        self.new_chat_button.set_margin_end(12)
        self.new_chat_button.set_margin_top(12)
        self.new_chat_button.set_margin_bottom(12)
        self.new_chat_button.connect("clicked", self.on_new_chat)
        self.append(self.new_chat_button)

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search conversations...")
        self.search_entry.set_margin_start(12)
        self.search_entry.set_margin_end(12)
        self.search_entry.set_margin_bottom(12)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.append(self.search_entry)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(separator)

        # Scrolled window for conversation list
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_vexpand(True)

        # Conversation list box
        self.conversation_list = Gtk.ListBox()
        self.conversation_list.add_css_class("conversation-list")
        self.conversation_list.connect("row-activated", self.on_conversation_selected)
        self.scrolled.set_child(self.conversation_list)

        self.append(self.scrolled)

        # Store conversation data
        self.conversations = []
        self.all_conversations = []  # Store unfiltered conversations

    def on_new_chat(self, button):
        """Handle new chat button click"""
        self.emit('new-chat')

    def on_conversation_selected(self, list_box, row):
        """Handle conversation selection"""
        if row:
            conversation_id = row.conversation_id
            self.emit('conversation-selected', conversation_id)

    def populate_conversations(self, conversations: list):
        """
        Populate sidebar with conversations

        Args:
            conversations: List of conversation dicts with keys:
                          - id, title, updated_at, message_count
        """
        # Store all conversations for filtering
        self.all_conversations = conversations

        # Apply current search filter if any
        search_text = self.search_entry.get_text()
        if search_text:
            filtered = self._filter_conversations(conversations, search_text)
            self._display_conversations(filtered)
        else:
            self._display_conversations(conversations)

    def _display_conversations(self, conversations: list):
        """Internal method to display conversations"""
        # Clear existing
        while self.conversation_list.get_first_child() is not None:
            self.conversation_list.remove(self.conversation_list.get_first_child())

        self.conversations = conversations

        # Group conversations by date
        groups = self._group_by_date(conversations)

        # Add conversations in groups
        for group_name, convos in groups.items():
            # Group header
            header = Gtk.Label(label=group_name.upper())
            header.add_css_class("conversation-group-header")
            header.set_halign(Gtk.Align.START)
            header.set_margin_start(12)
            header.set_margin_top(12)
            header.set_margin_bottom(4)
            self.conversation_list.append(header)

            # Conversations in group
            for conv in convos:
                row = ConversationRow(conv)
                row.connect('delete-requested', self.on_delete_requested)
                row.connect('rename-requested', self.on_rename_requested)
                self.conversation_list.append(row)

    def on_search_changed(self, search_entry):
        """Handle search text changes"""
        search_text = search_entry.get_text().strip().lower()

        if not search_text:
            # Show all conversations
            self._display_conversations(self.all_conversations)
        else:
            # Filter conversations
            filtered = self._filter_conversations(self.all_conversations, search_text)
            self._display_conversations(filtered)

    def _filter_conversations(self, conversations: list, search_text: str) -> list:
        """Filter conversations by search text"""
        return [
            conv for conv in conversations
            if search_text.lower() in conv['title'].lower()
        ]

    def _group_by_date(self, conversations: list) -> dict:
        """Group conversations by time periods"""
        from datetime import datetime, timedelta, timezone

        groups = {
            "Today": [],
            "Last 7 Days": [],
            "Last 30 Days": [],
            "Older": []
        }

        now = datetime.now(timezone.utc)
        today = now.date()
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)

        for conv in conversations:
            try:
                # Parse timestamp
                updated_at = datetime.fromisoformat(conv['updated_at'].replace('Z', '+00:00'))
                conv_date = updated_at.date()

                if conv_date == today:
                    groups["Today"].append(conv)
                elif conv_date >= seven_days_ago:
                    groups["Last 7 Days"].append(conv)
                elif conv_date >= thirty_days_ago:
                    groups["Last 30 Days"].append(conv)
                else:
                    groups["Older"].append(conv)
            except:
                # If parsing fails, put in "Older"
                groups["Older"].append(conv)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def on_delete_requested(self, row, conversation_id):
        """Handle delete request from conversation row"""
        self.emit('conversation-deleted', conversation_id)

    def on_rename_requested(self, row, conversation_id, new_title):
        """Handle rename request from conversation row"""
        self.emit('conversation-renamed', conversation_id, new_title)

    def set_active_conversation(self, conversation_id: int):
        """Highlight active conversation"""
        row = self.conversation_list.get_first_child()
        while row:
            if isinstance(row, ConversationRow) and row.conversation_id == conversation_id:
                self.conversation_list.select_row(row)
            row = row.get_next_sibling()


class ConversationRow(Gtk.ListBoxRow):
    """Single conversation row in sidebar"""

    __gsignals__ = {
        'delete-requested': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'rename-requested': (GObject.SIGNAL_RUN_FIRST, None, (object, str))
    }

    def __init__(self, conversation: dict):
        super().__init__()

        self.conversation_id = conversation['id']
        self.original_title = conversation['title']
        self.is_editing = False

        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.main_box.set_margin_start(12)
        self.main_box.set_margin_end(12)
        self.main_box.set_margin_top(8)
        self.main_box.set_margin_bottom(8)

        # Title and metadata
        self.text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # Title
        self.title_label = Gtk.Label(label=conversation['title'])
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_ellipsize(True)  # Truncate with "..."
        self.title_label.set_width_chars(25)
        self.text_box.append(self.title_label)

        # Metadata (message count, time)
        metadata = f"{conversation.get('message_count', 0)} messages"
        meta_label = Gtk.Label(label=metadata)
        meta_label.add_css_class("dim-label")
        meta_label.set_halign(Gtk.Align.START)
        meta_label.set_size_request(200, -1)
        self.text_box.append(meta_label)

        self.main_box.append(self.text_box)

        # Delete button (trash icon, initially hidden)
        self.delete_button = Gtk.Button()
        trash_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        trash_icon.set_pixel_size(16)
        self.delete_button.set_child(trash_icon)
        self.delete_button.set_tooltip_text("Delete conversation")
        self.delete_button.add_css_class("delete-button")
        self.delete_button.set_opacity(0)  # Hidden initially
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.main_box.append(self.delete_button)

        self.set_child(self.main_box)

        # Add hover controller to the main box
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_hover_enter)
        hover_controller.connect("leave", self.on_hover_leave)
        self.main_box.add_controller(hover_controller)

        # Add double-click controller for rename
        click_controller = Gtk.GestureClick()
        click_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click_controller.connect("pressed", self.on_double_click)
        self.main_box.add_controller(click_controller)

        # Add right-click controller
        right_click_controller = Gtk.GestureClick()
        right_click_controller.set_button(3)  # Right click
        right_click_controller.connect("pressed", self.on_right_click)
        self.main_box.add_controller(right_click_controller)

    def on_double_click(self, gesture, n_press, x, y):
        """Handle double-click to start editing"""
        if n_press == 2:
            self.start_rename()

    def start_rename(self):
        """Start inline editing of the title"""
        if self.is_editing:
            return

        self.is_editing = True

        # Create entry for editing
        self.title_entry = Gtk.Entry()
        self.title_entry.set_text(self.original_title)
        self.title_entry.set_halign(Gtk.Align.START)
        self.title_entry.set_width_chars(25)

        # Replace label with entry
        parent = self.title_label.get_parent()
        parent.remove(self.title_label)
        parent.prepend(self.title_entry)

        # Connect signals
        self.title_entry.connect("activate", self.on_rename_activate)
        self.title_entry.connect("focus-out", self.on_rename_cancel)

        # Add key controller for Escape
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_rename_key_pressed)
        self.title_entry.add_controller(key_controller)

        # Focus and select all text
        self.title_entry.grab_focus()
        self.title_entry.set_position(-1)  # Move cursor to end
        # We need to select all after the widget is realized
        GLib.timeout_add(50, self._select_entry_text)

    def _select_entry_text(self):
        """Select all text in entry (called after widget is realized)"""
        if self.title_entry and self.is_editing:
            self.title_entry.grab_focus()
            # Select all text
            buffer = self.title_entry.get_buffer()
            self.title_entry.select_region(0, -1)
        return False  # Don't repeat

    def on_rename_activate(self, entry):
        """Handle Enter key in rename entry"""
        new_title = entry.get_text().strip()
        if new_title and new_title != self.original_title:
            self.original_title = new_title
            self.emit('rename-requested', self.conversation_id, new_title)
        self.finish_rename()

    def on_rename_cancel(self, entry, unknown):
        """Handle focus-out (cancel edit)"""
        # Cancel if empty or same as original
        new_title = entry.get_text().strip()
        if not new_title or new_title == self.original_title:
            self.finish_rename()
        else:
            self.original_title = new_title
            self.emit('rename-requested', self.conversation_id, new_title)
            self.finish_rename()

    def on_rename_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press in rename entry"""
        if keyval == Gdk.KEY_Escape:
            # Cancel without saving
            self.finish_rename()
            return True
        return False

    def finish_rename(self):
        """Finish editing and restore label"""
        if not self.is_editing:
            return

        self.is_editing = False

        # Create new label with updated title
        new_label = Gtk.Label(label=self.original_title)
        new_label.set_halign(Gtk.Align.START)
        new_label.set_ellipsize(True)
        new_label.set_width_chars(25)

        # Replace entry with label
        parent = self.title_entry.get_parent()
        parent.remove(self.title_entry)
        parent.prepend(new_label)

        self.title_label = new_label
        self.title_entry = None

    def on_hover_enter(self, controller, x, y):
        """Show delete button on hover"""
        self.delete_button.set_opacity(1)

    def on_hover_leave(self, controller):
        """Hide delete button when hover ends"""
        self.delete_button.set_opacity(0)

    def on_delete_clicked(self, button):
        """Handle delete button click"""
        self.emit('delete-requested', self.conversation_id)

    def on_right_click(self, gesture, n_press, x, y):
        """Show context menu on right-click"""
        if n_press == 1:
            # Create popover menu
            popover = Gtk.Popover()
            popover.set_parent(self)

            # Position popover in the center of the row
            allocation = self.get_allocation()
            rect = Gdk.Rectangle()
            rect.x = allocation.width / 2
            rect.y = allocation.height / 2
            rect.width = 1
            rect.height = 1
            popover.set_pointing_to(rect)

            # Create delete button
            delete_btn = Gtk.Button(label="Delete")
            delete_btn.connect("clicked", self.on_context_delete_close, popover)
            delete_btn.add_css_class("menu-item")

            # Add to popover
            popover.set_child(delete_btn)
            popover.popup()

    def on_context_delete_close(self, widget, popover):
        """Handle delete from context menu and close popover"""
        popover.popdown()
        self.emit('delete-requested', self.conversation_id)

    def on_context_delete(self, widget):
        """Handle delete from context menu"""
        self.emit('delete-requested', self.conversation_id)
