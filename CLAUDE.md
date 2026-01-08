# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NanoChat Desktop is a Linux desktop AI chat application built with Python and GTK4, integrating with the NanoGPT API. The application uses a Model-View-Controller (MVC) pattern with clear separation between UI, state management, and API layers.

**Technology Stack:**
- Python 3.11+
- GTK4 with PyGObject bindings
- SQLAlchemy (SQLite)
- aiohttp for async HTTP
- Markdown + Pygments for formatting
- WebKit2 (optional, falls back to TextView)

## Building and Running

### Development Installation

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the application
nanochat
# or
python -m nanochat.main
```

### Building Distribution Packages

**Flatpak (Recommended - Self-Contained):**
```bash
./build_flatpak.sh
# Output: build/NanoChatDesktop-{VERSION}-x86_64.flatpak
# Bundles all dependencies including GTK4
```

**AppImage:**
```bash
./build_appimage_proper.sh
# Output: build/NanoChatDesktop-{VERSION}-x86_64.AppImage
# Note: Requires GTK4 to be installed on target system
```

**Version bumps:** Update `VERSION` variable in both `build_appimage_proper.sh` and `build_flatpak.sh` before building releases.

### Icon Management

Application icons are stored in the repository root:
- `icon.png` (1024x1024) - Source icon
- `icon_{size}.png` - Pre-sized variants (256x256, 128x128, 64x64, 48x48, 32x32)

Both AppImage and Flatpak build scripts handle icon installation automatically. The desktop file is `com.nanochat.desktop.desktop`.

## Architecture

The application follows a clear MVC pattern with async/streaming support:

### Model Layer (`nanochat/api/` and `nanochat/data/`)

**API Client (`nanochat/api/client.py`)**
- `NanoGPTClient`: Async client with streaming support
- Endpoints: `/v1/chat/completions` (chat), `/web` (web search)
- Returns async generators that yield `StreamChunk` objects
- Handles retry logic and connection errors

**Database (`nanochat/data/`)**
- SQLAlchemy ORM with SQLite backend
- `DatabaseManager`: Session management with migration support
- `ConversationRepository`: CRUD for conversations
- `MessageRepository`: CRUD for messages with web sources
- `ProjectRepository`: CRUD for conversation projects
- Models: `Conversation`, `Message`, `Project`, `SuggestedPrompt` (see `nanochat/data/models.py`)
- Database location: `~/.local/share/nanochat/conversations.db`
- Migrations: Located in `nanochat/data/migrations/`

### Controller Layer (`nanochat/state/`)

**`app_state.py`**: Main application controller
- Coordinates between UI, API, and database
- Manages conversation lifecycle
- `send_message()`: Async generator that yields tuples of `(role, content, web_sources)`
- Handles mode switching and web search preferences

**`conversation_mode.py`**: Conversation mode system
- `ConversationMode` enum: STANDARD, CREATE, EXPLORE, CODE, LEARN
- `ModeConfig` dataclass: Defines prompts, temperature, web search behavior
- `get_mode_config(mode)`: Retrieve configuration

### View Layer (`nanochat/ui/`)

**Component Structure:**
- `main_window.py`: Application shell, assembles all components
- `header_bar.py`: Top bar with settings button
- `sidebar.py`: Conversation list with search/filter, project management
  - Groups conversations by projects or time (Today, Yesterday, etc.)
  - Project CRUD operations
  - Conversation-to-project assignment
- `chat_view.py`: Main chat area with message display and input
  - `MarkdownView`: WebView (WebKit2) or TextView fallback for markdown rendering
  - `ActionBar`: Mode selection buttons
  - Message action buttons (copy, regenerate, delete)
- `settings_dialog.py`: Two-tab dialog (API Configuration | Modes)
- `project_dialog.py`: Project creation and management dialogs

**CSS Styling:**
- Located in `nanochat/ui/resources/style.css`
- Loaded in `MainWindow.load_css()`
- Components use `add_css_class()` to apply styles
- Dark theme matching GTK4 aesthetic

**Responsive Design:**
- Uses Adw.OverlaySplitView for responsive sidebar (when libadwaita is available)
- Sidebar collapses below 800px window width
- Toggle button in header bar shows/hides sidebar when collapsed
- Falls back to fixed horizontal layout without libadwaita

### Configuration (`nanochat/config.py`)

Multi-source configuration with priority:
1. Environment variables (`NANOCHAT_API_KEY`, etc.)
2. Config file (`~/.config/nanochat-desktop/config.ini`)
3. Defaults

Config file uses simple key=value format (not .env format despite code variable names).

## Key Patterns

### Async/Threading Model

GTK4 runs on the main thread. API calls use async/await with aiohttp. Bridge pattern:

```python
# Run async operations in background thread
threading.Thread(
    target=lambda: asyncio.run(self.send_message_async(text)),
    daemon=True
).start()

# Update UI from background thread
GLib.idle_add(lambda: self.update_ui(data))
```

### Streaming Responses

The API client returns async generators that yield `StreamChunk` objects. The `send_message()` method in `ApplicationState` is itself an async generator that yields `(role, content, web_sources)` tuples:

```python
async for chunk in api_client.send_message(...):
    if chunk.content:
        yield ('assistant', chunk.content, None)
    if chunk.web_sources:
        yield ('assistant', None, chunk.web_sources)
