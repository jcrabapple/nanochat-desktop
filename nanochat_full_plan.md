# NanoChat Desktop - Complete Development Plan

## Project Overview
A desktop AI chat application built with Python (backend/logic), Rust (performance-critical components), and GTK4 (UI), integrating with the NanoGPT API. The application features conversation management, web search integration, and a modern dark-themed interface.

## Architecture

### Core Components

#### 1. **Backend Layer (Python)**

**API Client Module** (`nanochat/api/client.py`)
- NanoGPT API integration with dual endpoints:
  - Base URL: `https://nano-gpt.com/api`
  - Chat endpoint: `/v1/chat/completions`
  - Web search endpoint: `/web`
- Request/response handling with streaming support
- Authentication management
- Rate limiting and retry logic with exponential backoff
- Connection pooling for better performance
- Error handling with user-friendly messages

```python
class NanoGPTClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.web_endpoint = f"{base_url}/web"
        self.standard_endpoint = f"{base_url}/v1/chat/completions"
        self.timeout = aiohttp.ClientTimeout(total=60)
    
    async def send_message(
        self, 
        message: str, 
        conversation_history: list,
        use_web_search: bool = False,
        stream: bool = True
    ):
        """Send message with optional web search"""
        endpoint = self.web_endpoint if use_web_search else self.standard_endpoint
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": conversation_history,
                        "stream": stream,
                        "web_search": use_web_search
                    }
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise APIError(error_data.get('error', 'Unknown error'))
                    
                    if stream:
                        async for chunk in response.content.iter_chunked(1024):
                            yield self.parse_stream_chunk(chunk)
                    else:
                        data = await response.json()
                        yield self.parse_response(data)
            except aiohttp.ClientError as e:
                raise APIError(f"Connection error: {str(e)}")
            except asyncio.TimeoutError:
                raise APIError("Request timed out")
```

**Data Layer** (`nanochat/data/`)
- SQLite database for chat history with efficient indexing
- Conversation management (CRUD operations)
- Message storage and retrieval with pagination
- Full-text search preparation (indexed columns)
- Export/import capabilities (JSON, Markdown, PDF)
- Database migrations system
- Automatic backups

**State Management** (`nanochat/state/`)
- Application state controller using observer pattern
- Active conversation tracking
- User preferences storage and caching
- Session management
- Undo/redo functionality for message editing
- WebSocket connection management for real-time updates

#### 2. **Performance Layer (Rust)**

**Fast Search Engine** (`rust/src/search/`)
- Full-text search indexing using Tantivy
- Vector similarity search for semantic queries
- Fuzzy matching for typo tolerance
- Incremental indexing for real-time updates
- Compile as Python extension using PyO3

```rust
use pyo3::prelude::*;
use tantivy::Index;

#[pyfunction]
fn search_conversations(query: &str, conversations: Vec<String>) -> PyResult<Vec<usize>> {
    // Fast search implementation with ranking
    let results = search_engine::search(query, &conversations)?;
    Ok(results.into_iter().map(|r| r.doc_id).collect())
}

#[pyclass]
pub struct SearchIndex {
    index: Index,
}

#[pymethods]
impl SearchIndex {
    #[new]
    fn new(index_path: &str) -> PyResult<Self> {
        // Initialize search index
        Ok(SearchIndex { index: create_index(index_path)? })
    }
    
    fn add_document(&mut self, doc_id: usize, content: &str) -> PyResult<()> {
        // Add document to index
        Ok(())
    }
}
```

**Message Parser** (`rust/src/parser/`)
- Markdown rendering optimization with CommonMark
- Code syntax highlighting using Syntect
- Link detection and validation
- Math formula rendering (LaTeX support)
- Table formatting
- Emoji rendering

**Data Compression** (`rust/src/compression/`)
- Chat history compression using zstd
- Efficient storage utilities
- Batch compression for exports
- Decompression streaming for large conversations

#### 3. **UI Layer (GTK4 + Python)**

**Main Window** (`nanochat/ui/main_window.py`)
- Application shell with responsive layout
- Header bar with search, web search toggle, and settings
- Sidebar/main content split view with resizable panes
- Keyboard shortcut overlay (Ctrl+?)
- Status bar for connection status and statistics

