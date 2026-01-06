# Phase 3 Implementation Plan: Advanced Features

## Overview
This plan breaks down Phase 3 into prioritized, implementable tasks with clear dependencies and file changes.

## Priority Order

### **Priority 1: Quick Wins (No Rust Required)**
These can be implemented immediately and provide immediate value:

1. **Action Buttons & Modes** (3.3)
2. **Suggested Prompts** (3.4)
3. **Basic Message Management** (3.5 - copy, delete, regenerate)

### **Priority 2: Organization Features**
Build on Priority 1:

4. **Projects/Organization** (3.2)

### **Priority 3: Advanced Features**
Requires Rust integration:

5. **Full-Text Search** (3.1)
6. **Advanced Message Management** (3.5 - edit with branching)

---

## Task Breakdown

## PRIORITY 1: QUICK WINS

### Task 1.1: Action Buttons & Modes (3.3)
**Estimated Complexity**: Medium | **Time**: 2-3 hours

**Files to Create/Modify**:
- `nanochat/ui/action_bar.py` (NEW)
- `nanochat/state/conversation_mode.py` (NEW)
- `nanochat/ui/chat_view.py` (MODIFY)
- `nanochat/ui/resources/style.css` (MODIFY)

**Implementation Steps**:

1. **Create ConversationMode enum** (`nanochat/state/conversation_mode.py`):
```python
from enum import Enum
from dataclasses import dataclass

class ConversationMode(Enum):
    STANDARD = "standard"
    CREATE = "create"
    EXPLORE = "explore"
    CODE = "code"
    LEARN = "learn"

@dataclass
class ModeConfig:
    name: str
    icon: str
    system_prompt: str
    temperature: float
    enable_web_search: bool
    description: str

MODE_CONFIGS = {
    ConversationMode.STANDARD: ModeConfig(
        name="Standard",
        icon="chat-symbolic",
        system_prompt="",
        temperature=0.7,
        enable_web_search=False,
        description="Normal conversation mode"
    ),
    ConversationMode.CREATE: ModeConfig(
        name="Create",
        icon="document-new-symbolic",
        system_prompt="You are a creative assistant. Help users create content.",
        temperature=0.8,
        enable_web_search=False,
        description="Content creation mode with higher creativity"
    ),
    ConversationMode.EXPLORE: ModeConfig(
        name="Explore",
        icon="system-search-symbolic",
        system_prompt="You are a research assistant. Provide accurate, well-sourced information.",
        temperature=0.5,
        enable_web_search=True,
        description="Research mode with web search enabled"
    ),
    ConversationMode.CODE: ModeConfig(
        name="Code",
        icon="utilities-terminal-symbolic",
        system_prompt="You are a coding assistant. Provide clean, well-commented code.",
        temperature=0.3,
        enable_web_search=False,
        description="Code generation with lower temperature for precision"
    ),
    ConversationMode.LEARN: ModeConfig(
        name="Learn",
        icon="library-symbolic",
        system_prompt="You are an educational assistant. Explain concepts step by step.",
        temperature=0.6,
        enable_web_search=True,
        description="Learning mode with explanations"
    ),
}
```

2. **Create ActionBar widget** (`nanochat/ui/action_bar.py`):
```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio
from nanochat.state.conversation_mode import ConversationMode, MODE_CONFIGS

class ActionBar(Gtk.Box):
    __gtype_name__ = "ActionBar"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(12)
        self.set_margin_bottom(12)

        self.current_mode = ConversationMode.STANDARD
        self.mode_buttons = {}

        self._build_ui()

    def _build_ui(self):
        """Build action mode buttons"""
        for mode in [
            ConversationMode.CREATE,
            ConversationMode.EXPLORE,
            ConversationMode.CODE,
            ConversationMode.LEARN
        ]:
            config = MODE_CONFIGS[mode]

            btn = Gtk.ToggleButton()
            btn.add_css_class("action-mode-button")
            btn.set_tooltip_text(config.description)

            # Icon + Label
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            icon = Gtk.Image.new_from_icon_name(config.icon)
            icon.set_pixel_size(16)
            box.append(icon)

            label = Gtk.Label(label=config.name)
            box.append(label)

            btn.set_child(box)
            btn.connect("toggled", self._on_mode_toggled, mode)
            self.append(btn)

            self.mode_buttons[mode] = btn

    def _on_mode_toggled(self, button, mode):
        """Handle mode button toggle"""
        if not button.get_active():
            # Don't allow deselecting all modes
            if self.current_mode == mode:
                button.set_active(True)
            return

        # Deselect other buttons
        for m, btn in self.mode_buttons.items():
            if m != mode:
                btn.set_active(False)

        old_mode = self.current_mode
        self.current_mode = mode

        # Emit signal with new mode
        self.emit("mode-changed", old_mode, mode)

    def get_current_mode(self) -> ConversationMode:
        """Get current active mode"""
        return self.current_mode

# Register signal
GObject.signal_new(
    "mode-changed",
    ActionBar,
    GObject.SignalFlags.RUN_LAST,
    GObject.TYPE_NONE,
    (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)
)
```

