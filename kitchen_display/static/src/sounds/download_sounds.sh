#!/bin/bash
# Download sample notification sounds for Kitchen Display System
# These are placeholder sounds - replace with professional audio for production

SOUND_DIR="$(dirname "$0")"
cd "$SOUND_DIR" || exit 1

echo "================================================"
echo "Kitchen Display System - Sound Downloader"
echo "================================================"

# Function to create a simple beep sound using sox (if available)
create_beep_sound() {
    local filename=$1
    local freq=$2
    local duration=$3

    if command -v sox >/dev/null 2>&1; then
        echo "Creating $filename using sox..."
        sox -n -r 44100 -c 2 "$filename" synth "$duration" sine "$freq" fade 0.1 0 0.1 norm -3
        return 0
    fi
    return 1
}

# Check if we can create sounds with sox
if command -v sox >/dev/null 2>&1; then
    echo "✓ Found 'sox' - will generate simple notification sounds"
    echo ""

    # Generate new_order.mp3 (pleasant chime)
    if [ ! -f "new_order.mp3" ]; then
        echo "Creating new_order.mp3..."
        create_beep_sound "new_order.mp3" 800 0.3
        echo "✓ Created new_order.mp3"
    else
        echo "⊘ new_order.mp3 already exists"
    fi

    # Generate state_change.mp3 (confirmation beep)
    if [ ! -f "state_change.mp3" ]; then
        echo "Creating state_change.mp3..."
        create_beep_sound "state_change.mp3" 1000 0.15
        echo "✓ Created state_change.mp3"
    else
        echo "⊘ state_change.mp3 already exists"
    fi

    # Generate urgent_order.mp3 (attention sound)
    if [ ! -f "urgent_order.mp3" ]; then
        echo "Creating urgent_order.mp3..."
        sox -n -r 44100 -c 2 urgent_order.mp3 synth 0.2 sine 1200 fade 0.05 0 0.05 : synth 0.2 sine 1200 fade 0.05 0 0.05 norm -3
        echo "✓ Created urgent_order.mp3"
    else
        echo "⊘ urgent_order.mp3 already exists"
    fi

    echo ""
    echo "✅ Sound files generated successfully!"

else
    echo "❌ 'sox' is not installed"
    echo ""
    echo "To install sox:"
    echo "  Ubuntu/Debian: sudo apt-get install sox libsox-fmt-mp3"
    echo "  RedHat/CentOS: sudo yum install sox"
    echo "  macOS: brew install sox"
    echo ""
    echo "Alternative: Download sounds manually from:"
    echo "  - https://freesound.org/"
    echo "  - https://mixkit.co/free-sound-effects/"
    echo "  - https://www.zapsplat.com/"
    echo ""
    echo "Required files:"
    echo "  - new_order.mp3 (kitchen bell or chime)"
    echo "  - state_change.mp3 (optional - confirmation beep)"
    echo "  - urgent_order.mp3 (optional - urgent alert)"
    exit 1
fi

echo ""
echo "================================================"
echo "Testing sounds..."
echo "================================================"

# List created files
ls -lh *.mp3 2>/dev/null || echo "No MP3 files found"

echo ""
echo "Done! Sound files are ready for use."
echo "Clear browser cache and reload Kitchen Display Board to hear sounds."