**Header Bar Component** (`nanochat/ui/header_bar.py`)
```python
class HeaderBar(Gtk.HeaderBar):
    def __init__(self):
        super().__init__()
        self.set_show_title_buttons(True)
        
        # Title
        self.set_title_widget(Gtk.Label(label="NanoChat Desktop"))
        
        # Search button
        self.search_button = Gtk.ToggleButton()
        self.search_button.set_icon_name("system-search-symbolic")
        self.search_button.set_tooltip_text("Search (Ctrl+F)")
        self.pack_end(self.search_button)
        
        # Web search toggle
        self.web_search_toggle = Gtk.ToggleButton()
        self.web_search_toggle.set_icon_name("network-wireless-symbolic")
        self.web_search_toggle.set_tooltip_text("Enable Web Search (Ctrl+W)")
        self.web_search_toggle.connect("toggled", self.on_web_search_toggled)
        self.pack_end(self.web_search_toggle)
        
        # Settings button
        self.settings_button = Gtk.Button()
        self.settings_button.set_icon_name("preferences-system-symbolic")
        self.settings_button.set_tooltip_text("Settings")
        self.pack_end(self.settings_button)
        
        # Menu button
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")
        self.pack_end(self.menu_button)
    
    def on_web_search_toggled(self, button):
        is_active = button.get_active()
        if is_active:
            button.add_css_class("suggested-action")
            button.set_tooltip_text("Web Search Enabled")
        else:
            button.remove_css_class("suggested-action")
            button.set_tooltip_text("Enable Web Search (Ctrl+W)")
        
        self.emit("web-search-changed", is_active)
```

**Sidebar Component** (`nanochat/ui/sidebar.py`)
- "New Chat" button with prominent styling
- Search threads input with real-time filtering
- Project organization section with collapsible folders
- Date-grouped conversation list:
  - Today
  - Last 7 Days
  - Last 30 Days
  - Older (with pagination)
- Conversation selection with hover effects
- Right-click context menu (rename, delete, export, move to project)
- Drag-and-drop to reorder or move to projects

```python
class Sidebar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_size_request(280, -1)
        
        # New Chat button
        self.new_chat_btn = Gtk.Button(label="New Chat")
        self.new_chat_btn.add_css_class("suggested-action")
        self.new_chat_btn.set_margin_start(12)
        self.new_chat_btn.set_margin_end(12)
        self.new_chat_btn.set_margin_top(12)
        self.new_chat_btn.set_margin_bottom(12)
        self.pack_start(self.new_chat_btn, False, False, 0)
        
        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search threads...")
        self.search_entry.set_margin_start(12)
        self.search_entry.set_margin_end(12)
        self.search_entry.set_margin_bottom(12)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.pack_start(self.search_entry, False, False, 0)
        
        # Projects section
        self.projects_expander = Gtk.Expander(label="PROJECTS")
        self.projects_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.projects_expander.set_child(self.projects_box)
        self.pack_start(self.projects_expander, False, False, 0)
        
        # Scrolled window for conversations
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Conversations list
        self.conversations_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.scrolled.set_child(self.conversations_box)
        self.pack_start(self.scrolled, True, True, 0)
        
    def populate_conversations(self, conversations: list):
        """Populate sidebar with grouped conversations"""
        groups = self.group_by_date(conversations)
        
        for group_name, convos in groups.items():
            # Group header
            header = Gtk.Label(label=group_name.upper())
            header.add_css_class("conversation-group-header")
            header.set_xalign(0)
            header.set_margin_start(16)
            header.set_margin_top(8)
            self.conversations_box.append(header)
            
            # Conversations in group
            for convo in convos:
                row = ConversationRow(convo)
                self.conversations_box.append(row)
```

**Chat View** (`nanochat/ui/chat_view.py`)
- Welcome screen with action buttons and suggested prompts
- Message display area with markdown support and smooth scrolling
- Code block rendering with syntax highlighting and copy button
- Message input area with:
  - Multi-line text entry (auto-expanding)
  - Send button
  - Attachment button (for future file support)
  - Character/token counter
  - Typing indicator when AI is responding
- Action buttons (Create, Explore, Code, Learn)
- Suggested prompts display based on context
- Auto-scroll to bottom on new messages
- Message regeneration button
- Edit message functionality

