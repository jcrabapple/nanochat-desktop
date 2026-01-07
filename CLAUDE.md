# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NanoChat Desktop is a Linux desktop AI chat application built with Python and GTK4, integrating with the NanoGPT API. The application uses a Model-View-Controller (MVC) pattern with clear separation between UI, state management, and API layers.

**Technology Stack:**
- Python 3.11+
- GTK4 with PyGObject bindings
- SQLite (via SQLAlchemy)
- aiohttp for async HTTP
- Markdown + Pygments for formatting

## Building and Running

### Installation (Development)

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
# Installs to: build/NanoChatDesktop-0.2.3-x86_64.flatpak
```

**AppImage:**
```bash
./build_appimage_proper.sh
# Note: Requires GTK4 to be installed on target system
```

Both build scripts are in the repository root and handle all necessary packaging steps.

## Architecture

The application follows a clear MVC pattern:

### Model Layer (`nanochat/api/` and `nanochat/data/`)
- **`api/client.py`**: NanoGPT API client with streaming support
- **`api/models.py`**: Request/response data models
- **`data/`**: Database layer (currently minimal - SQLAlchemy referenced but not fully implemented)

### Controller Layer (`nanochat/state/`)
- **`app_state.py`**: Main application controller, manages conversations and coordinates between UI and API
- **`conversation_mode.py`**: Defines conversation modes (Standard, Create, Explore, Code, Learn)

### View Layer (`nanochat/ui/`)
- **`main_window.py`**: Application shell, combines all components
- **`header_bar.py`**: Top bar with settings button
- **`sidebar.py`**: Conversation list with search and grouping
- **`chat_view.py`**: Main chat area with message display and input
- **`action_bar.py`**: Mode selection buttons (Create, Explore, Code, Learn)
- **`settings_dialog.py`**: Configuration dialog for API settings

### Configuration (`nanochat/config.py`)
- Multi-source configuration (environment variables, config file, defaults)
- Config location: `~/.config/nanochat/config.ini`
- Data location: `~/.local/share/nanochat/`

## Key Patterns

### Async/Threading Model
GTK4 runs on the main thread, while API calls use async/await. Threading bridges these two worlds:
```python
# Run async operations in background thread
threading.Thread(
    target=lambda: asyncio.run(self.send_message_async(text)),
    daemon=True
).start()
```

UI updates from background threads use `GLib.idle_add()`.

### Streaming Responses
The API client supports streaming responses. Messages are yielded incrementally and the UI updates in real-time using generators.

### Conversation Modes
Modes change system prompts, temperature, and web search behavior. The `ConversationMode` enum and `MODE_CONFIGS` dictionary define these behaviors.

### CSS Styling
Dark theme CSS is in `nanochat/ui/resources/style.css`. Components use `add_css_class()` to apply styles.

## Common Development Tasks

### Adding a New Conversation Mode
1. Add enum to `nanochat/state/conversation_mode.py`
2. Add `ModeConfig` to `MODE_CONFIGS` dictionary
3. Update `action_bar.py` to include new button
4. Add CSS styling if needed

### Modifying the UI
GTK4 components are built programmatically (not with Glade). To modify a component:
1. Read the relevant file in `nanochat/ui/`
2. Modify the `_build_ui()` or `__init__()` method
3. Test with `python -m nanochat.main`

### Working with the API
The `NanoGPTClient` in `nanochat/api/client.py` handles all API communication. It supports:
- Standard chat endpoint
- Web search endpoint
- Streaming responses
- Error handling with retry logic

## Current State

### Implemented (Phase 1-2)
- Core UI with GTK4
- API integration with streaming
- Configuration management
- Action modes (Create, Explore, Code, Learn)
- Basic conversation management
- Settings dialog

### Not Yet Implemented
- Database layer for message persistence (referenced but not implemented)
- Rust modules for performance (fast search, markdown parsing) - see `nanochat_full_plan.md`
- Advanced features from Phase 3 (projects, search, etc.) - see `PHASE3_PLAN.md`

## Important Notes

- No test suite currently exists (pytest is configured but no tests written)
- The application is Linux-only (GTK4 dependency)
- Flatpak is the recommended distribution method (bundles GTK4)
- AppImage bundles Python but requires system GTK4
- Icon files are in the root `/icons/` directory and are packaged separately

## Documentation Files

- **README.md**: Installation and usage guide for end users
- **nanochat_full_plan.md**: Complete development roadmap with architecture details
- **PHASE3_PLAN.md**: Prioritized implementation plan for advanced features
