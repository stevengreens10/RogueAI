#!/usr/bin/env python3
"""
Windows Setup Script for AIRogue
Automatically installs dependencies and sets up the game for Windows
"""

import sys
import subprocess
import platform
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print(f"❌ Python {version.major}.{version.minor} is too old. Please install Python 3.6 or later.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_windows_curses():
    """Install windows-curses package"""
    commands = [
        ("pip install windows-curses", "Installing windows-curses"),
        ("pip install --upgrade windows-curses", "Upgrading windows-curses")
    ]
    
    for command, description in commands:
        if run_command(command, description):
            return True
    
    # Try with user flag if admin install fails
    print("🔄 Trying user installation...")
    return run_command("pip install --user windows-curses", "Installing windows-curses (user)")

def test_curses_import():
    """Test if curses can be imported"""
    try:
        import curses
        print("✅ Curses module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import curses: {e}")
        return False

def check_terminal_size():
    """Check if terminal is large enough"""
    try:
        columns = os.get_terminal_size().columns
        lines = os.get_terminal_size().lines
        
        if columns < 80 or lines < 24:
            print(f"⚠️  Terminal size is {columns}x{lines}. Recommended: 100x30 or larger")
            print("   Consider enlarging your terminal window for the best experience")
        else:
            print(f"✅ Terminal size {columns}x{lines} is good")
        return True
    except:
        print("⚠️  Could not detect terminal size")
        return True

def main():
    """Main setup function"""
    print("🎮 AIRogue Windows Setup")
    print("=" * 40)
    
    # Check if we're on Windows
    if platform.system() != "Windows":
        print(f"ℹ️  This setup script is for Windows. You're running {platform.system()}")
        print("   The game should work with standard Python curses on your system.")
        return
    
    print(f"🖥️  Detected: {platform.system()} {platform.release()}")
    
    # Check Python version
    if not check_python_version():
        print("\n🔗 Download Python from: https://www.python.org/downloads/")
        return
    
    # Install windows-curses
    if not install_windows_curses():
        print("\n❌ Failed to install windows-curses. Please try manually:")
        print("   pip install windows-curses")
        return
    
    # Test curses import
    if not test_curses_import():
        print("\n❌ Setup incomplete. Please check the error messages above.")
        return
    
    # Check terminal
    check_terminal_size()
    
    # Success message
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 You can now run the game:")
    print("   python main.py")
    print("\n📖 For help:")
    print("   python main.py --help")
    
    # Terminal recommendations
    print("\n💡 For the best experience:")
    print("   • Use Windows Terminal (available in Microsoft Store)")
    print("   • Set terminal size to at least 100x30 characters")
    print("   • Use a monospace font like Consolas or Cascadia Code")
    
    # Ask if user wants to start the game
    try:
        response = input("\n❓ Would you like to start the game now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("\n🎮 Starting AIRogue...")
            os.system("python main.py")
    except KeyboardInterrupt:
        print("\n👋 Setup complete. Run 'python main.py' when ready!")

if __name__ == "__main__":
    main()