```python
class ChatView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Message area
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.messages_box.set_margin_start(24)
        self.messages_box.set_margin_end(24)
        self.messages_box.set_margin_top(24)
        self.scrolled.set_child(self.messages_box)
        self.pack_start(self.scrolled, True, True, 0)
        
        # Input area
        self.input_box = self.create_input_area()
        self.pack_end(self.input_box, False, False, 0)
    
    def create_input_area(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_bottom(24)
        box.set_margin_top(12)
        
        # Action buttons row
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for action in ["Create", "Explore", "Code", "Learn"]:
            btn = Gtk.Button(label=action)
            btn.add_css_class("flat")
            actions_box.append(btn)
        box.append(actions_box)
        
        # Input row
        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_accepts_tab(False)
        self.text_view.add_css_class("message-input")
        
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        text_scroll.set_max_content_height(200)
        text_scroll.set_child(self.text_view)
        input_row.append(text_scroll)
        
        self.send_button = Gtk.Button()
        self.send_button.set_icon_name("mail-send-symbolic")
        self.send_button.add_css_class("suggested-action")
        self.send_button.set_valign(Gtk.Align.END)
        input_row.append(self.send_button)
        
        box.append(input_row)
        return box
    
    def add_message(self, message: Message):
        """Add a message to the chat view"""
        row = MessageRow(message)
        self.messages_box.append(row)
        
        # Auto-scroll to bottom
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
```

**Message Row Component** (`nanochat/ui/message_row.py`)
```python
class MessageRow(Gtk.Box):
    def __init__(self, message: Message):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.message = message
        
        # Message header (avatar, role, timestamp)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        avatar = Gtk.Label(label="🤖" if message.role == "assistant" else "👤")
        header.append(avatar)
        
        role_label = Gtk.Label(label=message.role.capitalize())
        role_label.add_css_class("message-role")
        header.append(role_label)
        
        timestamp = Gtk.Label(label=self.format_timestamp(message.created_at))
        timestamp.add_css_class("message-timestamp")
        timestamp.set_hexpand(True)
        timestamp.set_xalign(1)
        header.append(timestamp)
        
        self.append(header)
        
        # Web search indicator
        if message.used_web_search:
            web_indicator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            web_indicator.add_css_class("message-web-indicator")
            
            icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic")
            web_indicator.append(icon)
            
            label = Gtk.Label(label="Used web search")
            web_indicator.append(label)
            
            self.append(web_indicator)
        
        # Message content (with markdown rendering)
        content = self.render_markdown(message.content)
        self.append(content)
        
        # Web sources section
        if message.used_web_search and message.web_sources:
            sources_section = self.create_sources_section(message.web_sources)
            self.append(sources_section)
        
        # Action buttons (copy, regenerate, etc.)
        actions = self.create_action_buttons()
        self.append(actions)
    
    def create_sources_section(self, sources: list):
        """Display web sources used in the response"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("web-sources")
        
        header = Gtk.Label(label="Sources:")
        header.add_css_class("sources-header")
        header.set_xalign(0)
        box.append(header)
        
        for i, source in enumerate(sources, 1):
            source_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            
            num_label = Gtk.Label(label=f"[{i}]")
            num_label.add_css_class("source-number")
            source_box.append(num_label)
            
            link = Gtk.LinkButton.new_with_label(
                source.get('url', '#'),
                source.get('title', 'Untitled')
            )
            link.add_css_class("source-link")
            source_box.append(link)
            
            box.append(source_box)
        
        return box
    
    def render_markdown(self, content: str) -> Gtk.Widget:
        """Render markdown content with syntax highlighting"""
        # Use Rust parser for performance
        html = nanochat_rust.parse_markdown(content)
        
        # Create TextView or use WebKit for rich rendering
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        
        buffer = text_view.get_buffer()
        buffer.set_text(content)  # Simplified; use proper markdown rendering
        
        return text_view
```

**Settings Dialog** (`nanochat/ui/settings.py`)
- API Configuration
  - API key input (masked)
  - Base URL configuration
  - Connection test button
- Model Selection
  - Dropdown for available models
  - Model description and capabilities
  - Temperature slider
  - Max tokens slider
- Web Search Settings
  - Enable web search by default
  - Web search timeout
  - Maximum sources to display
- Appearance
  - Theme selection (dark/light/system)
  - Font family and size
  - Message spacing
  - Sidebar width
