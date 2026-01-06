import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, Gdk


class Sidebar(Gtk.Box):
    """Sidebar with conversation list"""

    __gsignals__ = {
        'new-chat': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'conversation-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'conversation-deleted': (GObject.SIGNAL_RUN_FIRST, None, (object,))
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
        # Clear existing
        while self.conversation_list.get_first_child() is not None:
            self.conversation_list.remove(self.conversation_list.get_first_child())

        self.conversations = conversations

        # Add conversations
        for conv in conversations:
            row = ConversationRow(conv)
            row.connect('delete-requested', self.on_delete_requested)
            self.conversation_list.append(row)

    def on_delete_requested(self, row, conversation_id):
        """Handle delete request from conversation row"""
        self.emit('conversation-deleted', conversation_id)

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
        'delete-requested': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self, conversation: dict):
        super().__init__()

        self.conversation_id = conversation['id']

        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        # Title and metadata
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # Title
        title_label = Gtk.Label(label=conversation['title'])
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(True)  # Truncate with "..."
        title_label.set_width_chars(25)
        text_box.append(title_label)

        # Metadata (message count, time)
        metadata = f"{conversation.get('message_count', 0)} messages"
        meta_label = Gtk.Label(label=metadata)
        meta_label.add_css_class("dim-label")
        meta_label.set_halign(Gtk.Align.START)
        meta_label.set_size_request(200, -1)
        text_box.append(meta_label)

        box.append(text_box)

        # Delete button (trash icon, initially hidden)
        self.delete_button = Gtk.Button()
        trash_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        trash_icon.set_pixel_size(16)
        self.delete_button.set_child(trash_icon)
        self.delete_button.set_tooltip_text("Delete conversation")
        self.delete_button.add_css_class("delete-button")
        self.delete_button.set_opacity(0)  # Hidden initially
        self.delete_button.connect("clicked", self.on_delete_clicked)
        box.append(self.delete_button)

        self.set_child(box)

        # Add hover controller to the main box
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_hover_enter)
        hover_controller.connect("leave", self.on_hover_leave)
        box.add_controller(hover_controller)

        # Add right-click controller
        click_controller = Gtk.GestureClick()
        click_controller.set_button(3)  # Right click
        click_controller.connect("pressed", self.on_right_click)
        box.add_controller(click_controller)

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
