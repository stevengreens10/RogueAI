"""
3D ASCII Renderer using raycasting for Doom-like perspective
"""

import math
import curses
from game.entities import EntityType
from game.dungeon import CellType


class Renderer3D:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # 3D rendering parameters
        self.fov = math.pi / 3  # 60 degrees field of view
        self.max_depth = 20     # Maximum ray distance
        self.wall_height = 15   # Base wall height multiplier (increased for better scaling)
        
        # ASCII characters for different distances (closer = denser, farther = lighter)
        self.wall_chars = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏', '|', ':', '.', ' ']
        self.floor_char = '.'
        self.ceiling_char = ' '
        
        # Colors for 3D rendering - grayscale walls
        if curses.has_colors():
            # Grayscale wall colors by distance
            curses.init_pair(16, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Close walls (bright)
            curses.init_pair(17, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Medium-close walls
            curses.init_pair(18, curses.COLOR_BLACK, curses.COLOR_BLACK)   # Far walls (dark)
            curses.init_pair(19, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Floor
    
    def cast_ray(self, dungeon, start_x, start_y, angle):
        """Cast a ray and return distance to nearest wall and wall type"""
        step_size = 0.1
        distance = 0
        
        dx = math.cos(angle) * step_size
        dy = math.sin(angle) * step_size
        
        x, y = start_x, start_y
        
        while distance < self.max_depth:
            x += dx
            y += dy
            distance += step_size
            
            # Check bounds
            map_x = int(x)
            map_y = int(y)
            
            if (map_x < 0 or map_x >= dungeon.width or 
                map_y < 0 or map_y >= dungeon.height):
                return distance, CellType.WALL
            
            # Check for wall
            cell_type = dungeon.grid[map_y][map_x]
            if cell_type == CellType.WALL:
                return distance, CellType.WALL
            elif cell_type == CellType.STAIRS_DOWN:
                return distance, CellType.STAIRS_DOWN
        
        return self.max_depth, CellType.FLOOR
    
    def get_wall_char(self, distance):
        """Get ASCII character based on distance"""
        if distance >= self.max_depth:
            return ' '
        
        # Map distance to character index
        char_index = int((distance / self.max_depth) * (len(self.wall_chars) - 1))
        char_index = max(0, min(len(self.wall_chars) - 1, char_index))
        return self.wall_chars[char_index]
    
    def get_wall_color(self, distance):
        """Get grayscale color based on distance"""
        if not curses.has_colors():
            return 0
        
        # Use brightness based on distance for grayscale effect (6 tile max visibility)
        if distance < 1.5:
            return curses.color_pair(16) | curses.A_BOLD  # Close: bright white + bold
        elif distance < 3.0:
            return curses.color_pair(16)  # Medium: normal white
        elif distance < 4.5:
            return curses.color_pair(17)  # Far: dim white
        else:
            return curses.color_pair(18)  # Very far: black/dark
    
    def render_column(self, x, distance, wall_type=CellType.WALL):
        """Render a single vertical column at screen position x"""
        # Don't render walls that are too far away - only show them when closer
        wall_visibility_limit = 6  # Walls invisible beyond 6 tiles
        
        if distance >= wall_visibility_limit:
            # Render empty space for distant walls
            for y in range(self.height):
                try:
                    self.stdscr.addch(y, x, ' ')
                except curses.error:
                    pass
            return
        
        # Special handling for stairs - render as lower walls with stairs pattern
        if wall_type == CellType.STAIRS_DOWN:
            # Stairs appear as shorter walls with stair pattern
            wall_height = int(self.wall_height * self.height / max(distance, 0.5) * 0.3)  # 30% height
            wall_start = max(0, self.height - wall_height - 3)  # Bottom aligned
            wall_end = min(self.height - 3, wall_start + wall_height)  # Leave space for floor
            
            stairs_char = '▼'
            stairs_color = curses.color_pair(6) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
            floor_color = curses.color_pair(19) if curses.has_colors() else 0
            
            for y in range(self.height):
                try:
                    if y < wall_start:
                        # Ceiling
                        self.stdscr.addch(y, x, self.ceiling_char)
                    elif y < wall_end:
                        # Stairs pattern
                        if (y - wall_start) % 2 == 0:
                            self.stdscr.addch(y, x, stairs_char, stairs_color)
                        else:
                            self.stdscr.addch(y, x, '═', stairs_color)
                    else:
                        # Floor
                        self.stdscr.addch(y, x, self.floor_char, floor_color)
                except curses.error:
                    pass
        else:
            # Normal wall rendering with much more accurate distance scaling
            # Walls should only fill screen when very close, scale down rapidly with distance
            wall_height = int(self.wall_height * self.height / max(distance * 3.0, 2.0))
            wall_start = max(0, (self.height - wall_height) // 2)
            wall_end = min(self.height, wall_start + wall_height)
            
            wall_char = self.get_wall_char(distance)
            wall_color = self.get_wall_color(distance)
            floor_color = curses.color_pair(19) if curses.has_colors() else 0
            
            for y in range(self.height):
                try:
                    if y < wall_start:
                        # Ceiling
                        self.stdscr.addch(y, x, self.ceiling_char)
                    elif y < wall_end:
                        # Wall with density-based character that changes based on distance
                        # Use different characters for texture variation on the same wall
                        texture_variation = (y + x) % 3
                        if distance < 1.5:
                            # Very close - use solid block
                            render_char = '█'
                        elif distance < 3.0:
                            # Close - dense patterns
                            chars = ['█', '▉', '▊']
                            render_char = chars[texture_variation]
                        elif distance < 4.5:
                            # Medium - medium density
                            chars = ['▋', '▌', '▍']
                            render_char = chars[texture_variation]
                        else:
                            # Far - light patterns (up to 6 tiles)
                            chars = ['▎', '▏', '|']
                            render_char = chars[texture_variation]
                        
                        self.stdscr.addch(y, x, render_char, wall_color)
                    else:
                        # Floor
                        self.stdscr.addch(y, x, self.floor_char, floor_color)
                except curses.error:
                    pass
    
    def render_entities_on_column(self, x, dungeon, player_x, player_y, player_angle, ray_angle, distance):
        """Render entities (monsters, items) on this column if they're visible"""
        # Simple grid-based approach - calculate which tile this ray is hitting
        ray_dx = math.cos(ray_angle)
        ray_dy = math.sin(ray_angle)
        
        # Step along the ray and check each grid cell
        for step in range(1, int(distance) + 1):
            grid_x = int(player_x + ray_dx * step)
            grid_y = int(player_y + ray_dy * step)
            
            # Check all entities at this grid position
            for entity in dungeon.entities:
                if entity.hp <= 0 or entity.type == EntityType.PLAYER:
                    continue
                    
                if entity.pos.x == grid_x and entity.pos.y == grid_y:
                    entity_distance = step
                    
                    # Simple width calculation - closer = wider
                    sprite_width = max(1, 6 - entity_distance)
                    
                    # Check if this column should show the entity
                    entity_center_column = self.width * (ray_angle - player_angle + self.fov/2) / self.fov
                    if abs(x - entity_center_column) <= sprite_width // 2:
                        # Render entity sprite
                        sprite_height = max(2, int(8 * self.height / max(entity_distance * 2, 1.0)))
                        sprite_start = max(0, (self.height - sprite_height) // 2)
                        sprite_end = min(self.height, sprite_start + sprite_height)
                        
                        entity_char = entity.type.value
                        entity_color = self.get_entity_color(entity.type) | curses.A_BOLD
                        
                        for y in range(sprite_start, sprite_end):
                            try:
                                self.stdscr.addch(y, x, entity_char, entity_color)
                            except curses.error:
                                pass
                        return
            
            # Check all items at this grid position
            for item_pos, item in dungeon.items:
                if item_pos.x == grid_x and item_pos.y == grid_y:
                    item_distance = step
                    
                    # Simple width calculation for items
                    sprite_width = max(1, 4 - item_distance)
                    
                    # Check if this column should show the item
                    item_center_column = self.width * (ray_angle - player_angle + self.fov/2) / self.fov
                    if abs(x - item_center_column) <= sprite_width // 2:
                        # Render item sprite
                        sprite_height = max(1, int(4 * self.height / max(item_distance * 2, 1.0)))
                        sprite_start = max(0, self.height - sprite_height - 2)
                        sprite_end = min(self.height - 2, sprite_start + sprite_height)
                        
                        item_char = item.type.value
                        item_color = self.get_entity_color(item.type) | curses.A_BOLD
                        
                        for y in range(sprite_start, sprite_end):
                            try:
                                self.stdscr.addch(y, x, item_char, item_color)
                            except curses.error:
                                pass
                        return
    
    def get_entity_color(self, entity_type):
        """Get color for entity type"""
        if not curses.has_colors():
            return 0
        
        if entity_type == EntityType.PLAYER:
            return curses.color_pair(2)  # Yellow
        elif entity_type in [EntityType.GOBLIN, EntityType.ORC]:
            return curses.color_pair(3)  # Red
        elif entity_type == EntityType.GOLD:
            return curses.color_pair(6)  # Gold
        elif entity_type == EntityType.POTION:
            return curses.color_pair(4)  # Green
        else:
            return curses.color_pair(1)  # White
    
    def get_direction_char(self, angle):
        """Get directional character based on angle"""
        # Normalize angle to 0-2π range
        angle = angle % (2 * math.pi)
        
        # Convert to 8 directions (45-degree increments for better accuracy)
        directions = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']
        direction_index = int((angle + math.pi/8) / (math.pi/4)) % 8
        return directions[direction_index]
    
    def render_minimap(self, dungeon, player_x, player_y, player_angle):
        """Render a small minimap in the corner"""
        map_size = 12
        map_scale = 1
        
        # Position minimap in top-right corner
        map_start_x = self.width - map_size - 2
        map_start_y = 1
        
        if map_start_x < 0 or map_start_y < 0:
            return
        
        # Draw minimap border
        try:
            border_color = curses.color_pair(1) if curses.has_colors() else 0
            for i in range(map_size + 2):
                self.stdscr.addch(map_start_y - 1, map_start_x - 1 + i, '-', border_color)
                self.stdscr.addch(map_start_y + map_size, map_start_x - 1 + i, '-', border_color)
            for i in range(map_size):
                self.stdscr.addch(map_start_y + i, map_start_x - 1, '|', border_color)
                self.stdscr.addch(map_start_y + i, map_start_x + map_size, '|', border_color)
        except curses.error:
            pass
        
        # Draw minimap background
        for my in range(map_size):
            for mx in range(map_size):
                screen_x = map_start_x + mx
                screen_y = map_start_y + my
                
                if screen_x >= self.width or screen_y >= self.height:
                    continue
                
                # Calculate world coordinates (centered on player)
                world_x = int(player_x - map_size//2 + mx)
                world_y = int(player_y - map_size//2 + my)
                
                char = ' '
                color = 0
                
                if (0 <= world_x < dungeon.width and 0 <= world_y < dungeon.height):
                    cell = dungeon.grid[world_y][world_x]
                    if cell == CellType.WALL:
                        char = '█'
                        color = curses.color_pair(16) if curses.has_colors() else 0
                    elif cell == CellType.STAIRS_DOWN:
                        char = '▼'
                        color = curses.color_pair(6) if curses.has_colors() else 0
                    else:
                        char = '·'
                        color = curses.color_pair(7) if curses.has_colors() else 0
                    
                    # Check for entities at this position
                    for entity in dungeon.entities:
                        if entity.pos.x == world_x and entity.pos.y == world_y and entity.hp > 0:
                            if entity.type in [EntityType.GOBLIN, EntityType.ORC]:
                                char = 'E'  # Enemy
                                color = curses.color_pair(3) if curses.has_colors() else 0
                            elif entity.type == EntityType.SHOPKEEPER:
                                char = 'S'
                                color = curses.color_pair(10) if curses.has_colors() else 0
                    
                    # Check for items
                    for item_pos, item in dungeon.items:
                        if item_pos.x == world_x and item_pos.y == world_y:
                            if item.type == EntityType.GOLD:
                                char = '$'
                                color = curses.color_pair(6) if curses.has_colors() else 0
                            else:
                                char = '?'
                                color = curses.color_pair(4) if curses.has_colors() else 0
                
                try:
                    self.stdscr.addch(screen_y, screen_x, char, color)
                except curses.error:
                    pass
        
        # Draw player position with direction indicator
        player_map_x = map_start_x + map_size // 2
        player_map_y = map_start_y + map_size // 2
        
        direction_char = self.get_direction_char(player_angle)
        
        try:
            self.stdscr.addch(player_map_y, player_map_x, direction_char, 
                            curses.color_pair(2) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD)
        except curses.error:
            pass
    
    def render_weapon_sprite(self, player):
        """Render the equipped weapon in the bottom center of the screen"""
        if not player.weapon:
            return
        
        # Weapon sprite positioned in bottom center, classic dungeon crawler style
        weapon_width = 8
        weapon_height = 6
        sprite_x = (self.width - weapon_width) // 2
        sprite_y = self.height - weapon_height - 4  # Move up to avoid UI overlap
        
        # Ensure weapon sprite fits on screen
        if sprite_x < 0 or sprite_y < 0:
            return
        
        weapon_color = curses.color_pair(6) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
        
        # Different weapon sprites based on weapon type/name
        weapon_sprite = self.get_weapon_sprite(player.weapon)
        
        try:
            for y, row in enumerate(weapon_sprite):
                if sprite_y + y >= self.height:
                    break
                for x, char in enumerate(row):
                    if sprite_x + x >= self.width or char == ' ':
                        continue
                    self.stdscr.addch(sprite_y + y, sprite_x + x, char, weapon_color)
        except curses.error:
            pass
    
    def get_weapon_sprite(self, weapon):
        """Get ASCII art sprite for weapon based on its name"""
        name_lower = weapon.name.lower()
        
        if 'sword' in name_lower:
            return [
                "   |    ",
                "   |    ",
                "  |||   ",
                "  |||   ",
                "  /_\\   ",
                " (___) "
            ]
        elif 'dagger' in name_lower or 'knife' in name_lower:
            return [
                "   /    ",
                "  /     ",
                " /      ",
                "/       ",
                "\\       ",
                " \\___   "
            ]
        elif 'axe' in name_lower:
            return [
                "  ___   ",
                " /   \\  ",
                "/     \\ ",
                "\\     / ",
                " \\___/  ",
                "   |    "
            ]
        elif 'mace' in name_lower or 'club' in name_lower:
            return [
                "  ___   ",
                " /###\\  ",
                " |###|  ",
                " \\___/  ",
                "   |    ",
                "   |    "
            ]
        elif 'staff' in name_lower or 'wand' in name_lower:
            return [
                "   *    ",
                "  /|\\   ",
                "   |    ",
                "   |    ",
                "   |    ",
                "  ___   "
            ]
        else:
            # Generic weapon sprite
            return [
                "   )    ",
                "  ))    ",
                " )))    ",
                "  ))    ",
                "  ))    ",
                " (__    "
            ]
    
    def render_ui(self, game):
        """Render 3D UI elements"""
        if not game.dungeon.player:
            return
        
        player = game.dungeon.player
        ui_y = self.height - 3
        
        try:
            ui_color = curses.color_pair(8) if curses.has_colors() else 0
            
            # Health bar
            hp_bar = f"HP: {player.hp}/{player.max_hp}"
            self.stdscr.addstr(ui_y, 1, hp_bar, ui_color)
            
            # Weapon info
            if player.weapon:
                weapon_info = f"Weapon: {player.weapon.name}"
                self.stdscr.addstr(ui_y + 1, 1, weapon_info, ui_color)
            
            # Level and gold
            level_info = f"Floor: {game.current_level} | Gold: {player.gold}"
            self.stdscr.addstr(ui_y, self.width - len(level_info) - 1, level_info, ui_color)
            
            # Controls reminder
            controls = "Arrows: Turn | WASD: Move | I: Inventory | Q: Quit"
            if len(controls) < self.width:
                self.stdscr.addstr(self.height - 1, 1, controls, ui_color)
            
        except curses.error:
            pass
    
    def render_scene(self, game, player_x, player_y, player_angle):
        """Render the complete 3D scene"""
        self.stdscr.clear()
        
        dungeon = game.dungeon
        
        # Cast rays for each column of the screen
        for x in range(self.width):
            # Calculate ray angle for this column
            ray_angle = player_angle - self.fov/2 + (x / self.width) * self.fov
            
            # Cast ray
            distance, wall_type = self.cast_ray(dungeon, player_x, player_y, ray_angle)
            
            # Render the column with wall type
            self.render_column(x, distance, wall_type)
            
            # Render entities on this column
            self.render_entities_on_column(x, dungeon, player_x, player_y, player_angle, ray_angle, distance)
        
        # Render UI elements
        self.render_minimap(dungeon, player_x, player_y, player_angle)
        self.render_ui(game)
        
        # Render equipped weapon sprite
        if game.dungeon.player:
            self.render_weapon_sprite(game.dungeon.player)
        
        self.stdscr.refresh()