- Privacy
  - Clear conversation history
  - Export all data
  - Delete account data
- Keyboard Shortcuts
  - Customizable shortcuts list
  - Reset to defaults

**Welcome Screen** (`nanochat/ui/welcome_screen.py`)
```python
class WelcomeScreen(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        
        # Title
        title = Gtk.Label(label="How can I help you?")
        title.add_css_class("welcome-title")
        self.append(title)
        
        # Action buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_box.set_halign(Gtk.Align.CENTER)
        actions_box.set_margin_top(24)
        
        actions = [
            ("Create", "document-new-symbolic"),
            ("Explore", "system-search-symbolic"),
            ("Code", "utilities-terminal-symbolic"),
            ("Learn", "library-symbolic")
        ]
        
        for label, icon in actions:
            btn = Gtk.Button()
            btn.add_css_class("pill")
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.append(Gtk.Image.new_from_icon_name(icon))
            box.append(Gtk.Label(label=label))
            btn.set_child(box)
            
            actions_box.append(btn)
        
        self.append(actions_box)
        
        # Suggested prompts
        prompts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        prompts_box.set_margin_top(48)
        prompts_box.set_halign(Gtk.Align.CENTER)
        
        prompts = [
            "How does AI work?",
            "Are black holes real?",
            "How many Rs are in the word 'strawberry'?",
            "What is the meaning of life?"
        ]
        
        for prompt in prompts:
            btn = Gtk.Button(label=prompt)
            btn.add_css_class("flat")
            btn.add_css_class("suggested-prompt")
            prompts_box.append(btn)
        
        self.append(prompts_box)
```

## Feature Implementation Plan

### Phase 1: Foundation (Week 1-2)

**1.1 Project Setup**
- Initialize Python project structure
  ```bash
  mkdir -p nanochat/{api,data,state,ui,utils}
  touch nanochat/__init__.py
  ```
- Create `pyproject.toml` with dependencies
- Set up Rust workspace
  ```bash
  cargo init rust --lib
  ```
- Configure PyO3 in `Cargo.toml`
- Create virtual environment and install dependencies
- Set up Git repository with proper `.gitignore`
- Create development/production configuration files

**1.2 Basic UI Shell**
- Implement `MainWindow` class
- Create `HeaderBar` with placeholder buttons
- Build `Sidebar` layout with "New Chat" button
- Create basic `ChatView` with scrolling area
- Implement dark theme CSS
  ```css
  window {
    background-color: #1a1b1e;
    color: #e0e0e0;
  }
  
  .sidebar {
    background-color: #202123;
    border-right: 1px solid #2a2b2e;
  }
  
  headerbar {
    background-color: #1a1b1e;
    border-bottom: 1px solid #2a2b2e;
  }
  ```
- Connect UI components
- Test window resizing and layout

**1.3 Database Setup**
- Create SQLite schema
- Implement database connection manager
- Create ORM models using SQLAlchemy
- Write migration system
- Add database initialization on first run
- Create backup functionality

**1.4 API Client Foundation**
- Implement `NanoGPTClient` class
- Add authentication handling
- Create request/response structures
- Implement basic error handling
- Add connection timeout management
- Write unit tests for API client

### Phase 2: Core Features (Week 3-4)

**2.1 Conversation Management**
- Create new conversations
  - Generate unique IDs
  - Set default titles ("New Chat")
  - Initialize with empty message list
- Save conversations to database
  - Transaction handling
  - Error recovery
- Load conversation history
  - Pagination for long conversations
  - Lazy loading of messages
- Delete conversations
  - Confirmation dialog
  - Cascade delete messages
- Rename conversations
  - Inline editing in sidebar
  - Validation (non-empty, unique within project)
- Conversation metadata tracking
  - Message count
  - Last updated timestamp
  - Total tokens used

**2.2 Message Display**
- Message list rendering with virtualization
- User/AI message differentiation
  - Different styling
  - Avatar icons
- Timestamp display with relative formatting ("2 minutes ago")
- Markdown rendering using Rust parser
  - Headers
  - Lists (ordered/unordered)
  - Bold, italic, strikethrough
  - Inline code
  - Links (clickable)
- Code block syntax highlighting
  - Language detection
  - Line numbers
  - Copy button
  - Theme matching
