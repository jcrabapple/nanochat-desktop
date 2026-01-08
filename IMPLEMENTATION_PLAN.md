# NanoChat Desktop - Implementation Plan

## Current Status Assessment

Based on analysis of the codebase, here's what's **already implemented**:

### ✅ Completed Features

#### Phase 1 & 2 (Foundation & Core Features)
- **Project Structure**: Complete Python package with proper organization
- **API Client**: `nanochat/api/client.py` - NanoGPT integration with streaming support
- **Database Layer**: SQLite with SQLAlchemy ORM models for conversations and messages
- **Main Window**: GTK4 application shell with header bar, sidebar, and chat view
- **Sidebar**: Conversation list with date grouping, search, rename, delete, and context menus
- **Chat View**: Message display area with markdown rendering, web search toggle, streaming responses
- **Settings Dialog**: API configuration, model selection, appearance settings, web search options
- **Web Search Integration**: Toggle in header, dual API endpoints, source display
- **Action Bar**: Mode selection buttons (Create, Explore, Code, Learn) - `action_bar.py`
- **Conversation Modes**: Mode system with config - `conversation_mode.py`
- **Suggested Prompts**: Mode-based prompt suggestions - `suggested_prompts.py`
- **Markdown Rendering**: Using markdown library with Pygments for syntax highlighting
- **Dark Theme CSS**: Complete styling

### 🔄 Partially Implemented

- **Message Management**: Basic copy functionality exists, regeneration and deletion need work

### ❌ Not Yet Implemented (From Phase 3)

1. **Projects/Organization** (Task 3.2)
   - Project folders for organizing conversations
   - Drag-and-drop organization
   - Color-coded project folders

2. **Full-Text Search** (Task 3.1)
   - Rust-based search engine with Tantivy
   - Global search across all conversations
   - Search overlay UI

3. **Advanced Message Management** (Task 3.5)
   - Edit sent messages with branching
   - Full delete with confirmation
   - Message bookmarking/starring

4. **Performance Layer (Rust)** 
   - Fast search indexing
   - Message parsing optimization
   - Data compression

---

## Priority Implementation Order

### 🎯 Priority 1: Projects/Organization (HIGH VALUE, NO RUST)
**Estimated Time: 4-6 hours**

This provides immediate organizational value without requiring Rust setup.

#### Files to Create/Modify:
- `nanochat/data/models.py` - Add Project model
- `nanochat/data/repository.py` - Add ProjectRepository  
- `nanochat/ui/project_dialog.py` - **NEW** - Create/edit project dialog
- `nanochat/ui/sidebar.py` - Add projects section with expandable folders
- `nanochat/state/project_manager.py` - **NEW** - Project CRUD operations
- `nanochat/ui/resources/style.css` - Project styling

#### Implementation Steps:

**Step 1: Database Schema Update**
```python
# Add to models.py
class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default='#4a9eff')  # Hex color
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order_index = Column(Integer, default=0)

# Update Conversation model
class Conversation(Base):
    # Add:
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
```

**Step 2: Project Manager**
- Create `project_manager.py` with CRUD operations
- Methods: create_project, get_all_projects, delete_project, assign_conversation_to_project

**Step 3: Project Dialog UI**
- Create `project_dialog.py` with name, color picker, description fields
- Add validation for project names

**Step 4: Sidebar Integration**
- Add collapsible "PROJECTS" section above conversation list
- Show project color indicator
- Filter conversations by project when clicked
- Add "New Project" button

**Step 5: Context Menu Integration**
- Add "Move to Project" option in conversation context menu
- Show available projects in submenu

---

### 🎯 Priority 2: Enhanced Message Management (MEDIUM, NO RUST)
**Estimated Time: 2-3 hours**

#### Files to Modify:
- `nanochat/ui/chat_view.py` - Add message action buttons
- `nanochat/state/app_state.py` - Add regenerate/delete logic
- `nanochat/ui/resources/style.css` - Action button styling

#### Implementation Steps:

**Step 1: Action Buttons on Messages**
- Add hover-visible action buttons to message rows
- Copy button (already partially exists)
- Regenerate button (assistant messages only)
- Delete button with confirmation dialog

**Step 2: Regenerate Functionality**
- Delete last assistant message
- Re-send user's last message
- Stream new response

**Step 3: Delete Messages**
- Show confirmation dialog
- Update database
- Remove from UI
- Handle conversation continuity

---

### 🎯 Priority 3: Keyboard Shortcuts (LOW EFFORT, HIGH VALUE)
**Estimated Time: 1-2 hours**

#### Implementation Steps:

**Step 1: Define Shortcuts Map**
```python
shortcuts = {
    "<Ctrl>N": "new_chat",
    "<Ctrl>F": "search",
    "<Ctrl>W": "toggle_web_search",
    "<Ctrl>comma": "open_settings",
    "<Ctrl>Q": "quit",
    "<Ctrl>Return": "send_message",
    "<Ctrl>1": "mode_standard",
    "<Ctrl>2": "mode_create",
    "<Ctrl>3": "mode_explore",
    "<Ctrl>4": "mode_code",
    "<Ctrl>5": "mode_learn",
}
```

**Step 2: Register Shortcuts in MainWindow**
- Add GTK action for each shortcut
- Connect to appropriate handlers

**Step 3: Shortcuts Help Overlay**
- Create help dialog showing all shortcuts
- Trigger with Ctrl+?

---

### 🎯 Priority 4: Export/Import Conversations (MEDIUM)
**Estimated Time: 2-3 hours**

