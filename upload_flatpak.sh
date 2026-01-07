#!/bin/bash
set -e

# GITHUB_TOKEN="ghp_..."
RELEASE_ID="274635175"
FLATPAK_FILE="build/NanoChatDesktop-0.3.0-x86_64.flatpak"

echo "Uploading Flatpak to release v0.3.0..."
echo "File: $FLATPAK_FILE"
echo "Size: $(ls -lh $FLATPAK_FILE | awk '{print $5}')"

curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@${FLATPAK_FILE}" \
  "https://uploads.github.com/repos/jcrabapple/nanochat-desktop/releases/${RELEASE_ID}/assets?name=$(basename ${FLATPAK_FILE})" | grep -E '"state"|"browser_download_url"|"name"'

echo ""
echo "✓ Flatpak uploaded!"