- Message streaming with typewriter effect
- Message actions (copy, edit, regenerate)

**2.3 Message Input & Sending**
- Multi-line text input with auto-expansion
- Send on Ctrl+Enter (configurable)
- Message validation
  - Non-empty check
  - Length limits
- Disable input while processing
- Show typing indicator when AI is responding
- Handle send errors gracefully
- Message queuing for offline support

**2.4 Web Search Integration**
- Header bar toggle button
  - Active/inactive visual states
  - Keyboard shortcut (Ctrl+W)
- API endpoint selection based on toggle
- Store web search preference per conversation
- Display "Searching the web..." indicator
- Parse and display web sources
  - Source title and URL
  - Numbered references [1], [2], etc.
  - Clickable links that open in browser
- Handle web search errors
  - Timeout handling
  - No results found
  - API limitations
- Web search settings in preferences

**2.5 Sidebar Functionality**
- Populate conversation list from database
- Date-based grouping
  - Today: messages from current day
  - Last 7 Days: last week
  - Last 30 Days: last month
  - Older: everything else (paginated)
- Conversation selection
  - Highlight active conversation
  - Load messages on click
- Real-time search/filter
  - Search by title
  - Search by message content (using Rust search)
  - Highlight matches
- Empty state handling
  - "No conversations yet" message
  - Helpful getting started text

### Phase 3: Advanced Features (Week 5-6)

**3.1 Search Functionality**
- Implement Rust-based full-text search engine
  ```rust
  use tantivy::{Index, IndexWriter, doc};
  
  pub fn create_search_index(path: &str) -> Result<Index> {
      let schema = build_schema();
      let index = Index::create_in_dir(path, schema)?;
      Ok(index)
  }
  
  pub fn search(index: &Index, query: &str) -> Result<Vec<SearchResult>> {
      let searcher = index.reader()?.searcher();
      let query_parser = QueryParser::for_index(&index, vec![field]);
      let query = query_parser.parse_query(query)?;
      let results = searcher.search(&query, &TopDocs::with_limit(20))?;
      Ok(results)
  }
  ```
- Index all conversations and messages on startup
- Incremental indexing on new messages
- Search UI in header bar
  - Search overlay/popover
  - Results list with preview
  - Jump to conversation and message
- Highlight search terms in results
- Fuzzy matching for typo tolerance
- Search filters (by date, by project)
- Search history and suggestions

**3.2 Projects/Organization**
- Create project folders
  - Name validation
  - Color coding (optional)
- Project CRUD operations
- Assign conversations to projects
  - Drag-and-drop
  - Context menu
  - Bulk operations
- Project-based filtering in sidebar
- Collapsible project sections
- "No project" section for unorganized chats
- Project statistics (conversation count)

**3.3 Action Buttons & Modes**
- "Create" mode
  - Optimized prompts for content creation
  - Templates for common formats
  - Export options
- "Explore" mode
  - Automatically enable web search
  - Research-focused prompts
  - Source aggregation
- "Code" mode
  - Code generation focus
  - Syntax highlighting preferences
  - Code execution (future)
- "Learn" mode
  - Educational response style
  - Step-by-step explanations
  - Follow-up questions
- Mode indicator in UI
- Mode-specific settings

**3.4 Suggested Prompts**
- Context-aware suggestions based on:
  - Current conversation topic
  - Previous messages
  - User's common queries
- Welcome screen prompts
  - General interest topics
  - Popular use cases
- Dynamic prompt generation
- Prompt templates library
- User-created custom prompts

**3.5 Message Management**
- Edit sent messages
  - Branch conversations
  - Show edit history
- Regenerate AI responses
  - Multiple attempts
  - Compare responses
- Delete messages
  - Confirmation
  - Update conversation flow
- Copy message content
  - Plain text
  - Markdown
  - With/without sources
- Message bookmarking/starring
- Export individual messages

### Phase 4: Polish & Optimization (Week 7-8)

**4.1 Performance Optimization**
- Lazy loading for long conversations
  - Load messages in chunks (50 at a time)
  - Infinite scroll implementation
- Message virtualization
  - Only render visible messages
  - Recycle message widgets
- Async API calls with proper cancellation
  - Cancel requests on navigation
  - Request queuing
