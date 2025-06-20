# AIRogue

A CLI-based roguelike game inspired by the original Rogue.

**✨ Now fully compatible with Windows, macOS, and Linux! ✨**

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
- **Complete magic system** with 8 different spells and spellbooks
- **Dual equipment system** - weapons and shields/spellbooks
- **3D raycasting mode** - Toggle between 2D ASCII and 3D first-person view
- **Epic boss battles** with special abilities and multiple phases
- **Godmode** for testing and casual play
- **Death screen** with restart, load, or quit options
- **Victory screen** when you defeat a boss
- Save/load game functionality
- **Color-coded graphics** for enhanced visual experience
- **Cross-platform compatibility** (Windows, macOS, Linux)
- Multiple movement options (WASD, vi-keys, arrow keys)
- Real-time terminal rendering using curses

## Installation & Setup

### Windows
```cmd
# Quick setup (recommended)
python setup_windows.py

# Or manual setup
pip install windows-curses
python main.py
```

### macOS & Linux
```bash
# No additional setup needed
python3 main.py
```

## How to Play

```bash
# Start new game
python main.py          # Windows
python3 main.py         # macOS/Linux

# Load saved game
python main.py --load

# Show help
python main.py --help
```

### Controls

#### 2D Mode
- **Movement**: `wasd`, `hjkl` (vi-style), or arrow keys
- **Combat**: Move into enemies to attack them
- **Inventory**: `i` to toggle inventory screen
- **Magic**: `m/M` to view spells, `f/F` to cast spells
- **Godmode**: `g/G` to toggle godmode
- **3D Toggle**: `3` to switch to 3D mode
- **Save**: `S` (capital S) to save game
- **Quit**: `q`

#### 3D Mode
- **Turn**: Arrow keys (left/right)
- **Move**: `w/a/s/d` keys
- **Combat**: Walk into enemies
- **All other controls**: Same as 2D mode

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
- `]` - Shield (Cyan)
- `&` - Spellbook (Purple)
- `B` - Boss (Red, Bold)

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

### All Platforms
- Python 3.6+

### Windows
- `windows-curses` package (automatically installed by setup script)
- Windows Terminal recommended for best experience

### macOS & Linux
- Built-in curses support (no additional packages needed)

## Windows Troubleshooting

If you encounter issues on Windows:

1. **Install windows-curses**: `pip install windows-curses`
2. **Use Windows Terminal** instead of Command Prompt
3. **Check terminal size**: Ensure at least 100x30 characters
4. **Run setup script**: `python setup_windows.py` for automatic configuration

See `WINDOWS_SETUP.md` for detailed Windows installation instructions.

## Magic System

The game features a complete magic system:

- **8 Different Spells**: Fireball, Heal, Magic Missile, Lightning Bolt, Shield, Teleport, Freeze, Poison Cloud
- **Spellbooks**: Find spellbooks to learn new spells or equip for magic power bonuses
- **Mana System**: Spells cost mana, which slowly regenerates each turn
- **Spell Targeting**: Some spells require targeting with directional input
- **Status Effects**: Shield protection, freezing enemies, poison damage over time

## Boss Battles

Encounter powerful bosses at deeper levels:

- **Spawn at level 10+**: Guaranteed every 10 levels, 10% chance at level 15+
- **Multiple Phases**: Bosses get more aggressive as health decreases
- **Special Abilities**: Summon minions, dark magic blasts, teleport attacks, life drain, phase shifting
- **Victory Condition**: Defeating any boss wins the game!

## 3D Mode

Toggle between 2D ASCII and 3D first-person view:

- **Raycasting Engine**: Real-time 3D rendering in terminal
- **Weapon Sprites**: See your equipped weapons on screen
- **Shield Display**: Shields appear on the right side
- **Minimap**: Small overhead view in 3D mode
- **Same Gameplay**: All game mechanics work in both modes