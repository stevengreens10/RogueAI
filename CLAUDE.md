# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running and Testing

### Windows
```cmd
# Quick setup
python setup_windows.py

# Run the game
python main.py

# Load saved game
python main.py --load
```

### macOS/Linux
```bash
# Run the game
python3 main.py

# Load saved game
python3 main.py --load

# Show help and controls
python3 main.py --help
```

The game is cross-platform compatible (Windows, macOS, Linux). On Windows, it requires the `windows-curses` package. The game has no build system, test framework, or linting - it runs directly with Python 3.6+.

## Architecture Overview

AIRogue is a modular CLI roguelike with dual rendering modes (2D ASCII and 3D raycasting). The architecture centers around a main `Game` class that orchestrates all systems.

### Core Systems Integration

- **main.py**: Contains the main game loop, input handling, and dual rendering coordination
- **game/entities.py**: Fundamental data structures (Entity, Item, Position) used across all systems
- **game/dungeon.py**: Procedural generation and spatial management for all game objects
- **game/renderer3d.py**: Raycasting 3D engine with weapon sprites, minimap, and entity rendering

### Key Architectural Patterns

1. **State Centralization**: The `Game` class holds all game state and coordinates between systems
2. **Dual Rendering**: Same game state renders in both 2D ASCII and 3D raycasting modes (toggle with '3' key)
3. **Component Systems**: Combat, shop, leveling, and save/load are separate modules that operate on shared entity data
4. **Level Scaling**: All systems (combat, shop, AI, loot) scale content based on current dungeon level

### Critical Dependencies Between Systems

- **Combat System**: Reads weapon/shield stats from entity equipment slots
- **Shop System**: Generates level-appropriate items using dungeon.level for scaling
- **Save/Load**: Serializes complete game state including all entity equipment and dungeon data
- **3D Renderer**: Accesses player.angle for camera rotation and player.weapon for sprite rendering
- **Leveling System**: XP rewards scale with dungeon level, affects entity stats permanently

## Working with Game Systems

### Adding New Items/Entities
1. Add enum values to `EntityType` in `entities.py`
2. Update color mapping in `main.py:get_color_pair()`
3. Add item generation logic in `shop.py` or `dungeon.py`
4. Update save/load compatibility in `save_load.py`

### Modifying 3D Rendering
- **Weapon Sprites**: Edit `get_weapon_sprite()` in `renderer3d.py` for new weapon types
- **Entity Sprites**: Modify `render_entities_on_column()` for new monster/item appearance
- **UI Elements**: Both 2D and 3D share the same game state, so UI changes affect both modes

### Equipment System Architecture
The game supports both weapons and shields through entity attributes:
- `entity.weapon` - provides attack bonus
- `entity.shield` - provides defense bonus
- `entity.equipment` - backwards compatibility property that maps to weapon

### Level Progression Flow
1. **Dungeon Generation**: `dungeon.py` creates level layout and places entities
2. **Combat Resolution**: `combat.py` handles damage calculation with equipment bonuses
3. **XP Rewards**: Scale with `dungeon.level` for balanced progression
4. **Shop Encounters**: 50% chance between levels, inventory scales with level
5. **Save State**: Complete game state persists to `savegame.json`

## Important Implementation Notes

- **No External Dependencies**: Pure Python standard library only
- **Curses Terminal**: All rendering uses curses for cross-platform terminal support
- **JSON Serialization**: Save system handles complete game state including equipment
- **Color System**: Uses curses color pairs - check `curses.has_colors()` before using colors
- **Error Handling**: Extensive curses.error catching for terminal compatibility
- **Position System**: Uses `Position` dataclass with arithmetic operations for spatial calculations