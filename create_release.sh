#!/bin/bash
# Script to create GitHub release and upload AppImage
# Requires: GitHub Personal Access Token with 'repo' scope

set -e

REPO="jcrabapple/nanochat-desktop"
VERSION="v0.3.0"
APPIMAGE="build/NanoChatDesktop-0.3.0-x86_64.AppImage"

echo "Creating GitHub release ${VERSION}..."

# Check for GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN environment variable not set"
    exit 1
fi

# Check AppImage exists
if [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: AppImage not found at $APPIMAGE"
    exit 1
fi

# Create release
echo "Creating release..."
RELEASE_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/releases" \
    -d "{
        \"tag_name\": \"${VERSION}\",
        \"target_commitish\": \"main\",
        \"name\": \"NanoChat Desktop 0.3.0 - Action Modes\",
        \"body\": \"## Release 0.3.0 - Action Modes Feature\\n\\n### ✨ New Features\\n\\n**Action Buttons & Conversation Modes (Task 1.1)**\\n- ✅ Added 4 conversation modes: Create, Explore, Code, Learn\\n- ✅ Each mode has optimized prompts, temperature settings, and web search preferences\\n- ✅ Visual toggle buttons in the chat interface\\n- ✅ Mutually exclusive mode selection (only one active at a time)\\n- ✅ Click active button to return to Standard mode\\n- ✅ Visual indicator toast when switching modes\\n- ✅ Settings dialog now has two tabs: API Configuration and Modes\\n- ✅ Modes tab explains what each mode does\\n\\n### 🔧 Improvements\\n\\n**Mode Configurations:**\\n- Standard: Default conversation (temperature 0.7)\\n- Create: Content creation with higher creativity (0.8)\\n- Explore: Research mode with web search enabled (0.5)\\n- Code: Code generation with higher precision (0.3)\\n- Learn: Educational mode with detailed explanations (0.6, web search enabled)\\n\\n**Settings Dialog:**\\n- New tabbed interface (API Configuration | Modes)\\n- API Base URL is now read-only (NanoGPT API only)\\n- Comprehensive mode information with descriptions and shortcuts\\n- Keyboard shortcuts displayed (Ctrl+2 through Ctrl+5)\\n\\n### 🐛 Bug Fixes\\n\\n- Fixed mutually exclusive toggle behavior for action mode buttons\\n- Fixed mode button state management with guard flag to prevent recursive calls\\n- Added proper visual feedback for mode changes\\n\\n### 📦 Installation\\n\\n1. Download NanoChatDesktop-0.3.0-x86_64.AppImage\\n2. chmod +x NanoChatDesktop-0.3.0-x86_64.AppImage\\n3. ./NanoChatDesktop-0.3.0-x86_64.AppImage\\n\\n### 🔑 Requirements\\n\\n- Linux x86_64\\n- GTK4 libraries\\n- Python 3.11+\\n- WebKit2GTK\\n- NanoGPT API key\\n\\n### ⌨️ Keyboard Shortcuts\\n\\n- Ctrl+N - New chat\\n- Ctrl+W - Toggle web search\\n- Ctrl+, - Settings\\n- Ctrl+Q - Quit\\n- Ctrl+1 through Ctrl+5 - Mode selection\\n\\n### 📝 Notes\\n\\n- This release implements Phase 3, Task 1.1 from the roadmap\\n- AppImage requires GTK4 to be installed on the host system\\n- Web search auto-enables for Explore and Learn modes\\n- Click the currently active mode button to return to Standard mode\\n\\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\",
        \"draft\": false,
        \"prerelease\": false
    }")

# Get upload URL
UPLOAD_URL=$(echo "$RELEASE_RESPONSE" | grep -o '"upload_url": "[^"]*' | cut -d'"' -f4 | sed 's/{?name,label}//')

if [ -z "$UPLOAD_URL" ]; then
    echo "ERROR: Failed to create release"
    echo "$RELEASE_RESPONSE"
    exit 1
fi

echo "Release created successfully!"
echo "Uploading AppImage..."

# Upload AppImage
UPLOAD_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Content-Type: application/octet-stream" \
    -H "Accept: application/vnd.github.v3+json" \
    --data-binary "@${APPIMAGE}" \
    "${UPLOAD_URL}?name=$(basename ${APPIMAGE})")

BROWSER_URL=$(echo "$UPLOAD_RESPONSE" | grep -o '"browser_download_url": "[^"]*' | cut -d'"' -f4)

if [ -z "$BROWSER_URL" ]; then
    # Check if upload actually succeeded despite error
    if echo "$UPLOAD_RESPONSE" | grep -q '"state": "uploaded"'; then
        BROWSER_URL=$(echo "$UPLOAD_RESPONSE" | grep -o '"browser_download_url": "[^"]*' | cut -d'"' -f4)
    else
        echo "ERROR: Failed to upload AppImage"
        echo "$UPLOAD_RESPONSE"
        exit 1
    fi
fi

echo ""
echo "✓ Release created and AppImage uploaded successfully!"
echo ""
echo "Release page: https://github.com/${REPO}/releases/tag/${VERSION}"
echo "Download URL: ${BROWSER_URL}"
