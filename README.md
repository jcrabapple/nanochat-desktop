# NanoChat Desktop

A desktop AI chat application built with Python and GTK4, integrating with the NanoGPT API.

## Features (Phase 1 MVP)

- Chat with AI using NanoGPT API
- Dark-themed GTK4 interface
- Conversation management
- Message history persistence
- API key configuration
- SQLite database storage

## Installation

### Option 1: AppImage (Recommended)

Download the latest AppImage from the [Releases](https://github.com/jcrabapple/nanochat-desktop/releases) page.

**IMPORTANT: AppImage requires GTK4 to be installed on your system.**

The AppImage bundles Python and all Python dependencies, but GTK4 must be installed from your system package manager:

**Fedora/RHEL:**
```bash
sudo dnf install gtk4 gtk4-devel
```

**Ubuntu/Debian:**
```bash
sudo apt install libgtk-4-1 gir1.2-gtk-4.0
```

**Arch Linux:**
```bash
sudo pacman -S gtk4
```

After installing GTK4:
```bash
chmod +x NanoChatDesktop-*.AppImage
./NanoChatDesktop-*.AppImage
```

### Option 2: From Source

### Prerequisites

- Python 3.11+
- GTK4 development libraries
- PyGObject (Python bindings for GTK)
- Linux (currently supports Linux only)

**System packages required:**

On Fedora/RHEL:
```bash
sudo dnf install python3.11 python3.11-devel gtk4-devel python3-gobject
```

On Ubuntu/Debian:
```bash
sudo apt install python3.11 python3.11-dev libgtk-4-dev python3-gi
```

The Python `PyGObject` package requires the system GTK4 development libraries to be installed first.

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd nanochat-desktop
```

2. Create virtual environment:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Run the application:
```bash
nanochat
# or
python -m nanochat.main
```

## Configuration

On first run, you'll be prompted to configure:

1. **API Key**: Get your API key from https://nano-gpt.com
2. **Base URL**: Default is `https://nano-gpt.com/api`
3. **Model**: Default is `gpt-4`

Configuration is saved to `~/.config/nanochat/config.ini`

## Usage

### Sending Messages

1. Type your message in the input box at the bottom
2. Click "Send" or press Ctrl+Enter
3. The AI response will appear in the chat area

### Managing Conversations

- Click "New Chat" in the sidebar to start a new conversation
- Click on any conversation in the sidebar to load it
- Conversations are automatically saved

### Keyboard Shortcuts

- `Ctrl+Enter`: Send message
- `Ctrl+Q`: Quit application

## Data Storage

- Database: `~/.local/share/nanochat/conversations.db`
- Config: `~/.config/nanochat/config.ini`

## Development

### Project Structure

```
nanochat-desktop/
├── nanochat/          # Main Python package
│   ├── api/           # API client
│   ├── data/          # Database layer
│   ├── state/         # Application state
│   ├── ui/            # GTK4 UI
│   └── utils/         # Utilities
├── rust/              # Rust modules (future)
└── tests/             # Tests
```

### Running Tests

```bash
pytest test_integration.py
```

## Troubleshooting

### API Key Not Working

- Verify your API key at https://nano-gpt.com
- Check that the key is entered correctly in Settings
- Ensure you have network connectivity

### Database Errors

- Check that `~/.local/share/nanochat/` exists
- Verify write permissions
- Try deleting the database file and restarting

## License

MIT License

## Roadmap

See [nanochat_full_plan.md](nanochat_full_plan.md) for complete development roadmap.
