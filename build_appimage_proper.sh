#!/bin/bash
set -e

VERSION="0.2.2"
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
    wget -q --show-progress "https://github.com/linuxdeploy/linuxdeploy-plugin-gtk/releases/download/continuous/linuxdeploy-plugin-gtk-${ARCH}.AppImage" -O "$GTK_PLUGIN"
    chmod +x "$GTK_PLUGIN"
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

# Create desktop file
cat > "$APPDIR/com.nanochat.desktop.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=NanoChat Desktop
Comment=Desktop AI chat application
Exec=nanochat
Icon=nanochat
Terminal=false
Categories=GNOME;GTK;Network;
EOF
cp "$APPDIR/com.nanochat.desktop.desktop" "$APPDIR/usr/share/applications/"

# Create icon
cat > "$APPDIR/nanochat.svg" << 'EOFSVG'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="48" fill="#1a1b1e"/>
  <rect width="256" height="256" rx="48" fill="#4a9eff" fill-opacity="0.2"/>
  <text x="128" y="160" font-family="Arial, sans-serif" font-size="100" font-weight="bold" text-anchor="middle" fill="#4a9eff">NC</text>
</svg>
EOFSVG

# Try to convert to PNG
if command -v convert &> /dev/null; then
    echo "Converting icon to PNG..."
    convert -background none "$APPDIR/nanochat.svg" "$APPDIR/nanochat.png" 2>/dev/null || cp "$APPDIR/nanochat.svg" "$APPDIR/nanochat.png"
fi

cp "$APPDIR/nanochat.svg" "$APPDIR/usr/share/icons/hicolor/256x256/apps/nanochat.svg"
if [ -f "$APPDIR/nanochat.png" ]; then
    cp "$APPDIR/nanochat.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/nanochat.png"
fi

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