#### Files to Create/Modify:
- `nanochat/utils/export.py` - **NEW** - Export functionality
- `nanochat/ui/sidebar.py` - Add export option to context menu
- `nanochat/ui/main_window.py` - Add import menu option

#### Supported Formats:
- **Markdown** (.md) - Human-readable with formatting
- **JSON** (.json) - For backup/restore
- **PDF** (.pdf) - Using weasyprint (optional dependency)

---

### 🎯 Priority 5: Rust Integration & Full-Text Search (FUTURE)
**Estimated Time: 8-12 hours**

This requires setting up the Rust toolchain and PyO3 bindings.

#### Components:
1. **Search Engine** - Tantivy-based full-text search
2. **Message Parser** - Fast markdown rendering with Syntect
3. **Compression** - zstd compression for large conversations

---

## Recommended Implementation Sequence

### Phase A: Quick Wins (1-2 days)
1. ✓ Keyboard shortcuts
2. ✓ Enhanced message management (copy, regenerate, delete)

### Phase B: Organization (2-3 days)
3. ✓ Projects/Folders system
4. ✓ Export conversations

### Phase C: Performance (Future)
5. ✓ Rust integration
6. ✓ Full-text search

---

## Immediate Next Steps

1. **Start with Projects/Organization** - This is the highest-value feature that doesn't require Rust
2. **Then Keyboard Shortcuts** - Quick win that improves usability
3. **Then Export** - Frequently requested feature

Would you like me to start implementing any of these features?

---

## 🆕 UI Improvements (Inspired by Newelle Project)

These enhancements are based on patterns from the [Newelle](https://github.com/qwersyk/Newelle) GTK4 chat application.

### Quick Wins (Low Effort, High Impact)
- [x] **Toast Notifications** ⏱️ 30 mins (Implemented)
- [x] **Responsive Layout with Breakpoints** ⏱️ 1 hour (Implemented)
- [x] **Stop Generation Button** ⏱️ 1 hour (Implemented)
- [x] **Continue Button** ⏱️ 30 mins (Implemented)
- [x] **Centered Conversation Titles** (Implemented)

#### 1. **Toast Notifications**
Show temporary "Copied to clipboard" notification when copying messages.
```python
# Use Adw.ToastOverlay
notification_block = Adw.ToastOverlay()
notification_block.add_toast(Adw.Toast(title="Copied to clipboard", timeout=2))
```

#### 2. **Responsive Layout with Breakpoints**
Auto-collapse sidebar on narrow windows.

#### 3. **Stop Generation Button**
Allow users to stop message generation mid-stream.
- Show "Stop" button while generating
- Cancel API request when clicked
- Keep partial response

#### 4. **Continue Button**
Continue generating if response was cut off.
- Detect truncated responses
- Send "continue" prompt with context

### Medium Effort Improvements

#### 5. **ThinkingWidget for Reasoning Models** ⏱️ 2-3 hours
Collapsible widget showing AI thinking process.
- Works with Claude's `<think>` blocks
- Animated spinner during thinking
- Expandable text showing reasoning

#### 6. **Code Syntax Highlighting with GtkSource** ⏱️ 2-3 hours
Replace basic code blocks with proper syntax highlighting.
```python
from gi.repository import GtkSource
sourceview = GtkSource.View(monospace=True)
manager = GtkSource.LanguageManager.new()
language = manager.get_language("python")
buffer.set_language(language)
```

#### 7. **File Drag-and-Drop** ⏱️ 2 hours
Allow dragging files into chat.
```python
drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
drop_target.connect("drop", self.handle_file_drag)
self.chat_view.add_controller(drop_target)
```

#### 8. **Chat Switch Animations** ⏱️ 1 hour
Smooth slide animations when switching conversations.
```python
chat_stack = Gtk.Stack(
    transition_type=Gtk.StackTransitionType.SLIDE_UP, 
    transition_duration=300
)
```

### Future Enhancements

#### 9. **Voice Input (Mic Button)** ⏱️ 4-6 hours
- Add microphone button next to input
- Record audio and transcribe
- Requires STT integration

#### 10. **Profile System** ⏱️ 4-6 hours
- Multiple assistant personalities
- Per-profile settings
- Profile-specific system prompts

#### 11. **Zoom Support** ⏱️ 1 hour
- Allow UI scaling
- Persist zoom level in settings

---

## Implementation Notes

### GTK4 Best Practices (from Newelle)

1. **Thread Safety**: Always use `GLib.idle_add()` for UI updates from background threads
2. **Widget Sizing**: Use `width_chars=1` with `wrap=True` to prevent Labels from expanding
3. **Dynamic Sizing**: Use `create_pango_layout()` to calculate text dimensions
4. **Transparent Backgrounds**: Use `apply_css_to_widget()` helper for inline CSS
5. **Responsive Design**: Use `Adw.Breakpoint` for adaptive layouts

### Reference Code Patterns

```python
# Apply inline CSS to a widget
def apply_css_to_widget(widget, css_string):
    provider = Gtk.CssProvider()
    provider.load_from_data(css_string.encode())
    widget.get_style_context().add_provider(
        provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

# Scroll to bottom of text
def scroll_to_end(textview, textbuffer):
    end_iter = textbuffer.get_end_iter()
    end_mark = textbuffer.create_mark("end_mark", end_iter, False)
    textview.scroll_to_mark(end_mark, 0.0, True, 0.0, 1.0)
    GLib.idle_add(textbuffer.delete_mark, end_mark)
```