```

### Conversation Modes

Modes affect system prompts, temperature, and web search:
- Configured in `MODE_CONFIGS` dictionary
- Changed via `ActionBar` toggle buttons (mutually exclusive)
- Current mode stored in `ApplicationState.current_conversation_mode`
- UI shows temporary toast notification when mode changes

### Signal/Callback Pattern

GTK4 uses signals for events. Components emit custom signals:

```python
# Sidebar emits signals
self.sidebar.connect('new-chat', self.on_new_chat)
self.sidebar.connect('conversation-selected', self.on_conversation_selected)

# Custom signals defined with GObject.register_signal()
```

### Keyboard Shortcuts

Global keyboard shortcuts (defined in `MainWindow.setup_shortcuts()`):
- `Ctrl+N`: New chat
- `Ctrl+W`: Toggle web search
- `Ctrl+,`: Open settings
- `Ctrl+Q`: Quit application

Conversation mode shortcuts:
- `Ctrl+1` through `Ctrl+5`: Switch to specific mode (Standard, Create, Explore, Code, Learn)

### Web Search Integration

Web search is per-conversation (stored in `Conversation.web_search_enabled`):
- Can be toggled via button in chat view
- Some modes auto-enable web search (Explore, Learn)
- Web sources stored as JSON in `Message.web_sources`
- Displayed as clickable links below assistant messages

### Regenerate Feature

Users can regenerate the last assistant response:
- Click regenerate button on the last assistant message
- `ApplicationState.regenerate_last_response()` deletes the last assistant message from database
- Makes a new API call with the same conversation history
- Updates UI in real-time with new response
- Uses async generator pattern like normal message sending

### Suggested Prompts

Welcome screen displays mode-aware suggested prompts:
- `SuggestedPrompt` model stores prompts in database
- Each prompt has a `mode` field for different conversation modes
- `SuggestedPromptsView` filters and displays relevant prompts
- Clicking a prompt automatically sends it as a message

## Data Flow

### Sending a Message

1. User types message and clicks Send (or Ctrl+Enter)
2. `ChatView` emits signal → `MainWindow` handler
3. `MainWindow` calls `ApplicationState.send_message()` in background thread
4. `ApplicationState`:
   - Saves user message to database
   - Yields user message back to UI
   - Calls `NanoGPTClient.send_message()` with conversation history
   - Streams response chunks
   - Each chunk yielded back to UI for display
   - On `chunk.done`: saves assistant message with web sources to database
5. UI updates in real-time as chunks arrive

### Loading Conversations

1. User clicks conversation in sidebar
2. `Sidebar` emits `conversation-selected` signal
3. `MainWindow` calls `ApplicationState.load_conversation()`
4. `ApplicationState.get_conversation_messages()` retrieves from database
5. `ChatView.clear_messages()` followed by `ChatView.add_message()` for each

## Important Implementation Details

### WebView vs TextView Fallback

The `MarkdownView` widget attempts to use WebKit2 for rich markdown rendering. If WebKit2 is unavailable ( ImportError or ValueError), it falls back to a simple `Gtk.TextView` with plain text. Check `WEBKIT_AVAILABLE` constant before using WebKit features.

### Guard Flags for Mutually Exclusive Buttons

The `ActionBar` uses a `_updating_mode` guard flag to prevent recursive signal calls when programmatically deselecting toggle buttons:

```python
def _on_mode_toggled(self, button, mode):
    if self._updating_mode:
        return
    self._updating_mode = True
    # Deselect other buttons
    for m, btn in self.mode_buttons.items():
        if m != mode:
            btn.set_active(False)
    self._updating_mode = False
```

### GTK Widget Sizing

**Critical**: `set_size_request()` sets a MINIMUM size, not a maximum. GTK will expand widgets beyond `set_size_request()` if content is longer or parent container expands.

To constrain widget width:
1. Use CSS `max-width` property
2. Set `set_hexpand(False)` to prevent horizontal expansion
3. Use wrapper widgets with alignment constraints
4. Set `set_halign(Gtk.Align.START)` for left-aligned widgets

Example of constraining a message bubble:
```python
wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
wrapper.set_halign(Gtk.Align.START)
wrapper.set_hexpand(False)
wrapper.add_css_class("constrained-width")
wrapper.append(content_widget)
```

With CSS:
```css
.constrained-width {
    max-width: 100px;
    width: 100px;
}
```

### Configuration Persistence

Settings are saved to `~/.config/nanochat-desktop/config.ini` file. When settings change, the dialog directly calls `config.save_to_file()` and reinitializes the API client via `app_state.init_api_client()`.

## Testing

Currently no automated tests exist. Manual testing involves:
1. Running `python -m nanochat.main`
2. Testing with various API keys
3. Verifying streaming responses
4. Testing mode switching
5. Checking web search functionality

## Release Workflow

1. Update version numbers in build scripts
2. Commit changes
3. Run `./build_appimage_proper.sh` and `./build_flatpak.sh`
4. Create GitHub release via API (see `create_release.sh`)
5. Upload AppImage and Flatpak assets
6. Tag release with version number

Release scripts use the GitHub API token stored in the script itself.

## Common Issues

- **WebKit2 import errors**: Not all systems have WebKit2 bindings. The app gracefully falls back to TextView.
- **GTK4 version**: Requires GTK4 4.0+. Check with `gtk4-demo` or similar.
- **Database locked errors**: SQLite uses WAL mode, but concurrent writes can still lock. Only one application instance should run at a time.
- **Icon not showing**: Ensure icons exist in root directory and build scripts reference correct filenames.