3. **Integrate into ChatView** (`nanochat/ui/chat_view.py`):
```python
from nanochat.ui.action_bar import ActionBar

class ChatView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Message area
        self.scrolled = Gtk.ScrolledWindow()
        # ... existing code ...

        # Action bar
        self.action_bar = ActionBar()
        self.action_bar.connect("mode-changed", self._on_mode_changed)
        self.pack_end(self.action_bar, False, False, 0)

        # Input area
        self.input_box = self.create_input_area()
        self.pack_end(self.input_box, False, False, 0)

    def _on_mode_changed(self, action_bar, old_mode, new_mode):
        """Handle mode change"""
        from nanochat.state.conversation_mode import MODE_CONFIGS

        config = MODE_CONFIGS[new_mode]

        # Update mode indicator in header
        self.emit("conversation-mode-changed", new_mode)

        # Show mode indicator toast
        self._show_mode_indicator(new_mode)
```

4. **Add CSS styling** (`nanochat/ui/resources/style.css`):
```css
/* Action Mode Buttons */
.action-mode-button {
    padding: 8px 16px;
    border-radius: 20px;
    background-color: #2a2b2e;
    color: #e0e0e0;
    border: 1px solid #3a3b3e;
    transition: all 200ms;
}

.action-mode-button:hover {
    background-color: #3a3b3e;
    border-color: #4a9eff;
}

.action-mode-button:checked {
    background-color: #4a9eff;
    color: #ffffff;
    border-color: #4a9eff;
}

.action-mode-button:checked image {
    -gtk-icon-effect: none;
}
```

5. **Update app state to track mode** (`nanochat/state/app_state.py`):
```python
from nanochat.state.conversation_mode import ConversationMode, MODE_CONFIGS

class ApplicationState:
    def __init__(self):
        # ... existing code ...
        self.current_conversation_mode = ConversationMode.STANDARD

    def set_conversation_mode(self, mode: ConversationMode):
        """Set current conversation mode"""
        self.current_conversation_mode = mode
        # Save to preferences

    def get_mode_config(self):
        """Get current mode configuration"""
        return MODE_CONFIGS[self.current_conversation_mode]
```

---

### Task 1.2: Suggested Prompts (3.4)
**Estimated Complexity**: Low | **Time**: 1-2 hours

**Files to Create/Modify**:
- `nanochat/ui/welcome_screen.py` (MODIFY)
- `nanochat/ui/suggested_prompts.py` (NEW)
- `nanochat/data/models.py` (MODIFY - add prompts table)

**Implementation Steps**:

1. **Create prompts database model** (`nanochat/data/models.py`):
```python
class SuggestedPrompt(Base):
    __tablename__ = 'suggested_prompts'

    id = Column(Integer, primary_key=True)
    text = Column(String(500), nullable=False)
    category = Column(String(50))  # 'general', 'create', 'explore', 'code', 'learn'
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Create SuggestedPrompts widget** (`nanochat/ui/suggested_prompts.py`):
```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class SuggestedPrompts(Gtk.Box):
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
        self.append(title)

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
        self.emit("prompt-selected", prompt)

    def set_mode(self, mode):
        """Update prompts based on mode"""
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
```

3. **Integrate into WelcomeScreen** (`nanochat/ui/welcome_screen.py`):
```python
from nanochat.ui.suggested_prompts import SuggestedPrompts

