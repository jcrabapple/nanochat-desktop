import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject


class Sidebar(Gtk.Box):
    """Sidebar with conversation list"""

    __gsignals__ = {
        'new-chat': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'conversation-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,))
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
            self.conversation_list.append(row)

    def set_active_conversation(self, conversation_id: int):
        """Highlight active conversation"""
        row = self.conversation_list.get_first_child()
        while row:
            if isinstance(row, ConversationRow) and row.conversation_id == conversation_id:
                self.conversation_list.select_row(row)
            row = row.get_next_sibling()


class ConversationRow(Gtk.ListBoxRow):
    """Single conversation row in sidebar"""

    def __init__(self, conversation: dict):
        super().__init__()

        self.conversation_id = conversation['id']

        # Main box
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        # Icon
        icon = Gtk.Image.new_from_icon_name("user-home-symbolic")
        icon.set_pixel_size(20)
        box.append(icon)

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
        self.set_child(box)
