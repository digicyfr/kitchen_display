# Kitchen Display Sound Files

This directory contains audio notification files for the kitchen display system.

## Required Sound Files

Place the following MP3 files in this directory:

1. **new_order.mp3** - Played when a new order arrives
   - Recommended: Pleasant chime or bell sound (2-3 seconds)
   - Volume: Medium-high for kitchen environment
   - Example: Kitchen bell, order bell, notification chime

2. **state_change.mp3** (Optional) - Played when order state changes
   - Recommended: Subtle click or confirmation sound (1 second)
   - Volume: Medium
   - Example: Confirmation beep, success tone

3. **urgent_order.mp3** (Optional) - Played for urgent priority orders
   - Recommended: More attention-grabbing sound (2-3 seconds)
   - Volume: High
   - Example: Urgent bell, alarm tone, alert sound

## Sound Sources

You can obtain free sounds from:
- **Freesound.org** - https://freesound.org/ (CC0 or CC-BY licensed)
- **Zapsplat** - https://www.zapsplat.com/ (Free for commercial use)
- **Mixkit** - https://mixkit.co/free-sound-effects/ (Free license)

## Format Requirements

- **Format**: MP3 (most compatible)
- **Sample Rate**: 44.1kHz or 48kHz
- **Bit Rate**: 128-192 kbps
- **Duration**: 1-3 seconds (short sounds work best)
- **Volume**: Normalize to -6dB to -3dB for consistency

## Implementation

Sounds are played via JavaScript in `static/src/js/kitchen_board.js`:

```javascript
playNotificationSound('new_order')
```

The system will gracefully handle missing files by logging a warning to console.

## Testing Sounds

To test sounds after adding files:

1. Place MP3 files in this directory
2. Clear browser cache
3. Open Kitchen Display Board
4. Create a test POS order
5. Sound should play when order arrives

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Opera: Full support

**Note**: Some browsers require user interaction before playing audio. The first sound may be blocked until the user clicks in the kitchen board.

## Volume Control

Adjust volume in `kitchen_board.js`:
```javascript
audio.volume = 0.5;  // 50% volume (adjust 0.0-1.0)
```
