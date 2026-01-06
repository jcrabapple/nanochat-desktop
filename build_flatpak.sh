#!/bin/bash
set -e

VERSION="0.2.4"
REPO="jcrabapple/nanochat-desktop"

echo "Building NanoChat Desktop Flatpak..."

# Install flatpak-builder if not present
if ! flatpak list | grep -q "org.flatpak.Builder"; then
    echo "flatpak-builder not found. Installing..."
    flatpak install --user flathub org.flatpak.Builder
fi

# Install GNOME platform SDK if not present
echo "Checking for GNOME Platform runtime..."
if ! flatpak list | grep -q "org.gnome.Platform.*46"; then
    echo "Installing GNOME Platform 46 runtime..."
    flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
fi

# Clean previous build
rm -rf build/flatpak-build
rm -rf build/flatpak-repo

# Build Flatpak
echo "Building Flatpak..."
flatpak run --command=flatpak-builder org.flatpak.Builder --install --user --force-clean \
    --repo=build/flatpak-repo \
    build/flatpak-build \
    com.nanochat.desktop.json

# Export to single file
echo "Exporting Flatpak bundle..."
flatpak build-bundle build/flatpak-repo \
    build/NanoChatDesktop-${VERSION}-x86_64.flatpak \
    com.nanochat.desktop

echo ""
echo "✓ Flatpak built successfully!"
echo ""
echo "To test:"
echo "  flatpak run com.nanochat.desktop"
echo ""
echo "To install from bundle:"
echo "  flatpak install build/NanoChatDesktop-${VERSION}-x86_64.flatpak"
echo ""
echo "To uninstall:"
echo "  flatpak uninstall com.nanochat.desktop"
