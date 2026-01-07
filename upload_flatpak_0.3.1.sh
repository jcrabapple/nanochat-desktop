#!/bin/bash
# GITHUB_TOKEN="ghp_..."
RELEASE_ID="274641088"

curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@build/NanoChatDesktop-0.3.1-x86_64.flatpak" \
  "https://uploads.github.com/repos/jcrabapple/nanochat-desktop/releases/${RELEASE_ID}/assets?name=NanoChatDesktop-0.3.1-x86_64.flatpak"
