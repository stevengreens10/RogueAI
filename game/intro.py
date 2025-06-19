"""
Intro screen with animations for AIRogue
"""

import curses
import time
import random


class IntroScreen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.animation_frame = 0
        self.start_time = time.time()
        
        # Setup colors for intro
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(11, curses.COLOR_RED, -1)      # Title red
            curses.init_pair(12, curses.COLOR_YELLOW, -1)   # Title yellow
            curses.init_pair(13, curses.COLOR_GREEN, -1)    # Subtitle
            curses.init_pair(14, curses.COLOR_CYAN, -1)     # Instructions
            curses.init_pair(15, curses.COLOR_WHITE, -1)    # Default
    
    def draw_animated_title(self, center_y, center_x):
        """Draw the AIRogue title with color cycling animation"""
        title = "AIRogue"
        subtitle = "A CLI Roguelike Adventure"
        
        # Color cycling based on animation frame
        colors = [11, 12, 13, 14]  # Red, Yellow, Green, Cyan
        color_index = (self.animation_frame // 5) % len(colors)
        title_color = curses.color_pair(colors[color_index]) | curses.A_BOLD
        
        # Draw title with letter-by-letter color variation
        for i, char in enumerate(title):
            char_color_index = (color_index + i) % len(colors)
            char_color = curses.color_pair(colors[char_color_index]) | curses.A_BOLD
            try:
                self.stdscr.addch(center_y - 4, center_x - len(title) // 2 + i, char, char_color)
            except curses.error:
                pass
        
        # Draw subtitle
        try:
            subtitle_color = curses.color_pair(13)
            self.stdscr.addstr(center_y - 2, center_x - len(subtitle) // 2, subtitle, subtitle_color)
        except curses.error:
            pass
    
    def draw_animated_border(self, center_y, center_x):
        """Draw animated border around the title"""
        width = 40
        height = 10
        
        # Animate border characters
        border_chars = ['*', '+', 'x', '~']
        border_char = border_chars[(self.animation_frame // 3) % len(border_chars)]
        
        border_color = curses.color_pair(14)
        
        try:
            # Top and bottom borders
            for x in range(width):
                self.stdscr.addch(center_y - height // 2, center_x - width // 2 + x, border_char, border_color)
                self.stdscr.addch(center_y + height // 2, center_x - width // 2 + x, border_char, border_color)
            
            # Left and right borders
            for y in range(height):
                self.stdscr.addch(center_y - height // 2 + y, center_x - width // 2, border_char, border_color)
                self.stdscr.addch(center_y - height // 2 + y, center_x + width // 2, border_char, border_color)
        except curses.error:
            pass
    
    def draw_floating_symbols(self, center_y, center_x):
        """Draw floating dungeon symbols around the screen"""
        symbols = ['@', '#', '.', '$', '!', '&', '%']
        
        # Get screen dimensions for better distribution
        height, width = self.stdscr.getmaxyx()
        
        # Create pseudo-random positions based on animation frame
        random.seed(42)  # Fixed seed for consistent pattern
        
        for i in range(25):
            # Better distribution across the entire screen
            base_x = random.randint(2, max(2, width - 3))
            base_y = random.randint(1, max(1, height - 3))
            
            # Skip symbols that would overlap with the main title area
            title_area_left = center_x - 25
            title_area_right = center_x + 25
            title_area_top = center_y - 6
            title_area_bottom = center_y + 10
            
            # Skip if in title area
            if (title_area_left <= base_x <= title_area_right and 
                title_area_top <= base_y <= title_area_bottom):
                continue
            
            # Floating movement with sine waves
            time_offset = time.time() - self.start_time + i * 0.5
            offset_x = int(2 * __import__('math').sin(time_offset * 0.8))
            offset_y = int(1.5 * __import__('math').cos(time_offset * 0.6 + i))
            
            float_x = base_x + offset_x
            float_y = base_y + offset_y
            
            # Ensure symbols stay within screen bounds
            float_x = max(0, min(width - 1, float_x))
            float_y = max(0, min(height - 1, float_y))
            
            symbol = symbols[i % len(symbols)]
            symbol_color = curses.color_pair((i % 4) + 11)
            
            try:
                self.stdscr.addch(float_y, float_x, symbol, symbol_color)
            except curses.error:
                pass
    
    def draw_instructions(self, center_y, center_x):
        """Draw game instructions and start prompt"""
        instructions = [
            "Welcome to AIRogue!",
            "",
            "Navigate dungeons, fight monsters, collect treasure",
            "Use WASD or arrow keys to move",
            "Press 'i' for inventory, 'S' to save, 'q' to quit",
            "",
            "Press any key to start your adventure..."
        ]
        
        instruction_color = curses.color_pair(14)
        
        # Blinking effect for the last line
        blink_on = (self.animation_frame // 10) % 2 == 0
        
        for i, line in enumerate(instructions):
            try:
                if i == len(instructions) - 1 and blink_on:
                    # Blinking start prompt
                    self.stdscr.addstr(center_y + 2 + i, center_x - len(line) // 2, line, 
                                     instruction_color | curses.A_BLINK | curses.A_BOLD)
                else:
                    self.stdscr.addstr(center_y + 2 + i, center_x - len(line) // 2, line, instruction_color)
            except curses.error:
                pass
    
    def draw(self):
        """Draw the complete intro screen"""
        self.stdscr.clear()
        
        # Get screen dimensions
        height, width = self.stdscr.getmaxyx()
        center_y = height // 2
        center_x = width // 2
        
        # Draw all animated elements
        self.draw_floating_symbols(center_y, center_x)
        self.draw_animated_border(center_y, center_x)
        self.draw_animated_title(center_y, center_x)
        self.draw_instructions(center_y, center_x)
        
        # Update animation frame
        self.animation_frame += 1
        
        self.stdscr.refresh()
    
    def run(self):
        """Run the intro screen until user presses a key"""
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(50)    # 50ms timeout for smooth animation
        
        while True:
            self.draw()
            
            # Check for key press
            key = self.stdscr.getch()
            if key != -1:  # Key was pressed
                break
            
            time.sleep(0.05)  # Small delay for smooth animation
        
        # Clear screen before returning
        self.stdscr.clear()
        self.stdscr.refresh()