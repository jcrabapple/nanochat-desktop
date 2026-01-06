#!/bin/bash
# Script to create GitHub release and upload AppImage
# Requires: GitHub Personal Access Token with 'repo' scope

set -e

REPO="jcrabapple/nanochat-desktop"
VERSION="v0.2.1"
APPIMAGE="build/NanoChatDesktop-0.2.1-x86_64.AppImage"

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
        \"name\": \"NanoChat Desktop 0.2.1\",
        \"body\": \"Release 0.2.1 - Critical Bug Fixes\\n\\n**Bug Fixes:**\\n- ✅ Fixed CSS parser errors (removed unsupported GTK CSS properties)\\n- ✅ Fixed MessageDialog API for GTK4 compatibility\\n- ✅ Fixed database schema for new installations\\n\\n**Changes:**\\n- Removed invalid CSS properties (max-width, display, gap, keyframes)\\n- Updated MessageDialog to use proper GTK4 constructor\\n- AppImage now works without errors\\n\\n**Installation:**\\n1. Download NanoChatDesktop-0.2.1-x86_64.AppImage\\n2. chmod +x NanoChatDesktop-0.2.1-x86_64.AppImage\\n3. ./NanoChatDesktop-0.2.1-x86_64.AppImage\\n\\n**Requirements:**\\n- Linux x86_64\\n- GTK4 libraries\\n- Python 3.11+\\n- WebKit2GTK\",
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