class WelcomeScreen(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Logo/Icon
        logo = Gtk.Label(label="💬")
        logo.get_style_context().add_class("welcome-logo")
        self.append(logo)

        # Title
        title = Gtk.Label(label="NanoChat")
        title.add_css_class("welcome-title")
        self.append(title)

        # Suggested prompts
        self.suggested_prompts = SuggestedPrompts(mode="general")
        self.suggested_prompts.connect("prompt-selected", self._on_prompt_selected)
        self.append(self.suggested_prompts)

    def _on_prompt_selected(self, widget, prompt):
        """Handle prompt selection"""
        self.emit("send-message", prompt)

    def update_mode(self, mode):
        """Update suggested prompts based on mode"""
        self.suggested_prompts.set_mode(mode)
```

---

### Task 1.3: Basic Message Management (3.5)
**Estimated Complexity**: Medium | **Time**: 2-3 hours

**Files to Create/Modify**:
- `nanochat/ui/message_row.py` (MODIFY)
- `nanochat/ui/chat_view.py` (MODIFY)
- `nanochat/state/app_state.py` (MODIFY)

**Implementation Steps**:

1. **Add action buttons to MessageRow** (`nanochat/ui/message_row.py`):
```python
class MessageRow(Gtk.Box):
    def __init__(self, role, content, timestamp=None, web_sources=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        # ... existing code ...

        # Action buttons (initially hidden, shown on hover)
        self.actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.actions_box.add_css_class("message-actions")
        self.actions_box.set_visible(False)

        # Copy button
        copy_btn = Gtk.Button()
        copy_btn.set_icon_name("edit-copy-symbolic")
        copy_btn.set_tooltip_text("Copy")
        copy_btn.add_css_class("flat")
        copy_btn.connect("clicked", self._on_copy_clicked)
        self.actions_box.append(copy_btn)

        # Regenerate button (assistant messages only)
        if role == "assistant":
            regenerate_btn = Gtk.Button()
            regenerate_btn.set_icon_name("view-refresh-symbolic")
            regenerate_btn.set_tooltip_text("Regenerate")
            regenerate_btn.add_css_class("flat")
            regenerate_btn.connect("clicked", self._on_regenerate_clicked)
            self.actions_box.append(regenerate_btn)

        # Delete button
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("edit-delete-symbolic")
        delete_btn.set_tooltip_text("Delete")
        delete_btn.add_css_class("flat")
        delete_btn.connect("clicked", self._on_delete_clicked)
        self.actions_box.append(delete_btn)

        self.append(self.actions_box)

        # Show actions on hover
        self.connect("enter-notify-event", lambda *_: self.actions_box.set_visible(True))
        self.connect("leave-notify-event", lambda *_: self.actions_box.set_visible(False))

    def _on_copy_clicked(self, button):
        """Handle copy button click"""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_content(Gdk.ContentProvider.new_for_value(self.content))
        self.emit("message-copied")

    def _on_regenerate_clicked(self, button):
        """Handle regenerate button click"""
        self.emit("regenerate-message", self)

    def _on_delete_clicked(self, button):
        """Handle delete button click"""
        self.emit("delete-message", self)
```

2. **Handle message actions in ChatView** (`nanochat/ui/chat_view.py`):
```python
class ChatView(Gtk.Box):
    def add_message(self, role, content, web_sources=None, update_last=False):
        """Add message to chat view"""
        if update_last:
            # Update last message
            last_child = self.messages_box.get_last_child()
            if last_child:
                self.messages_box.remove(last_child)

        row = MessageRow(role, content, web_sources=web_sources)
        row.connect("message-copied", self._on_message_copied)
        row.connect("regenerate-message", self._on_regenerate_message)
        row.connect("delete-message", self._on_delete_message)

        self.messages_box.append(row)

        # Scroll to bottom
        self._scroll_to_bottom()

    def _on_regenerate_message(self, message_row):
        """Handle message regeneration"""
        # Remove all messages after this one
        self._remove_messages_after(message_row)

        # Emit signal to regenerate
        self.emit("regenerate-response")

    def _on_delete_message(self, message_row):
        """Handle message deletion"""
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            text="Delete this message?",
            secondary_text="This action cannot be undone.",
            buttons=Gtk.ButtonsType.YES_NO
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.messages_box.remove(message_row)
            self.emit("message-deleted")
```

3. **Update app state to handle regeneration** (`nanochat/state/app_state.py`):
```python
async def regenerate_last_response(self):
    """Regenerate the last assistant message"""
    # Get conversation history
    messages = self.get_conversation_messages(self.current_conversation_id)

    # Remove last assistant message
    if messages and messages[-1]['role'] == 'assistant':
        with self.db.get_session() as session:
            msg_repo = MessageRepository(session)
            # Delete last message
            msg_repo.delete_message(messages[-1]['id'])

    # Re-send user's last message (or second-to-last if we just deleted)
    if len(messages) >= 2:
        user_msg = messages[-2] if messages[-1]['role'] == 'assistant' else messages[-1]
        async for role, content, web_sources in self.send_message(user_msg['content'], False):
            yield (role, content, web_sources)
```

4. **Add CSS for message actions** (`nanochat/ui/resources/style.css`):
```css
.message-actions {
    opacity: 0;
    transition: opacity 200ms;
}

.message-row:hover .message-actions {
    opacity: 1;
}

.message-actions button {
    padding: 4px 8px;
    min-width: 32px;
    min-height: 32px;
    border-radius: 16px;
    background-color: rgba(255, 255, 255, 0.05);
}

.message-actions button:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
```

---

## PRIORITY 2: ORGANIZATION FEATURES

### Task 2.1: Projects/Organization (3.2)
**Estimated Complexity**: High | **Time**: 4-6 hours

**Files to Create/Modify**:
- `nanochat/data/models.py` (MODIFY - add projects table)
- `nanochat/ui/sidebar.py` (MODIFY)
- `nanochat/ui/project_dialog.py` (NEW)
- `nanochat/state/project_manager.py` (NEW)

**Implementation Steps**:

1. **Create project database model** (`nanochat/data/models.py`):
```python
class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default='#4a9eff')  # Hex color
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order_index = Column(Integer, default=0)

    # Relationship with conversations
    conversations = relationship("Conversation", back_populates="project")

# Update Conversation model
class Conversation(Base):
    # ... existing fields ...
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="conversations")
```

2. **Create project manager** (`nanochat/state/project_manager.py`):
```python
from nanochat.data.models import Project
from nanochat.data.repository import ProjectRepository

