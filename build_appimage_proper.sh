#!/bin/bash
set -e

VERSION="0.5.0"
ARCH="x86_64"
APPNAME="NanoChatDesktop"
BUILDDIR="build/appimage-build"
APPDIR="$BUILDDIR/AppDir"

echo "Building NanoChat Desktop AppImage with linuxdeploy..."

# Clean previous build
rm -rf "$BUILDDIR"
mkdir -p "$BUILDDIR"

# Download linuxdeploy and GTK plugin if not present
LINUXDEPLOY="$BUILDDIR/linuxdeploy-${ARCH}.AppImage"
GTK_PLUGIN="$BUILDDIR/linuxdeploy-plugin-gtk-${ARCH}.AppImage"

if [ ! -f "$LINUXDEPLOY" ]; then
    echo "Downloading linuxdeploy..."
    wget -q --show-progress "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage" -O "$LINUXDEPLOY"
    chmod +x "$LINUXDEPLOY"
fi

if [ ! -f "$GTK_PLUGIN" ]; then
    echo "Downloading linuxdeploy GTK plugin..."
    wget -q --show-progress "https://github.com/linuxdeploy/linuxdeploy-plugin-gtk/releases/download/continuous/linuxdeploy-plugin-gtk-${ARCH}.AppImage" -O "$GTK_PLUGIN" || echo "Warning: GTK plugin not available (not required for this build)"
    if [ -f "$GTK_PLUGIN" ]; then
        chmod +x "$GTK_PLUGIN"
    fi
fi

# Create AppDir structure manually first
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

# Copy Python application
echo "Copying application files..."
mkdir -p "$APPDIR/usr/lib/nanochat-desktop"
cp -r nanochat "$APPDIR/usr/lib/nanochat-desktop/"
cp .env.example "$APPDIR/usr/lib/nanochat-desktop/.env.example"

# Copy desktop file
echo "Installing desktop file..."
cp com.nanochat.desktop.desktop "$APPDIR/com.nanochat.desktop.desktop"
cp com.nanochat.desktop.desktop "$APPDIR/usr/share/applications/com.nanochat.desktop.desktop"

# Install icons
echo "Installing icons..."
# Install main icon (scalable)
cp icon.png "$APPDIR/com.nanochat.desktop.png"
cp icon.png "$APPDIR/.icon"
cp icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/com.nanochat.desktop.png"

# Install additional sizes if available
for size in 128x128 64x64 48x48 32x32; do
    icon_file="icon_${size}.png"
    if [ -f "$icon_file" ]; then
        mkdir -p "$APPDIR/usr/share/icons/hicolor/${size}/apps"
        cp "$icon_file" "$APPDIR/usr/share/icons/hicolor/${size}/apps/com.nanochat.desktop.png"
        echo "  Installed ${size} icon"
    fi
done

# Create launcher script
cat > "$APPDIR/usr/bin/nanochat" << 'EOF'
#!/bin/bash
# NanoChat Desktop launcher

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="${SCRIPT_DIR}/../lib/nanochat-desktop:${PYTHONPATH}"

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nanochat-desktop"
CONFIG_FILE="$CONFIG_DIR/.env"

if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    cp "${SCRIPT_DIR}/../lib/nanochat-desktop/.env.example" "$CONFIG_FILE"
    echo "Created config file at $CONFIG_DIR"
    echo "Please edit it and add your API key, then run the application again."
    exit 1
fi

exec python3 -m nanochat.main "$@"
EOF
chmod +x "$APPDIR/usr/bin/nanochat"

# Create AppInfo
cat > "$APPDIR/usr/share/metainfo/com.nanochat.desktop.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.nanochat.desktop</id>
  <name>NanoChat Desktop</name>
  <summary>Desktop AI chat application</summary>
  <description>
    <p>A modern desktop application for AI-powered conversations.</p>
  </description>
  <launchable type="desktop-id">com.nanochat.desktop.desktop</launchable>
  <url type="homepage">https://github.com/jcrabapple/nanochat-desktop</url>
  <project_license>MIT</project_license>
  <provides>
    <binary>nanochat</binary>
  </provides>
  <releases>
    <release version="${VERSION}" date="2025-01-06"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

# Create AppRun (will be replaced by linuxdeploy but good to have)
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/nanochat-desktop:${PYTHONPATH}"
export GI_TYPELIB_PATH="${HERE}/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/nanochat" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Build AppImage with linuxdeploy
echo ""
echo "Building AppImage with linuxdeploy..."
export VERSION="$VERSION"
export OUTPUT="build/${APPNAME}-${VERSION}-${ARCH}.AppImage"

# For now, create a simple AppImage that bundles dependencies using appimagetool
# but with better library detection
echo ""
echo "Note: Building basic AppImage (requires GTK4 on host system)"
echo "For full bundling, we need to use linuxdeploy which has compatibility issues"

# Use appimagetool for now (simpler, more compatible)
APPIMAGETOOL="build/appimagetool-${ARCH}.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -q --show-progress "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

ARCH="${ARCH}" "$APPIMAGETOOL" "$APPDIR" "build/${APPNAME}-${VERSION}-${ARCH}.AppImage"

echo ""
echo "✓ AppImage built: build/${APPNAME}-${VERSION}-${ARCH}.AppImage"
echo ""
echo "IMPORTANT: This AppImage requires GTK4 to be installed on the host system."
echo "Install with: sudo dnf install gtk4 (Fedora) or sudo apt install libgtk-4-1 (Ubuntu)"
