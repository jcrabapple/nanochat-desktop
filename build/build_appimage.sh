#!/bin/bash
set -e

VERSION="0.2.2"
ARCH="x86_64"
APPNAME="NanoChatDesktop"
APPDIR="build/AppDir"

echo "Building NanoChat Desktop AppImage..."

# Clean previous build
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}"

# Create AppRun first (before cleaning)
cat > "build/AppRun.tmp" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/nanochat-desktop:${PYTHONPATH}"
exec "${HERE}/usr/bin/nanochat" "$@"
EOF

# Create AppDir structure
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APPDIR}/usr/share/metainfo"

# Copy application files
echo "Copying application files..."
mkdir -p "${APPDIR}/usr/lib/nanochat-desktop"
cp -r nanochat "${APPDIR}/usr/lib/nanochat-desktop/"

# Copy environment example
cp .env.example "${APPDIR}/usr/lib/nanochat-desktop/.env.example"

# Create launcher script
cat > "${APPDIR}/usr/bin/nanochat" << 'EOF'
#!/bin/bash
# NanoChat Desktop launcher

# Set up paths
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="${SCRIPT_DIR}/../lib/nanochat-desktop:${PYTHONPATH}"

# Check for GTK4
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
    echo "ERROR: GTK4 is not installed or not available."
    echo ""
    echo "This AppImage requires GTK4 to be installed on your system."
    echo ""
    echo "To install GTK4:"
    echo "  Fedora: sudo dnf install gtk4 gtk4-devel"
    echo "  Ubuntu: sudo apt install libgtk-4-1 gir1.2-gtk-4.0"
    echo "  Arch: sudo pacman -S gtk4"
    echo ""
    echo "See https://github.com/jcrabapple/nanochat-desktop for more information."
    exit 1
fi

# Check if config exists, if not copy example
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nanochat-desktop"
CONFIG_FILE="$CONFIG_DIR/.env"

if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    cp "${SCRIPT_DIR}/../lib/nanochat-desktop/.env.example" "$CONFIG_FILE"
    echo "Created config file at $CONFIG_FILE"
    echo "Please edit it and add your API key, then run the application again."
    exit 1
fi

# Run the application
exec python3 -m nanochat.main "$@"
EOF
chmod +x "${APPDIR}/usr/bin/nanochat"

# Create simple SVG icon
cat > "${APPDIR}/nanochat.svg" << 'EOFSVG'
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
    convert -background none "${APPDIR}/nanochat.svg" "${APPDIR}/nanochat.png" 2>/dev/null || cp "${APPDIR}/nanochat.svg" "${APPDIR}/nanochat.png"
fi

# Copy icon
cp "${APPDIR}/nanochat.svg" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/nanochat.svg"
if [ -f "${APPDIR}/nanochat.png" ]; then
    cp "${APPDIR}/nanochat.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/nanochat.png"
fi

# Copy desktop file
cp build/com.nanochat.desktop.desktop "${APPDIR}/com.nanochat.desktop.desktop"
cp build/com.nanochat.desktop.desktop "${APPDIR}/usr/share/applications/com.nanochat.desktop.desktop"

# Create AppInfo for AppImage
cat > "${APPDIR}/usr/share/metainfo/com.nanochat.desktop.appdata.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.nanochat.desktop</id>
  <name>NanoChat Desktop</name>
  <summary>Desktop AI chat application with NanoGPT</summary>
  <description>
    <p>A modern desktop application for AI-powered conversations using NanoGPT API.</p>
  </description>
  <launchable type="desktop-id">com.nanochat.desktop.desktop</launchable>
  <screenshots>
    <screenshot type="default">
      <image>https://raw.githubusercontent.com/jcrabapple/nanochat-desktop/main/screenshot.png</image>
    </screenshot>
  </screenshots>
  <url type="homepage">https://github.com/jcrabapple/nanochat-desktop</url>
  <project_license>MIT</project_license>
  <provides>
    <binary>nanochat</binary>
  </provides>
  <releases>
    <release version="0.1.0" date="2025-01-06"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

# Copy AppRun
cp build/AppRun.tmp "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"
rm -f build/AppRun.tmp

# Create .dirinfo for AppImage
cat > "${APPDIR}/.dirinfo" << EOF
AppID: com.nanochat.desktop
AppVersion: ${VERSION}
AppPackageType: AppImage
EOF

# Download appimagetool if not present
APPIMAGETOOL="build/appimagetool-${ARCH}.AppImage"
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "Downloading appimagetool..."
    wget -q --show-progress "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -O "${APPIMAGETOOL}"
    chmod +x "${APPIMAGETOOL}"
fi

# Build AppImage
echo ""
echo "Building AppImage..."
ARCH="${ARCH}" "${APPIMAGETOOL}" "${APPDIR}" "build/${APPNAME}-${VERSION}-${ARCH}.AppImage"

echo ""
echo "✓ AppImage built successfully: build/${APPNAME}-${VERSION}-${ARCH}.AppImage"
echo ""
echo "Test it with: ./build/${APPNAME}-${VERSION}-${ARCH}.AppImage"