class ProjectManager:
    def __init__(self, db):
        self.db = db

    def create_project(self, name, color='#4a9eff', description=''):
        """Create a new project"""
        with self.db.get_session() as session:
            repo = ProjectRepository(session)
            project = repo.create_project(
                name=name,
                color=color,
                description=description
            )
            return project

    def get_all_projects(self):
        """Get all projects ordered"""
        with self.db.get_session() as session:
            repo = ProjectRepository(session)
            return repo.get_all_projects()

    def assign_conversation_to_project(self, conversation_id, project_id):
        """Assign conversation to project"""
        with self.db.get_session() as session:
            repo = ProjectRepository(session)
            repo.assign_conversation(conversation_id, project_id)

    def delete_project(self, project_id):
        """Delete project (conversations move to 'No Project')"""
        with self.db.get_session() as session:
            repo = ProjectRepository(session)
            repo.delete_project(project_id)
```

3. **Create project dialog** (`nanochat/ui/project_dialog.py`):
```python
class ProjectDialog(Gtk.Dialog):
    def __init__(self, parent=None, project=None):
        super().__init__(
            title="New Project" if not project else "Edit Project",
            parent=parent,
            modal=True
        )

        self.project = project
        self._build_ui()

    def _build_ui(self):
        """Build dialog UI"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Name entry
        name_label = Gtk.Label(label="Project Name:")
        name_label.set_xalign(0)
        box.append(name_label)

        self.name_entry = Gtk.Entry()
        if self.project:
            self.name_entry.set_text(self.project.name)
        box.append(self.name_entry)

        # Color picker (simplified as combo box)
        color_label = Gtk.Label(label="Color:")
        color_label.set_xalign(0)
        box.append(color_label)

        colors = ['#4a9eff', '#ff6b6b', '#51cf66', '#ffd43b', '#cc5de8']
        self.color_chooser = Gtk.ComboBoxText()
        for color in colors:
            self.color_chooser.append_text(color)
        self.color_chooser.set_active(0)
        box.append(self.color_chooser)

        # Description (optional)
        desc_label = Gtk.Label(label="Description (optional):")
        desc_label.set_xalign(0)
        box.append(desc_label)

        self.desc_buffer = Gtk.TextBuffer()
        desc_view = Gtk.TextView(buffer=self.desc_buffer)
        desc_view.set_size_request(-1, 100)
        box.append(desc_view)

        # Buttons
        buttons = self.get_content_area()
        buttons.append(box)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)

        self.set_default_size(400, 300)
```

4. **Update sidebar to show projects** (`nanochat/ui/sidebar.py`):
```python
class Sidebar(Gtk.Box):
    def __init__(self, app_state):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.app_state = app_state

        # New Chat button
        # Search entry
        # ... existing ...

        # Projects section
        self.projects_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.projects_expander = Gtk.Expander(label="PROJECTS")
        self.projects_expander.set_child(self.projects_box)
        self.pack_start(self.projects_expander, False, False, 0)

        # "No Project" section
        self.no_project_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        no_project_header = Gtk.Label(label="NO PROJECT")
        no_project_header.add_css_class("conversation-group-header")
        self.no_project_box.append(no_project_header)

        # Scrolled window for conversations
        # ... existing ...

        self._load_projects()
        self._load_conversations()

    def _load_projects(self):
        """Load and display projects"""
        projects = self.app_state.project_manager.get_all_projects()

        # Clear existing project buttons
        child = self.projects_box.get_first_child()
        while child:
            self.projects_box.remove(child)
            child = self.projects_box.get_first_child()

        for project in projects:
            project_btn = Gtk.Button(label=project.name)
            project_btn.add_css_class("project-button")
            # Set color
            color_provider = Gtk.CssProvider()
            css = f".project-button {{ border-left: 3px solid {project.color}; }}"
            color_provider.load_from_data(css.encode())

            project_btn.connect("clicked", self._on_project_clicked, project.id)
            self.projects_box.append(project_btn)

    def _on_project_clicked(self, button, project_id):
        """Filter conversations by project"""
        self.current_project_filter = project_id
        self._load_conversations()
```

---

## PRIORITY 3: ADVANCED FEATURES

### Task 3.1: Full-Text Search (3.1)
**Estimated Complexity**: Very High | **Time**: 8-12 hours (requires Rust)

**This task requires Rust integration and should be done last.**

See nanochat_full_plan.md lines 686-717 for full Rust implementation details.

---

## DEPENDENCY GRAPH

```
Priority 1 (Quick Wins)
├── Task 1.1: Action Buttons & Modes
│   └── No dependencies
├── Task 1.2: Suggested Prompts
│   └── Can integrate with Task 1.1 (mode-aware prompts)
└── Task 1.3: Basic Message Management
    └── No dependencies

Priority 2 (Organization)
└── Task 2.1: Projects/Organization
    ├── Can use modes from Task 1.1
    └── Can organize messages from Task 1.3

Priority 3 (Advanced)
└── Task 3.1: Full-Text Search (Rust)
    ├── Requires Rust build setup
    ├── Can search across all Priority 1 & 2 features
    └── Should be done last
```

---

## IMPLEMENTATION ORDER

### Week 1: Quick Wins
1. **Day 1-2**: Task 1.1 - Action Buttons & Modes
2. **Day 3**: Task 1.2 - Suggested Prompts
3. **Day 4-5**: Task 1.3 - Basic Message Management

### Week 2: Organization
4. **Day 1-3**: Task 2.1 - Projects/Organization

### Week 3+: Advanced (Optional)
5. **When ready**: Task 3.1 - Full-Text Search with Rust

---

## TESTING CHECKLIST

For each task, verify:
- [ ] Feature works as expected
- [ ] UI looks good and is responsive
- [ ] Keyboard shortcuts work
- [ ] Error handling is graceful
- [ ] Data persists across restarts
- [ ] No performance issues

---

## NEXT STEPS

1. **Choose which task to start with** - I recommend Task 1.1 (Action Buttons & Modes)

2. **Create feature branch**:
   ```bash
   git checkout -b feature/action-modes
   ```

3. **Start implementing** following the detailed steps above

Would you like me to start implementing Task 1.1 (Action Buttons & Modes) now?
