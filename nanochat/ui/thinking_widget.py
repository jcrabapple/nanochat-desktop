import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango

class ThinkingWidget(Gtk.Box):
    """
    Widget to display AI reasoning/thinking process.
    Collapsible with a spinner animation while thinking is active.
    """
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("thinking-widget")
        self.set_margin_bottom(12)
        
        # Expander container
        self.expander = Gtk.Expander()
        self.expander.set_expanded(False)
        
        # Header Box (Label + Spinner)
        # We need a custom box for the label widget to hold both text and spinner
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.label = Gtk.Label(label="Thinking Process")
        self.label.add_css_class("thinking-header")
        header_box.append(self.label)
        
        self.spinner = Gtk.Spinner()
        header_box.append(self.spinner)
        
        self.expander.set_label_widget(header_box)
        
        # Content
        # Use ScrolledWindow to limit height if reasoning is very long
        self.content_scroll = Gtk.ScrolledWindow()
        self.content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content_scroll.set_max_content_height(800)  # Increased from 400 to show more reasoning
        self.content_scroll.set_propagate_natural_height(True)
        # Set minimum height so widget is always tall enough to be useful
        self.content_scroll.set_min_content_height(200)  # Always at least this tall
        
        # Text view for the reasoning content
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_monospace(True) # Usually code-like or technical
        self.text_view.add_css_class("thinking-content")
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_buffer = self.text_view.get_buffer()
        
        self.content_scroll.set_child(self.text_view)
        
        self.expander.set_child(self.content_scroll)
        self.append(self.expander)
        
        self.is_thinking = False

    def set_thinking(self, is_thinking: bool):
        """Update thinking state (spinner animation)"""
        if self.is_thinking == is_thinking:
            return
            
        self.is_thinking = is_thinking
        if is_thinking:
            self.spinner.start()
            self.label.set_label("Thinking...")
            # Auto-expand when thinking starts? Maybe not, can be distracting.
        else:
            self.spinner.stop()
            self.label.set_label("Thinking Process")
            # Auto-collapse when thinking is complete
            if self.expander.get_expanded():
                self.expander.set_expanded(False)
            
    def set_content(self, text: str):
        """Set the reasoning content text"""
        self.text_buffer.set_text(text)
        # Auto-expand if there's content and widget is visible
        if text and self.get_visible():
            # Expand to show content if it's the first time receiving content
            if not self.expander.get_expanded():
                self.expander.set_expanded(True)
        
    def append_content(self, text: str):
        """Append text to reasoning content"""
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text)
        
        # Auto-scroll to bottom of thinking if expanded
        if self.expander.get_expanded():
            adj = self.content_scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())
