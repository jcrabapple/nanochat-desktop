#!/bin/bash
set -e

# GITHUB_TOKEN="ghp_..."
REPO="jcrabapple/nanochat-desktop"
VERSION="v0.3.1"
APPIMAGE="build/NanoChatDesktop-0.3.1-x86_64.AppImage"
FLATPAK="build/NanoChatDesktop-0.3.1-x86_64.flatpak"

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

# Check Flatpak exists
if [ ! -f "$FLATPAK" ]; then
    echo "ERROR: Flatpak not found at $FLATPAK"
    exit 1
fi

# Create release
echo "Creating release..."
RELEASE_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/releases" \
    -d @- << EOF
{
    "tag_name": "${VERSION}",
    "target_commitish": "main",
    "name": "NanoChat Desktop 0.3.1 - Application Icons",
    "body": "## Release 0.3.1 - Application Icons Feature\n\n### ✨ New Features\n\n**Application Icons & Desktop Integration**\n- ✅ Added application icon at multiple sizes (32x32, 48x48, 64x64, 128x128, 256x256)\n- ✅ Created proper desktop file (com.nanochat.desktop.desktop)\n- ✅ Icon now appears in application launcher\n- ✅ Users can add desktop shortcuts with proper icon\n- ✅ Icon appears in taskbar/dock while running\n\n### 🔧 Improvements\n\n**Desktop Integration:**\n- Desktop file includes proper categories and keywords\n- Icons follow freedesktop.org standards\n- All sizes installed to standard icon directories\n- Both AppImage and Flatpak include full icon set\n\n### 📦 Installation\n\n**AppImage:**\n1. Download NanoChatDesktop-0.3.1-x86_64.AppImage\n2. chmod +x NanoChatDesktop-0.3.1-x86_64.AppImage\n3. ./NanoChatDesktop-0.3.1-x86_64.AppImage\n\n**Flatpak:**\n1. Download NanoChatDesktop-0.3.1-x86_64.flatpak\n2. flatpak install NanoChatDesktop-0.3.1-x86_64.flatpak\n\n### 🔑 Requirements\n\n- Linux x86_64\n- GTK4 libraries (for AppImage)\n- NanoGPT API key\n\n### 📝 Notes\n\n- This release adds desktop integration with application icons\n- Icon will appear in your application launcher\n- Size increased due to icon inclusion (AppImage: 1.4MB, Flatpak: 6.8MB)\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)",
    "draft": false,
    "prerelease": false
}
EOF
)

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
    if echo "$UPLOAD_RESPONSE" | grep -q '"state": "uploaded"'; then
        BROWSER_URL=$(echo "$UPLOAD_RESPONSE" | grep -o '"browser_download_url": "[^"]*' | cut -d'"' -f4)
    else
        echo "ERROR: Failed to upload AppImage"
        echo "$UPLOAD_RESPONSE"
        exit 1
    fi
fi

echo "✓ AppImage uploaded!"

# Upload Flatpak
echo "Uploading Flatpak..."
UPLOAD_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Content-Type: application/octet-stream" \
    -H "Accept: application/vnd.github.v3+json" \
    --data-binary "@${FLATPAK}" \
    "${UPLOAD_URL}?name=$(basename ${FLATPAK})")

BROWSER_URL2=$(echo "$UPLOAD_RESPONSE" | grep -o '"browser_download_url": "[^"]*' | cut -d'"' -f4)

if [ -z "$BROWSER_URL2" ]; then
    if echo "$UPLOAD_RESPONSE" | grep -q '"state": "uploaded"'; then
        BROWSER_URL2=$(echo "$UPLOAD_RESPONSE" | grep -o '"browser_download_url": "[^"]*' | cut -d'"' -f4)
    else
        echo "ERROR: Failed to upload Flatpak"
        echo "$UPLOAD_RESPONSE"
        exit 1
    fi
fi

echo "✓ Flatpak uploaded!"
echo ""
echo "✓ Release created and both files uploaded successfully!"
echo ""
echo "Release page: https://github.com/${REPO}/releases/tag/${VERSION}"
