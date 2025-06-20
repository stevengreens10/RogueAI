# AIRogue - Windowed Edition

AIRogue has been successfully converted from a CLI-only game to a proper windowed video game! The game now supports both the original terminal interface and a new pygame-based windowed interface.

## What's New

### 🖼️ Windowed Interface
- **Full pygame window** with 1024x768 resolution
- **Improved graphics** with color-coded entities and UI
- **Better readability** with proper fonts and layouts
- **Mouse and keyboard support** (keyboard controls currently)

### 🎮 Dual Rendering Modes
- **2D ASCII Mode**: Enhanced ASCII rendering in a window with better colors
- **3D Raycasting Mode**: Full 3D raycasting with minimap, weapon sprites, and entity rendering
- **Toggle between modes** with the '3' key just like the original

### 🎯 Enhanced UI
- **Clean interface layout** with dedicated game area and UI section
- **Better inventory screens** with improved formatting
- **Shop interface** with better visual organization
- **Spell casting menus** with clear options and descriptions

## Installation & Setup

### Quick Start
```bash
# Universal launcher (recommended)
python3 launch_windowed.py

# Or install pygame and run directly
python3 setup_windowed.py
python3 main_windowed.py
```

### Manual Setup
```bash
# Install pygame
pip install pygame

# Run windowed version
python3 main_windowed.py

# Load saved game
python3 main_windowed.py --load
```

## Controls

### Windowed Version Controls
- **2D Mode**: WASD/Arrow keys/HJKL for movement
- **3D Mode**: Arrow keys to turn, WASD to move
- **I**: Toggle inventory
- **M**: View spells
- **F**: Cast spell
- **G**: Toggle godmode
- **3**: Toggle 2D/3D mode
- **Shift+S**: Save game
- **Q**: Quit
- **E**: Exit shop (when in shop)
- **L**: Learn spells (when viewing spellbook)
- **1-9**: Use/equip items, buy/sell in shop, select options
- **Shift+1-9**: Sell items in shop

## Architecture

### File Structure
```
main_windowed.py           # Main windowed game class
game/window_renderer.py    # Pygame rendering system
game/renderer3d_pygame.py  # 3D raycasting for pygame
launch_windowed.py         # Universal launcher
setup_windowed.py          # Pygame setup script
```

### Key Components

1. **GameWindow Class**: Main game state and logic (replaces curses Game class)
2. **WindowRenderer Class**: Handles all pygame rendering and input
3. **PygameRenderer3D Class**: 3D raycasting adapted for pygame
4. **Event System**: Clean command-based input handling

### Rendering Pipeline
1. **Event Handling**: Pygame events → command strings
2. **Game Logic**: Commands processed by game state
3. **Rendering**: Game state rendered to pygame surface
4. **Display**: 60 FPS with proper timing

## Features Preserved

✅ **All original gameplay** - exact same mechanics  
✅ **Save/load system** - compatible with CLI saves  
✅ **3D raycasting** - enhanced with better graphics  
✅ **Magic system** - all spells work identically  
✅ **Shop system** - improved visual interface  
✅ **Boss fights** - all mechanics preserved  
✅ **Level progression** - identical XP and rewards  
✅ **Equipment system** - weapons, shields, spellbooks  

## Compatibility

- **Cross-platform**: Windows, macOS, Linux
- **Save compatibility**: Saves work between CLI and windowed versions
- **Fallback support**: Automatically falls back to CLI if pygame not available
- **Python 3.6+**: Same minimum requirements as original

## Development Notes

### For Developers
- All core game logic remains in `game/` modules
- Rendering is completely separated from game logic
- Input handling uses a clean command system
- Easy to extend with new UI elements

### Architecture Benefits
- **Modular design**: Renderer can be swapped easily
- **Shared logic**: No duplication between CLI and windowed versions
- **Clean separation**: Input/Output separated from game state
- **Extensible**: Easy to add new features to either version

## Troubleshooting

### Pygame Issues
```bash
# If pygame fails to install
python3 -m pip install --upgrade pip
python3 -m pip install pygame

# On Ubuntu/Debian
sudo apt-get install python3-pygame

# On macOS with Homebrew
brew install pygame
```

### Fallback to CLI
If you can't install pygame, the launcher will automatically use the original CLI version:
```bash
python3 launch_windowed.py  # Will use CLI if no pygame
```

## Future Enhancements

The windowed architecture makes it easy to add:
- **Better graphics**: Tile-based sprites instead of ASCII
- **Mouse support**: Click-based interaction
- **Larger windows**: Configurable resolution
- **Audio**: Sound effects and music
- **Animations**: Smooth movement and effects
- **Modern UI**: Buttons, menus, and dialog boxes

The foundation is now in place for a full modern roguelike while preserving the classic gameplay!