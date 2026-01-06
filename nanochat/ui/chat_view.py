import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, GLib, Pango, Gdk


class ChatView(Gtk.Box):
    """Main chat area with message display and input"""

    __gsignals__ = {
        'message-send': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.add_css_class("chat-view")

        # Messages area (scrolled)
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_vexpand(True)

        # Messages box
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.messages_box.set_margin_start(24)
        self.messages_box.set_margin_end(24)
        self.messages_box.set_margin_top(24)
        self.messages_box.set_margin_bottom(24)
        self.scrolled.set_child(self.messages_box)

        self.append(self.scrolled)

        # Input area
        self.input_box = self.create_input_area()
        self.append(self.input_box)

        # Welcome screen (shown when no messages)
        self.welcome_screen = self.create_welcome_screen()

    def create_input_area(self) -> Gtk.Box:
        """Create message input area"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_bottom(24)
        box.set_margin_top(12)

        # Input row
        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Text view for input
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_accepts_tab(False)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.add_css_class("message-input")

        # Get buffer
        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self.on_text_changed)

        # Scroll for text view
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        text_scroll.set_max_content_height(200)
        text_scroll.set_child(self.text_view)
        text_scroll.set_hexpand(True)

        input_row.append(text_scroll)

        # Send button
        self.send_button = Gtk.Button(label="Send")
        self.send_button.add_css_class("suggested-action")
        self.send_button.set_valign(Gtk.Align.END)
        self.send_button.set_sensitive(False)  # Disabled until text entered
        self.send_button.connect("clicked", self.on_send_clicked)

        input_row.append(self.send_button)

        box.append(input_row)

        # Handle Ctrl+Enter to send
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.text_view.add_controller(key_controller)

        return box

    def create_welcome_screen(self) -> Gtk.Box:
        """Create welcome screen for empty conversations"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        # Title
        title = Gtk.Label(label="How can I help you?")
        title.add_css_class("welcome-title")
        box.append(title)

        return box

    def on_text_changed(self, buffer):
        """Enable/disable send button based on text"""
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, False)

        has_text = bool(text.strip())
        self.send_button.set_sensitive(has_text)

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events"""
        # Send on Ctrl+Enter
        if keyval == Gdk.KEY_Return and (state & Gdk.ModifierType.CONTROL_MASK):
            self.on_send_clicked(None)
            return True  # Event handled
        return False

    def on_send_clicked(self, button):
        """Handle send button click"""
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, False)

        if text.strip():
            self.emit('message-send', text.strip())
            self.buffer.set_text("")  # Clear input

    def add_message(self, role: str, content: str, timestamp: str = None):
        """
        Add a message to the chat view

        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Optional timestamp string
        """
        # Hide welcome screen
        if self.welcome_screen.get_parent():
            self.messages_box.remove(self.welcome_screen)

        # Create message row
        message_row = MessageRow(role, content, timestamp)
        self.messages_box.append(message_row)

        # Scroll to bottom
        GLib.timeout_add(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scroll messages view to bottom"""
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False  # Don't repeat

    def show_welcome(self):
        """Show welcome screen (clear messages)"""
        # Remove all messages
        child = self.messages_box.get_first_child()
        while child:
            self.messages_box.remove(child)
            child = self.messages_box.get_first_child()

        # Show welcome screen
        self.messages_box.append(self.welcome_screen)

    def clear(self):
        """Clear all messages"""
        child = self.messages_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            if child != self.welcome_screen:
                self.messages_box.remove(child)
            child = next_child


class MessageRow(Gtk.Box):
    """Single message display row"""

    def __init__(self, role: str, content: str, timestamp: str = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.role = role
        self.content = content

        # Add CSS class based on role
        self.add_css_class(f"message-row")
        self.add_css_class(role)

        # Margin
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)

        # Header
        header = self.create_header(timestamp)
        self.append(header)

        # Content
        content_label = Gtk.Label(label=content)
        content_label.set_halign(Gtk.Align.START)
        content_label.set_xalign(0)
        content_label.set_wrap(True)
        content_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        content_label.set_selectable(True)
        content_label.add_css_class("message-content")
        self.append(content_label)

    def create_header(self, timestamp: str = None) -> Gtk.Box:
        """Create message header with role and timestamp"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Role
        role_label = Gtk.Label(label=self.role.capitalize())
        role_label.add_css_class("message-role")
        role_label.set_weight(600)
        box.append(role_label)

        # Timestamp
        if timestamp:
            ts_label = Gtk.Label(label=timestamp)
            ts_label.add_css_class("message-timestamp")
            ts_label.set_hexpand(True)
            ts_label.set_xalign(1)
            box.append(ts_label)

        return box
