# AIRogue

A CLI-based roguelike game inspired by the original Rogue.

## Features

- Procedurally generated dungeons with rooms and corridors
- **Multi-level progression** with exit stairs and increasing difficulty
- **Dynamic shop system** with level-scaled items and random encounters between levels
- Player character with HP, attack, defense, and inventory
- Monster enemies (Goblins and Orcs) with intelligent AI that scales with level
- Turn-based combat system with equipment bonuses
- Items and inventory system (weapons, potions, gold)
- Equipment system with attack bonuses
- **Buy/sell mechanics** at mysterious shops
- **XP and leveling system** with character progression
- **Level-up rewards** with 5 different upgrade paths
- **Death screen** with restart, load, or quit options
- Save/load game functionality
- **Color-coded graphics** for enhanced visual experience
- Multiple movement options (WASD, vi-keys, arrow keys)
- Real-time terminal rendering using curses

## How to Play

```bash
# Start new game
python3 main.py

# Load saved game
python3 main.py --load

# Show help
python3 main.py --help
```

### Controls

- **Movement**: `wasd`, `hjkl` (vi-style), or arrow keys
- **Combat**: Move into enemies to attack them
- **Inventory**: `i` to toggle inventory screen
- **Save**: `S` (capital S) to save game
- **Quit**: `q`

### Game Elements

- `@` - Player character (Yellow)
- `#` - Walls (White)
- `.` - Floor (Blue)
- `>` - Exit stairs (White)
- `g` - Goblin (Red)
- `o` - Orc (Red)
- `S` - Shopkeeper (Magenta)
- `!` - Health Potion (Green)
- `)` - Weapon (Cyan)
- `$` - Gold (Yellow)

### Color Scheme

The game features a full color palette to enhance gameplay:
- **Player**: Yellow - easy to spot your character
- **Monsters**: Red - clearly identifies threats
- **Items**: Green (potions) and Cyan (weapons) for quick identification
- **Gold**: Yellow - matches the traditional color of treasure
- **Environment**: Blue floors, White walls for clear dungeon layout
- **UI**: Color-coded health (red when low), gold counter, and equipment display

### Gameplay

- **Level Progression**: Find the exit stairs (`>`) to advance to the next level
- **Scaling Difficulty**: Monsters get stronger, items get better, and gold rewards increase with each level
- **Shop Encounters**: 50% chance of finding a mysterious shop between levels
- **Monster AI**: Monsters hunt you when nearby (5 tile range), otherwise wander randomly with 30% movement chance
- **Combat**: Damage is calculated as (Attack + Equipment Bonus + 0-2 random) - (Defense + Equipment Bonus), minimum 1
- **Items**: Walk over items to pick them up automatically
- **Inventory**: Press `i` to open inventory, then press number keys (1-9) to use items or equip weapons
- **Equipment**: Weapons provide attack bonuses when equipped
- **Gold**: Collected automatically when walked over, gained from defeating monsters
- **Shopping**: In shops, press number keys (1-9) to buy items, Shift+number keys to sell your items, 'e' to exit shop
- **Dynamic Shop Inventory**: Each shop generates 4-7 items appropriate for your current level
- **Shop Scaling**: Higher level shops offer better weapons, stronger potions, and defensive gear
- **Shop Pricing**: Items sell for half their original value
- **Experience**: Gain XP by killing monsters, amount scales with dungeon level
- **Character Leveling**: Automatically level up when you earn enough XP (50 XP for level 2, then +25 XP per level)
- **Level-up Rewards**: Choose from 3 random options when leveling up:
  - **Vitality Boost**: +10 Max HP and full heal
  - **Warrior Training**: +2 Attack damage
  - **Iron Skin**: +1 Defense
  - **Treasure Hunter**: +50 Gold and better loot sense
  - **Battle Hardened**: +5 Max HP and +1 Attack (balanced option)
- **Death**: When you die, choose to restart (1), load save (2), or quit (3)

## Requirements

- Python 3.6+
- Unix-like system with curses support (Linux, macOS)

The game uses only Python standard library modules, so no additional packages need to be installed.