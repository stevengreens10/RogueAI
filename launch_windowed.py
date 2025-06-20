#!/usr/bin/env python3
"""
Launcher for AIRogue Windowed Edition
Checks for pygame and launches the appropriate version
"""

import sys
import os

def check_pygame():
    """Check if pygame is available"""
    try:
        import pygame
        return True
    except ImportError:
        return False

def main():
    print("AIRogue Launcher")
    print("================")
    
    # Check command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if check_pygame():
        print("✓ pygame detected - launching windowed version")
        try:
            # Import and run windowed version
            from main_windowed import main as windowed_main
            windowed_main()
        except Exception as e:
            print(f"Error running windowed version: {e}")
            print("Falling back to CLI version...")
            fallback_to_cli(args)
    else:
        print("✗ pygame not found - using CLI version")
        print("To install pygame: python3 -m pip install pygame")
        print()
        fallback_to_cli(args)

def fallback_to_cli(args):
    """Fallback to the original CLI version"""
    try:
        print("Starting CLI version...")
        import subprocess
        cmd = [sys.executable, "main.py"] + args
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error running CLI version: {e}")
        print("Please check that all dependencies are installed.")

if __name__ == "__main__":
    main()