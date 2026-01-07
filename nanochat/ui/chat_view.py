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

from nanochat.ui.action_bar import ActionBar
from nanochat.ui.suggested_prompts import SuggestedPrompts
from nanochat.state.conversation_mode import ConversationMode

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
            logger.debug(f"Loaded HTML content ({len(content)} chars via WebView)")
        else:
            # Fallback: display as Pango markup
            # Convert markdown to Pango markup
            pango_content = self._markdown_to_plain_text(content)

            buffer = self.text_view.get_buffer()
            # Use insert_markup to render Pango markup
            buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
            # Pass -1 as length to let GTK calculate it automatically from the string
            buffer.insert_markup(buffer.get_start_iter(), pango_content, -1)
            logger.debug(f"Loaded Pango markup content ({len(content)} chars via TextView fallback)")

    def _markdown_to_plain_text(self, content: str) -> str:
        """Convert markdown to Pango markup for TextView fallback"""
        if not content:
            return ""

        # Strip leading/trailing whitespace
        content = content.strip()

        # Remove leading newlines
        content = content.lstrip('\n')

        # First pass: Process LaTeX (block and inline)
        content = self._process_latex(content)

        # Second pass: Process tables
        content = self._process_tables(content)

        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False

        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append('─' * 40)
                continue

            if in_code_block:
                # Code content - use monospace style
                formatted_lines.append(f"<tt><span foreground='#a9b7c6'>{self._escape_pango(line)}</span></tt>")
                continue

            # Table lines (preserve box-drawing characters)
            if '┌' in line or '┐' in line or '└' in line or '┘' in line or '├' in line or '┤' in line or line.strip().startswith('│'):
                # Don't escape or process table lines - keep them as-is
                formatted_lines.append(line)
            # Math markers
            elif '━━━ MATH ━━━' in line:
                formatted_lines.append(f"<span foreground='#4a9eff' weight='bold'>{line}</span>")
            # Headers
            elif line.startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                header_text = self._escape_pango(line.lstrip('#').strip())
                if header_level == 1:
                    formatted_lines.append(f"\n<span weight='bold' size='large'>{header_text}</span>")
                elif header_level == 2:
                    formatted_lines.append(f"\n<span weight='bold' size='medium'>{header_text}</span>")
                else:
                    formatted_lines.append(f"\n<span weight='bold'>{header_text}</span>")
            # List items
            elif line.strip().startswith(('- ', '* ', '+ ')):
                list_text = self._process_inline_markdown(line.strip()[2:])
                formatted_lines.append(f"• {list_text}")
            # Numbered lists
            elif line.strip() and re.match(r'^\d+\.\s', line.strip()):
                processed_line = self._process_inline_markdown(line.strip())
                formatted_lines.append(processed_line)
            # Regular text
            elif line.strip():
                processed_line = self._process_inline_markdown(line)
                formatted_lines.append(processed_line)
            else:
                formatted_lines.append('')

        # Join with newlines and clean up excessive empty lines
        result = '\n'.join(formatted_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 consecutive newlines

        return result

    def _process_latex(self, content: str) -> str:
        """Process LaTeX math expressions and convert to readable text"""
        # Block math: $$...$$ (handle multiline)
        content = re.sub(r'\$\$([^$]+?)\$\$', r'\n━━━ MATH ━━━\n\1\n━━━ MATH ━━━\n', content, flags=re.DOTALL)

        # Block math: \[...\] (match literal backslash bracket)
        content = re.sub(r'\\\[(.+?)\\\]', r'\n━━━ MATH ━━━\n\1\n━━━ MATH ━━━\n', content, flags=re.DOTALL)

        # Inline math: \(...\) (LaTeX style, match literal backslash paren)
        content = re.sub(r'\\\((.+?)\\\)', r'「\1」', content, flags=re.DOTALL)

        # Inline math: $...$ (non-greedy)
        content = re.sub(r'\$([^$\n]+?)\$', r'「\1」', content)

        return content

    def _process_tables(self, content: str) -> str:
        """Convert markdown tables to readable text format"""
        lines = content.split('\n')
        result = []
        in_table = False
        table_lines = []

        for i, line in enumerate(lines):
            # Check if this looks like a table row (contains | at start and end)
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                if not in_table:
                    # Starting a new table
                    in_table = True
                    table_lines = []

                # Check if this is a separator line (e.g., |---|---|)
                # Only matches lines with pipes, dashes, colons, and spaces
                temp = stripped.replace('|', '').replace('-', '').replace(':', '').replace(' ', '')
                if len(temp) == 0:
                    table_lines.append('├' + '─' * 50 + '┤')
                    continue

                # Process table row by splitting on |
                # Remove leading and trailing | first
                inner = stripped[1:-1]
                cells = [cell.strip() for cell in inner.split('|')]
                # Escape each cell's content for Pango
                cells = [self._escape_pango(cell) for cell in cells if cell]
                if cells:
                    table_lines.append('│ ' + ' │ '.join(cells) + ' │')

            elif in_table:
                # End of table
                in_table = False
                if table_lines:
                    result.append('┌' + '─' * 50 + '┐')
                    result.extend(table_lines)
                    result.append('└' + '─' * 50 + '┘')
                    result.append('')  # Empty line after table
                result.append(line)  # Add the current line
            else:
                result.append(line)

        if in_table and table_lines:
            result.append('┌' + '─' * 50 + '┐')
            result.extend(table_lines)
            result.append('└' + '─' * 50 + '┘')

        return '\n'.join(result)

    def _escape_pango(self, text: str) -> str:
        """Escape special Pango characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;'))

    def _process_inline_markdown(self, line: str) -> str:
        """Process inline markdown (bold, italic, code) and convert to Pango markup"""
        result = self._escape_pango(line)

        # Inline math: 「math」 - render with special styling
        result = re.sub(r'「([^」]+)」', r'<i><span foreground="#9cdcfe">\1</span></i>', result)

        # Code spans: `code` -> <tt>code</tt>
        result = re.sub(r'`([^`]+)`', r'<tt><span foreground="#a9b7c6">\1</span></tt>', result)

        # Bold: **text** -> <b>text</b>
        result = re.sub(r'\*\*([^*]+)\*\*', r'<span weight="bold">\1</span>', result)

        # Italic: *text* -> <i>text</i> (but not if already part of bold)
        result = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', result)

        # Links: [text](url) -> text (in blue/underline)
        result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'<span color="#4a9eff" underline="single">\1</span>', result)

        return result

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
        'web-search-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'conversation-mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.add_css_class("chat-view")

        # Create overlay for floating navigation buttons
        self.main_overlay = Gtk.Overlay()

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

        # Add scrolled window to overlay
        self.main_overlay.set_child(self.scrolled)

        # Create floating navigation buttons
        nav_buttons = self._create_navigation_buttons()
        # Position floating buttons on right side
        self.main_overlay.add_overlay(nav_buttons)

        # Add overlay to main view
        self.append(self.main_overlay)

        # Action bar for mode selection
        self.action_bar = ActionBar()
        self.action_bar.connect("mode-changed", self._on_mode_changed)
        self.append(self.action_bar)

        # Input area
        self.input_box = self.create_input_area()
        self.append(self.input_box)

        # Typing indicator (hidden by default)
        self.typing_dots = []  # Initialize empty list (will be populated by create_typing_indicator)
        self.typing_animation_timeout = None  # Track animation timer
        self.current_dot_index = 0  # Track which dot should be highlighted
        self.typing_indicator = self.create_typing_indicator()
        self.typing_indicator.set_visible(False)

        # Welcome screen (shown when no messages)
        self.welcome_screen = self.create_welcome_screen()

        # Track message navigation
        self.current_message_index = -1

    def _on_mode_changed(self, action_bar, old_mode, new_mode):
        """Handle conversation mode change"""
        logger.info(f"Conversation mode changed from {old_mode} to {new_mode}")

        # Emit signal for main application to handle
        self.emit("conversation-mode-changed", new_mode)

        # Update web search button if mode requires it
        from nanochat.state.conversation_mode import get_mode_config
        config = get_mode_config(new_mode)

        if config.enable_web_search and not self.web_search_button.get_active():
            # Auto-enable web search for modes that require it
            self.web_search_button.set_active(True)
            logger.info(f"Auto-enabled web search for {new_mode} mode")

        # Update suggested prompts based on mode
        mode_map = {
            ConversationMode.STANDARD: "general",
            ConversationMode.CREATE: "create",
            ConversationMode.EXPLORE: "explore",
            ConversationMode.CODE: "code",
            ConversationMode.LEARN: "learn"
        }

        if new_mode in mode_map:
            mode_str = mode_map[new_mode]
            self.suggested_prompts.set_mode(mode_str)
            logger.info(f"Updated suggested prompts for {mode_str} mode")

        # Show mode indicator toast
        self._show_mode_indicator(config)

    def _on_prompt_selected(self, widget, prompt):
        """Handle suggested prompt selection"""
        logger.info(f"Suggested prompt selected: {prompt}")
        # Emit signal to send the prompt as a message
        self.emit('message-send', prompt)

    def _show_mode_indicator(self, config):
        """Show temporary indicator when mode changes"""
        # Create indicator label
        indicator = Gtk.Label()

        # Custom message for Standard mode vs other modes
        if config.name == "Standard":
            indicator.set_text("✓ Standard mode (default)")
        else:
            indicator.set_text(f"✓ {config.name} mode activated")

        indicator.add_css_class("mode-indicator")

        # Add to messages box at the top
        self.messages_box.prepend(indicator)

        # Remove after 2.5 seconds
        GLib.timeout_add(2500, self._remove_mode_indicator, indicator)

    def _remove_mode_indicator(self, indicator):
        """Remove mode indicator after timeout"""
        self.messages_box.remove(indicator)
        return False  # Don't call again

    def get_current_mode(self):
        """Get current conversation mode"""
        return self.action_bar.get_current_mode()

    def set_mode(self, mode):
        """Set conversation mode programmatically"""
        self.action_bar.set_mode(mode)

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
        text_container.add_css_class("input-container")

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
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_vexpand(True)

        # Suggested prompts widget
        self.suggested_prompts = SuggestedPrompts(mode="general")
        self.suggested_prompts.connect("prompt-selected", self._on_prompt_selected)
        box.append(self.suggested_prompts)

        return box

    def create_typing_indicator(self) -> Gtk.Box:
        """Create typing indicator widget"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.add_css_class("typing-indicator")
        box.set_halign(Gtk.Align.START)  # Align to left, don't expand to full width
        box.set_hexpand(False)  # Don't expand horizontally

        # Create three bouncing dots
        dots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        dots_box.add_css_class("typing-dots")

        self.typing_dots = []  # Clear and create new dots
        for i in range(3):
            dot = Gtk.Box()
            dot.add_css_class("typing-dot")
            dot.set_size_request(8, 8)
            dot.set_opacity(0.3)  # Start with low opacity
            dots_box.append(dot)
            self.typing_dots.append(dot)

        box.append(dots_box)
        return box

    def _create_navigation_buttons(self) -> Gtk.Box:
        """Create floating navigation buttons for message traversal"""
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        nav_box.add_css_class("navigation-buttons")

        # Position on right side with margin
        nav_box.set_halign(Gtk.Align.END)
        nav_box.set_valign(Gtk.Align.CENTER)
        nav_box.set_margin_end(12)

        # Jump to top button
        top_btn = Gtk.Button()
        top_btn.set_icon_name("pan-up")
        top_btn.set_tooltip_text("Jump to top")
        top_btn.add_css_class("navigation-button")
        top_btn.connect("clicked", self._jump_to_top)
        nav_box.append(top_btn)

        # Previous message button
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-up")
        prev_btn.set_tooltip_text("Previous message")
        prev_btn.add_css_class("navigation-button")
        prev_btn.connect("clicked", self._jump_to_previous)
        nav_box.append(prev_btn)

        # Next message button
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-down")
        next_btn.set_tooltip_text("Next message")
        next_btn.add_css_class("navigation-button")
        next_btn.connect("clicked", self._jump_to_next)
        nav_box.append(next_btn)

        # Jump to bottom button
        bottom_btn = Gtk.Button()
        bottom_btn.set_icon_name("pan-down")
        bottom_btn.set_tooltip_text("Jump to bottom")
        bottom_btn.add_css_class("navigation-button")
        bottom_btn.connect("clicked", self._jump_to_bottom)
        nav_box.append(bottom_btn)

        return nav_box

    def _jump_to_top(self, button):
        """Scroll to top of messages"""
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_lower())

    def _jump_to_bottom(self, button):
        """Scroll to bottom of messages"""
        self.scroll_to_bottom()

    def _jump_to_previous(self, button):
        """Jump to previous message"""
        messages = self._get_message_rows()
        if not messages:
            return

        # Move to previous message
        if self.current_message_index > 0:
            self.current_message_index -= 1
        elif self.current_message_index == -1:
            # Start from last message
            self.current_message_index = len(messages) - 1

        self._scroll_to_message(messages[self.current_message_index])

    def _jump_to_next(self, button):
        """Jump to next message"""
        messages = self._get_message_rows()
        if not messages:
            return

        # Move to next message
        if self.current_message_index < len(messages) - 1:
            self.current_message_index += 1
        elif self.current_message_index == -1:
            # Start from first message
            self.current_message_index = 0

        self._scroll_to_message(messages[self.current_message_index])

    def _get_message_rows(self) -> list:
        """Get all assistant message rows from messages_box"""
        messages = []
        child = self.messages_box.get_first_child()
        while child:
            if isinstance(child, MessageRow) and child.get_visible():
                # Only include assistant messages for navigation
                if child.role == 'assistant':
                    messages.append(child)
            child = child.get_next_sibling()
        return messages

    def _scroll_to_message(self, message_row):
        """Scroll to the beginning of a specific message"""
        # Get the message's position
        message_row.set_visible(True)

        # Calculate scroll position
        alloc = message_row.get_allocation()
        if alloc:
            adj = self.scrolled.get_vadjustment()
            message_y = alloc.y

            # Scroll to position the message at the top of the viewport
            target_y = message_y
            target_y = max(adj.get_lower(), min(target_y, adj.get_upper() - adj.get_page_size()))

            adj.set_value(target_y)

    def _animate_typing_indicator(self):
        """Animate typing indicator dots - cycle through them"""
        if not self.typing_dots:
            return False  # Stop animation if no dots

        # Increase opacity of current dot, decrease others
        for i, dot in enumerate(self.typing_dots):
            if i == self.current_dot_index:
                dot.set_opacity(1.0)
            else:
                dot.set_opacity(0.3)

        # Move to next dot
        self.current_dot_index = (self.current_dot_index + 1) % 3

        # Return True to keep animation running
        return True

    def show_typing_indicator(self):
        """Show typing indicator"""
        # Hide welcome screen if visible
        if self.welcome_screen.get_parent():
            self.messages_box.remove(self.welcome_screen)

        # Add typing indicator if not already present
        if not self.typing_indicator.get_parent():
            self.messages_box.append(self.typing_indicator)

        self.typing_indicator.set_visible(True)

        # Start animation (if not already running)
        if not self.typing_animation_timeout:
            self.current_dot_index = 0
            self.typing_animation_timeout = GLib.timeout_add(500, self._animate_typing_indicator)

        # Scroll to bottom to show indicator
        GLib.timeout_add(100, self.scroll_to_bottom)

    def hide_typing_indicator(self):
        """Hide typing indicator"""
        # Stop animation
        if self.typing_animation_timeout:
            GLib.source_remove(self.typing_animation_timeout)
            self.typing_animation_timeout = None

        # Remove from parent
        if self.typing_indicator.get_parent():
            self.messages_box.remove(self.typing_indicator)

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

    def toggle_web_search(self):
        """Toggle web search programmatically (for keyboard shortcut)"""
        current_state = self.web_search_button.get_active()
        self.web_search_button.set_active(not current_state)
        self.web_search_button.grab_focus()  # Focus the button to show the toggle

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
            # Find the last assistant message to update
            last_child = self.messages_box.get_last_child()
            while last_child and isinstance(last_child, MessageRow):
                if last_child.role == 'assistant':
                    # Found the last assistant message - update it
                    if content:
                        last_child.update_content(content)
                    if web_sources:
                        last_child.update_sources(web_sources)
                    break
                # If it's not an assistant message, keep looking backward
                last_child = last_child.get_prev_sibling()
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
        self.timestamp_str = timestamp

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

            # User label with timestamp
            header_box = self._create_message_header("User", timestamp)
            align_container.append(header_box)

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

            # Assistant label with timestamp
            header_box = self._create_message_header("Assistant", timestamp)
            align_container.append(header_box)

            # Assistant bubble
            self.content_widget = self._create_assistant_bubble(content)
            align_container.append(self.content_widget)

            # Web sources (if any)
            self.sources_box = None
            if web_sources:
                self.sources_box = SourcesBox(web_sources)
                align_container.append(self.sources_box)

            self.append(align_container)

    def _create_message_header(self, role_name: str, timestamp: str) -> Gtk.Box:
        """Create message header with role label and timestamp"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_halign(Gtk.Align.START)

        # Avatar (emoji)
        avatar_label = Gtk.Label(label="🤖" if role_name == "Assistant" else "👤")
        avatar_label.add_css_class("message-avatar")
        header_box.append(avatar_label)

        # Role label
        role_label = Gtk.Label(label=role_name)
        role_label.add_css_class("message-role-label")
        header_box.append(role_label)

        # Timestamp label (if provided)
        if timestamp:
            from datetime import datetime
            try:
                # Parse ISO timestamp and format relative time
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                relative_time = self._format_relative_time(ts)
                time_label = Gtk.Label(label=relative_time)
                time_label.add_css_class("message-timestamp")
                header_box.append(time_label)
            except:
                pass  # If timestamp parsing fails, just don't show it

        return header_box

    def _format_relative_time(self, dt) -> str:
        """Format datetime as relative time string"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        delta = now - dt

        seconds = delta.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            # For older messages, show the date
            return dt.strftime("%b %d, %Y")

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
        label.set_selectable(False)  # User messages don't need to be selectable
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