- Database query optimization
  - Proper indexing
  - Query result caching
  - Connection pooling
- Profile and optimize bottlenecks
  - Use Python profiler
  - Rust benchmarks
- Memory usage optimization
  - Limit cache sizes
  - Periodic garbage collection

**4.2 UX Enhancements**
- Keyboard shortcuts
  ```python
  shortcuts = {
      "<Ctrl>N": "new_chat",
      "<Ctrl>F": "search",
      "<Ctrl>W": "toggle_web_search",
      "<Ctrl>comma": "open_settings",
      "<Ctrl>Q": "quit",
      "<Ctrl>Return": "send_message",
      "<Ctrl>K": "command_palette",
      "F1": "help"
  }
  ```
- Drag-and-drop organization
  - Move conversations between projects
  - Reorder conversations
- Export conversations
  - Markdown format
  - JSON format
  - PDF with formatting (using WeasyPrint)
  - HTML with embedded styles
- Import conversations
  - From JSON exports
  - From ChatGPT exports (future)
- Copy functionality
  - Copy message
  - Copy code block
  - Copy with/without formatting
- Loading states and animations
  - Skeleton screens
  - Progress indicators
  - Smooth transitions
- Toast notifications for actions
  - "Conversation deleted"
  - "Copied to clipboard"
  - "Settings saved"

**4.3 Settings & Customization**
- Model selection dropdown
  - Display model capabilities
  - Token limits
  - Cost information (if applicable)
- Temperature slider (0.0 - 2.0)
- Max tokens slider
- System prompt customization
- API endpoint configuration
- Font customization
  - Family selection
  - Size adjustment
  - Monospace for code
- Theme customization
  - Dark/light/auto
  - Custom color schemes
  - Accent color selection
- Sidebar width adjustment
- Message spacing preferences
- Export/import settings
- Reset to defaults option

**4.4 Error Handling & Resilience**
- Comprehensive error messages
  - User-friendly descriptions
  - Suggested actions
  - Technical details (collapsible)
- Network error handling
  - Offline detection
  - Automatic retry with backoff
  - Queue messages for later
- API error handling
  - Rate limit detection
  - Invalid API key
  - Server errors
- Database error handling
  - Corruption detection
  - Automatic repair attempts
  - Backup restoration
- Crash recovery
  - Auto-save drafts
  - Restore last session
  - Error reporting
- Validation throughout
  - Input validation
  - Data sanitization
  - Type checking

**4.5 Documentation & Help**
- In-app help system
  - Welcome tutorial on first launch
  - Feature tooltips
  - Keyboard shortcuts overlay (Ctrl+?)
  - Context-sensitive help
- User documentation
  - Getting started guide
  - Feature documentation
  - Troubleshooting guide
  - FAQ section
- Developer documentation
  - API reference
  - Architecture overview
  - Contributing guidelines
  - Code style guide

## Technical Specifications

### Complete File Structure
```
nanochat-desktop/
├── nanochat/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── config.py                  # Configuration management
│   ├── constants.py               # Application constants
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py              # NanoGPT API client
│   │   ├── models.py              # API request/response models
│   │   └── exceptions.py          # API-specific exceptions
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection and setup
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── repository.py          # Data access layer
│   │   └── migrations/            # Database migrations
│   │       ├── __init__.py
│   │       └── v1_initial.py
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── app_state.py           # Application state manager
│   │   ├── conversation_state.py  # Active conversation state
│   │   └── preferences.py         # User preferences
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # Main application window
│   │   ├── header_bar.py          # Header bar component
│   │   ├── sidebar.py             # Sidebar with conversations
│   │   ├── chat_view.py           # Main chat area
│   │   ├── message_row.py         # Individual message widget
│   │   ├── welcome_screen.py      # Welcome/empty state
│   │   ├── settings_dialog.py     # Settings window
│   │   ├── search_overlay.py      # Search UI
│   │   ├── context_menu.py        # Right-click menus
│   │   ├── dialogs.py             # Confirmation/error dialogs
│   │   └── resources/
│   │       ├── style.css          # GTK CSS styling
│   │       └── icons/             # Application icons
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Logging configuration
│       ├── validators.py          # Input validation
│       ├── formatters.py          # Date/text formatting
│       └── export.py              # Export functionality
│
├── rust/
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs                 # Library root and Py
