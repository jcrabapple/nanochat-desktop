import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject
import logging

logger = logging.getLogger(__name__)


class SuggestedPrompts(Gtk.Box):
    """Widget displaying suggested prompts with mode-aware content"""

    __gtype_name__ = "SuggestedPrompts"

    def __init__(self, mode="general"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_valign(Gtk.Align.CENTER)

        self.current_mode = mode
        self.prompt_buttons = []

        self._build_ui()

    def _build_ui(self):
        """Build suggested prompts UI"""
        # Title
        title = Gtk.Label(label="How can I help you?")
        title.add_css_class("welcome-title")
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_top(24)
        self.append(title)

        # Subtitle based on mode
        if self.current_mode != "general":
            from nanochat.state.conversation_mode import ConversationMode, get_mode_config

            mode_map = {
                "create": ConversationMode.CREATE,
                "explore": ConversationMode.EXPLORE,
                "code": ConversationMode.CODE,
                "learn": ConversationMode.LEARN,
            }

            if self.current_mode in mode_map:
                config = get_mode_config(mode_map[self.current_mode])
                subtitle = Gtk.Label(label=f"{config.name} Mode")
                subtitle.add_css_class("welcome-subtitle")
                subtitle.set_halign(Gtk.Align.CENTER)
                self.append(subtitle)

        # Mode-specific prompts
        prompts = self._get_prompts_for_mode(self.current_mode)

        prompts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        prompts_box.set_margin_top(24)

        for prompt in prompts:
            btn = Gtk.Button(label=prompt)
            btn.add_css_class("suggested-prompt")
            btn.connect("clicked", self._on_prompt_clicked, prompt)
            prompts_box.append(btn)

        self.append(prompts_box)

    def _get_prompts_for_mode(self, mode):
        """Get suggested prompts for current mode"""
        # For now, use hardcoded prompts. Later, load from database
        default_prompts = {
            "general": [
                "How does AI work?",
                "Are black holes real?",
                "What is the meaning of life?",
                "Explain quantum computing"
            ],
            "create": [
                "Write a poem about spring",
                "Create a marketing plan for a coffee shop",
                "Draft an email to request a meeting",
                "Write a short story about time travel"
            ],
            "explore": [
                "What's the latest news in technology?",
                "Compare renewable energy sources",
                "What are the current trends in AI?",
                "Explain the history of the internet"
            ],
            "code": [
                "Write a Python function to sort a list",
                "Create a React component for a button",
                "Debug this SQL query",
                "Explain Big O notation"
            ],
            "learn": [
                "Teach me about machine learning",
                "How does blockchain technology work?",
                "Explain the basics of investing",
                "What is cognitive behavioral therapy?"
            ]
        }

        return default_prompts.get(mode, default_prompts["general"])

    def _on_prompt_clicked(self, button, prompt):
        """Handle prompt button click"""
        logger.info(f"Suggested prompt clicked: {prompt}")
        self.emit("prompt-selected", prompt)

    def set_mode(self, mode):
        """Update prompts based on mode"""
        if mode == self.current_mode:
            return

        self.current_mode = mode

        # Clear and rebuild UI
        child = self.get_first_child()
        while child:
            self.remove(child)
            child = self.get_first_child()

        self._build_ui()


# Register signal
GObject.signal_new(
    "prompt-selected",
    SuggestedPrompts,
    GObject.SignalFlags.RUN_LAST,
    GObject.TYPE_NONE,
    (GObject.TYPE_PYOBJECT,)
)
