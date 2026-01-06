import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, GLib, Pango, Gdk

# Try to import WebKit2, but make it optional
try:
    gi.require_version('WebKit2', '4.1')
    from gi.repository import WebKit2
    WEBKIT_AVAILABLE = True
except (ValueError, ImportError):
    WEBKIT_AVAILABLE = False
    WebKit2 = None

import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import html as html_lib
import re
import logging

logger = logging.getLogger(__name__)


class MarkdownView(Gtk.Box):
    """Widget for displaying markdown content using WebKit"""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        if WEBKIT_AVAILABLE:
            # Create WebView
            self.webview = WebKit2.WebView()
            settings = self.webview.get_settings()
            settings.set_enable_javascript(False)  # Security
            settings.set_enable_plugins(False)

            # Create scrolled window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_child(self.webview)
            scrolled.set_vexpand(True)
            scrolled.set_hexpand(True)

            self.append(scrolled)
            self.use_webview = True
            self.load_html("")
        else:
            # Fallback to simple TextView
            logger.warning("WebKit2 not available, using TextView for markdown rendering")
            self.text_view = Gtk.TextView()
            self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            self.text_view.set_editable(False)
            self.text_view.set_left_margin(16)
            self.text_view.set_right_margin(16)
            self.text_view.set_top_margin(8)
            self.text_view.set_bottom_margin(12)
            self.text_view.set_hexpand(True)
            self.text_view.add_css_class("markdown-textview")  # Add CSS class for consistency
            # Don't put in scrolled window - let content expand naturally
            self.append(self.text_view)
            self.use_webview = False

    def load_html(self, content: str):
        """Load markdown content as HTML or plain text"""
        if self.use_webview:
            html = self._markdown_to_html(content)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><style>{self._get_dark_theme_css()}</style></head>
            <body>{html}</body>
            </html>
            """
            self.webview.load_html(full_html)
        else:
            # Fallback: display as plain text with minimal formatting
            # Strip leading/trailing whitespace to avoid empty lines
            clean_content = content.strip()

            # Remove leading double newlines that create empty space at the start
            # Check if content starts with text followed by \n\n and remove those newlines
            import re
            # Match: some text, then \n\n, then more content - remove the \n\n
            clean_content = re.sub(r'^([^\n]+)\n\n', r'\1\n', clean_content)

            buffer = self.text_view.get_buffer()
            buffer.set_text(clean_content)

            # Debug logging
            import sys
            print(f"DEBUG TextView: Content starts with: {repr(clean_content[:100])}", file=sys.stderr)

    def _markdown_to_html(self, content: str) -> str:
        """Convert markdown to HTML with syntax highlighting"""
        if not content:
            return ""

        # DEBUG: Log the raw content
        logger.debug(f"Raw content (first 100 chars): {repr(content[:100])}")

        # Strip leading/trailing whitespace and empty lines
        content = content.strip()

        # Additional cleanup: remove all leading newlines
        content = content.lstrip('\n')

        # DEBUG: Log after stripping
        logger.debug(f"After stripping (first 100 chars): {repr(content[:100])}")

        md = markdown.Markdown(
            extensions=['fenced_code', 'codehilite', 'tables', 'sane_lists'],
            extension_configs={'codehilite': {'linenums': False, 'css_class': 'codehilite'}}
        )
        html = md.convert(content)

        # DEBUG: Log the HTML
        logger.debug(f"HTML output (first 200 chars): {repr(html[:200])}")

        # Post-process HTML: remove leading <br>, <p>, or whitespace from beginning
        html = html.strip()
        html = re.sub(r'^^(<br\s*/?>|&nbsp;)+', '', html, flags=re.IGNORECASE)
        html = html.lstrip()

        # Remove empty paragraphs at the start
        html = re.sub(r'^<p>\s*</p>', '', html)
        html = re.sub(r'^<p>(\s|<br\s*/?>)*</p>', '', html)

        html = self._apply_syntax_highlighting(html)
        md.reset()
        return html

    def _apply_syntax_highlighting(self, html: str) -> str:
        """Apply Pygments syntax highlighting to code blocks"""
        pattern = r'<pre><code class="language-(\w*)">(.*?)</code></pre>'

        def highlight_block(match):
            lang = match.group(1)
            code = html_lib.unescape(match.group(2))

            try:
                lexer = get_lexer_by_name(lang, stripall=True) if lang else guess_lexer(code)
            except ClassNotFound:
                lexer = TextLexer()

            formatter = HtmlFormatter(style='monokai', noclasses=True, cssclass='codehilite')
            highlighted = highlight(code, lexer, formatter)
            return f'<pre class="codehilite">{highlighted}</pre>'

        return re.sub(pattern, highlight_block, html, flags=re.DOTALL)

    def _get_dark_theme_css(self) -> str:
        """Generate CSS matching app dark theme"""
        return """
        @font-face {
            font-family: 'Emoji';
            src: local('Noto Color Emoji'),
                 local('Apple Color Emoji'),
                 local('Segoe UI Emoji'),
                 local('Twemoji Emoji');
        }

        body { font-family: system-ui, 'Emoji', sans-serif; font-size: 15px; line-height: 1.5; color: #e0e0e0; margin: 0; padding: 8px; background: transparent; min-width: 600px; max-width: 900px; }
        h1, h2, h3 { color: #fff; margin-top: 0.8em; margin-bottom: 0.4em; font-weight: 600; }
        h1 { font-size: 1.5em; } h2 { font-size: 1.3em; } h3 { font-size: 1.15em; }
        p { margin: 0; }
        code { background-color: #2a2b2e; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
        pre { background-color: #2a2b2e; padding: 12px; border-radius: 6px; margin: 8px 0; overflow-x: auto; }
        pre code { background: transparent; padding: 0; }
        a { color: #4a9eff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        ul, ol { margin: 0.5em 0; padding-left: 2em; }
        blockquote { border-left: 4px solid #4a9eff; margin: 1em 0; padding-left: 1em; color: #a0a0a0; }
        table { border-collapse: collapse; margin: 1em 0; width: 100%; }
        th, td { border: 1px solid #2a2b2e; padding: 8px 12px; }
        th { background-color: rgba(255,255,255,0.05); font-weight: 600; }
        .codehilite { background-color: #2a2b2e; }
        """

    def update_content(self, content: str):
        """Update content (for streaming responses)"""
        logger.debug(f"MarkdownView.update_content called with {len(content)} characters")
        self.load_html(content)


class SourcesBox(Gtk.Box):
    """Collapsible widget for displaying web sources"""

    def __init__(self, sources: list):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.sources = sources
        self.expanded = False

        self.add_css_class("web-sources")
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_bottom(12)

        # Header row (always visible)
        header = self._create_header()
        self.append(header)

        # Sources list (collapsible, hidden by default)
        self.sources_list = self._create_sources_list()
        self.sources_list.set_visible(False)
        self.append(self.sources_list)

    def _create_header(self) -> Gtk.Box:
        """Create clickable header"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Expand/collapse icon
        self.icon = Gtk.Label(label="▶")
        self.icon.add_css_class("sources-icon")
        box.append(self.icon)

        # Title
        title = Gtk.Label(label=f"Sources ({len(self.sources)})")
        title.add_css_class("sources-header")
        box.append(title)

        # Make clickable
        click_controller = Gtk.GestureClick()
        click_controller.connect("pressed", self.on_header_clicked)
        box.add_controller(click_controller)

        return box

    def _create_sources_list(self) -> Gtk.Box:
        """Create list of source links"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_start(20)
        box.set_margin_top(8)

        for i, source in enumerate(self.sources):
            item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            # Number
            num_label = Gtk.Label(label=f"{i+1}.")
            num_label.add_css_class("source-number")
            item.append(num_label)

            # Link (truncated)
            url = source.get('url', '')
            title = source.get('title', url)
            if len(title) > 60:
                title = title[:57] + "..."

            link_label = Gtk.Label(label=title)
            link_label.add_css_class("source-link")
            link_label.set_ellipsize(Pango.EllipsizeMode.END)
            link_label.set_selectable(True)
            item.append(link_label)

            box.append(item)

        return box

    def on_header_clicked(self, gesture, n_press, x, y):
        """Toggle expand/collapse"""
        self.expanded = not self.expanded
        self.icon.set_label("▼" if self.expanded else "▶")
        self.sources_list.set_visible(self.expanded)


class ChatView(Gtk.Box):
    """Main chat area with message display and input"""

    __gsignals__ = {
        'message-send': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'web-search-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
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
        """Create message input area with floating buttons"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_bottom(24)
        box.set_margin_top(12)

        # Create overlay for floating buttons
        overlay = Gtk.Overlay()
        overlay.set_vexpand(False)

        # Main text input area
        text_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_container.set_hexpand(True)

        # Text view for input
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_accepts_tab(False)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(110)  # Space for buttons on right
        self.text_view.add_css_class("message-input")

        # Get buffer
        self.buffer = self.text_view.get_buffer()
        self.buffer.connect("changed", self.on_text_changed)

        # Minimal scrolled window - only shows scrollbar when content overflows
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        text_scroll.set_child(self.text_view)
        text_scroll.set_hexpand(True)
        text_scroll.set_min_content_height(70)  # Minimum 2 lines (taller)

        text_container.append(text_scroll)
        overlay.set_child(text_container)

        # Floating button container
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        button_container.set_halign(Gtk.Align.END)  # Align to right
        button_container.set_valign(Gtk.Align.END)
        button_container.set_margin_bottom(8)
        button_container.set_margin_end(8)

        # Web search toggle button
        self.web_search_button = Gtk.ToggleButton()
        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_icon.set_pixel_size(16)
        self.web_search_button.set_child(search_icon)
        self.web_search_button.set_tooltip_text("Enable Web Search")
        self.web_search_button.add_css_class("icon-button")
        self.web_search_button.add_css_class("floating-button")
        self.web_search_button.set_valign(Gtk.Align.CENTER)
        self.web_search_button.connect("toggled", self.on_web_search_toggled)
        button_container.append(self.web_search_button)

        # Send button (right side)
        self.send_button = Gtk.Button()
        send_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
        send_icon.set_pixel_size(16)
        self.send_button.set_child(send_icon)
        self.send_button.add_css_class("send-button")
        self.send_button.add_css_class("floating-button")
        self.send_button.set_valign(Gtk.Align.CENTER)
        self.send_button.set_tooltip_text("Send message")
        self.send_button.set_sensitive(False)
        self.send_button.connect("clicked", self.on_send_clicked)
        button_container.append(self.send_button)

        # Add floating buttons as overlay
        overlay.add_overlay(button_container)

        box.append(overlay)

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
        # Send on Enter (unless Shift is pressed for line break)
        if keyval == Gdk.KEY_Return:
            if state & Gdk.ModifierType.SHIFT_MASK:
                # Shift+Enter - allow line break
                return False
            else:
                # Just Enter - send message
                self.on_send_clicked(None)
                return True  # Event handled (don't insert newline)
        return False

    def on_web_search_toggled(self, button):
        """Handle web search toggle button"""
        is_active = button.get_active()

        if is_active:
            button.add_css_class("icon-button-active")
            button.set_tooltip_text("Web Search Enabled")
        else:
            button.remove_css_class("icon-button-active")
            button.set_tooltip_text("Enable Web Search")

        self.emit('web-search-toggled', is_active)

    def on_send_clicked(self, button):
        """Handle send button click"""
        print("DEBUG: Send button clicked")
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, False)

        if text.strip():
            print(f"DEBUG: Emitting message-send signal with text: '{text.strip()[:50]}...'")
            self.emit('message-send', text.strip())
            self.buffer.set_text("")  # Clear input
        else:
            print("DEBUG: No text to send")

    def add_message(self, role: str, content: str, timestamp: str = None,
                    web_sources: list = None, update_last: bool = False):
        """
        Add a message to the chat view

        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Optional timestamp string
            web_sources: Optional list of web sources
            update_last: If True, update the last assistant message instead of creating new one
        """
        # Hide welcome screen
        if self.welcome_screen.get_parent():
            self.messages_box.remove(self.welcome_screen)

        if update_last:
            # Update the last message row (for streaming responses)
            last_child = self.messages_box.get_last_child()
            if last_child and isinstance(last_child, MessageRow):
                if content:
                    last_child.update_content(content)
                if web_sources:
                    last_child.update_sources(web_sources)
        else:
            # Create new message row
            message_row = MessageRow(role, content, timestamp, web_sources)
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

    def set_web_search_enabled(self, enabled: bool):
        """Programmatically set web search state"""
        self.web_search_button.set_active(enabled)

    def get_web_search_enabled(self) -> bool:
        """Get current web search state"""
        return self.web_search_button.get_active()


class MessageRow(Gtk.Box):
    """Single message display row with bubble layout"""

    def __init__(self, role: str, content: str, timestamp: str = None, web_sources: list = None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.role = role
        self.content = content
        self.web_sources = web_sources

        # Add CSS class based on role
        self.add_css_class(f"message-row")
        self.add_css_class(role)

        # Margin
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        # Create alignment container for bubble
        if role == 'user':
            # User messages: align to right
            align_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            align_container.set_halign(Gtk.Align.END)
            align_container.set_hexpand(True)

            # User label
            label = self._create_role_label("User")
            align_container.append(label)

            # User bubble
            self.content_widget = self._create_user_bubble(content)
            align_container.append(self.content_widget)
            self.append(align_container)

            # No web sources for user messages
            self.sources_box = None
        else:
            # Assistant messages: align to left
            align_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            align_container.set_halign(Gtk.Align.START)
            align_container.set_hexpand(True)

            # Assistant label
            label = self._create_role_label("Assistant")
            align_container.append(label)

            # Assistant bubble
            self.content_widget = self._create_assistant_bubble(content)
            align_container.append(self.content_widget)

            # Web sources (if any)
            self.sources_box = None
            if web_sources:
                self.sources_box = SourcesBox(web_sources)
                align_container.append(self.sources_box)

            self.append(align_container)

    def _create_role_label(self, role_name: str) -> Gtk.Label:
        """Create role label"""
        label = Gtk.Label(label=role_name)
        label.add_css_class("message-role-label")
        label.set_halign(Gtk.Align.START)
        return label

    def _create_user_bubble(self, content: str) -> Gtk.Label:
        """Create user message bubble"""
        label = Gtk.Label(label=content)
        label.set_halign(Gtk.Align.START)
        label.set_xalign(0)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_selectable(True)
        label.add_css_class("message-bubble")
        label.add_css_class("user-bubble")
        return label

    def _create_assistant_bubble(self, content: str, web_sources: list = None):
        """Create assistant message bubble with markdown"""
        bubble = MarkdownView()
        bubble.load_html(content)
        bubble.add_css_class("message-bubble")
        bubble.add_css_class("assistant-bubble")
        bubble.set_hexpand(True)
        bubble.set_size_request(600, -1)  # Set minimum width of 600px
        logger.debug(f"Created assistant bubble with {len(content)} chars of content")
        return bubble

    def update_content(self, content: str):
        """Update the message content (for streaming responses)"""
        self.content = content
        if self.role == 'assistant':
            self.content_widget.update_content(content)
        else:
            self.content_widget.set_label(content)

    def update_sources(self, web_sources: list):
        """Update or add web sources"""
        if not web_sources or self.role != 'assistant':
            return

        self.web_sources = web_sources
        if self.sources_box:
            # Remove existing sources box
            parent = self.sources_box.get_parent()
            if parent:
                parent.remove(self.sources_box)

        self.sources_box = SourcesBox(web_sources)
        # Add to the alignment container (which is the second child of MessageRow)
        align_container = self.get_first_child()
        if align_container:
            align_container.append(self.sources_box)
            self.sources_box.show()
