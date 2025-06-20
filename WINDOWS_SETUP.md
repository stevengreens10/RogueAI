# Windows Setup Guide for AIRogue

AIRogue is now fully compatible with Windows! Follow these steps to get it running.

## Prerequisites

1. **Python 3.6+** - Download from [python.org](https://www.python.org/downloads/)
2. **Windows Terminal** (recommended) - Get from Microsoft Store or [GitHub](https://github.com/microsoft/terminal)

## Quick Setup

### Option 1: Automatic Setup (Recommended)
```cmd
python setup_windows.py
```

### Option 2: Manual Setup
```cmd
pip install windows-curses
python main.py
```

## Installation Steps

1. **Install Python** (if not already installed)
   - Download from python.org
   - Make sure to check "Add Python to PATH" during installation

2. **Install Windows-Curses**
   ```cmd
   pip install windows-curses
   ```

3. **Run the Game**
   ```cmd
   python main.py
   ```

## Troubleshooting

### "No module named 'curses'" Error
```cmd
pip install windows-curses
```

### "Permission denied" Error
```cmd
python -m pip install --user windows-curses
```

### Terminal Display Issues
- Use **Windows Terminal** instead of Command Prompt
- Enable UTF-8 support in your terminal
- Try running in PowerShell

### Character Display Problems
The game includes Windows-safe character replacements:
- Stairs: `▼` becomes `v`
- Other special characters are automatically converted

## Recommended Terminal Settings

For the best experience in Windows Terminal:
1. Use a monospace font (Consolas, Courier New, or Cascadia Code)
2. Set terminal size to at least 100x30 characters
3. Enable "Use legacy console" if you have display issues

## Performance Tips

- Close other applications for better performance
- Use Windows Terminal for better rendering
- Ensure your terminal window is large enough (100+ columns, 30+ rows)

## Controls

- **3D Mode**: Arrow keys turn, WASD move
- **2D Mode**: wasd/hjkl/arrows move
- **i**: Toggle inventory
- **m/M**: View/cast spells
- **f/F**: Cast spell
- **g/G**: Toggle godmode
- **3**: Toggle 2D/3D mode
- **S**: Save game
- **q**: Quit

## Support

If you encounter issues:
1. Make sure you have the latest version of Python
2. Try reinstalling windows-curses: `pip uninstall windows-curses && pip install windows-curses`
3. Use Windows Terminal instead of Command Prompt
4. Check that your terminal supports Unicode characters

Enjoy your dungeon adventure!