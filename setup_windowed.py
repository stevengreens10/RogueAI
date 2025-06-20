#!/usr/bin/env python3
"""
Setup script for AIRogue Windowed Edition
Installs pygame and checks system compatibility
"""

import subprocess
import sys
import platform

def install_pygame():
    """Install pygame using pip"""
    try:
        # Try to install pygame
        print("Installing pygame...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame>=2.0.0"])
        print("pygame installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install pygame via pip.")
        return False
    except FileNotFoundError:
        print("pip not found. Trying alternative installation methods...")
        return False

def check_pygame():
    """Check if pygame is available"""
    try:
        import pygame
        print(f"pygame version {pygame.version.ver} is available!")
        return True
    except ImportError:
        print("pygame is not installed.")
        return False

def main():
    print("AIRogue Windowed Edition Setup")
    print("=" * 40)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    # Check if pygame is already installed
    if check_pygame():
        print("✓ pygame is already installed and ready!")
        print("\nYou can now run the windowed version with:")
        print("  python3 main_windowed.py")
        return
    
    # Try to install pygame
    print("pygame not found. Attempting to install...")
    
    if install_pygame():
        print("\n✓ Setup complete! You can now run:")
        print("  python3 main_windowed.py")
    else:
        print("\n✗ Setup failed. Please install pygame manually:")
        print("  pip install pygame")
        print("  or")
        print("  python3 -m pip install pygame")
        print("\nOn some systems you may need:")
        print("  sudo apt-get install python3-pygame  # Ubuntu/Debian")
        print("  brew install pygame                   # macOS with Homebrew")

if __name__ == "__main__":
    main()