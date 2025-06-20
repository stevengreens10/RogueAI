"""
Pygame-based 3D raycasting renderer
Converts the original curses 3D renderer to work with pygame
"""

import pygame
import math
from typing import Dict, Tuple, List
from .entities import EntityType, Entity, Position
from .dungeon import CellType


class PygameRenderer3D:
    """3D raycasting renderer using pygame"""
    
    def __init__(self, screen: pygame.Surface, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height
        self.fov = math.pi / 3  # 60 degree field of view
        self.max_depth = 20.0
        
        # Colors for walls and floor/ceiling
        self.wall_color = (100, 100, 100)
        self.dark_wall_color = (50, 50, 50)
        self.floor_color = (30, 30, 30)
        self.ceiling_color = (20, 20, 20)
        
        # Entity colors for 3D rendering
        self.entity_colors = {
            EntityType.GOBLIN: (255, 0, 0),
            EntityType.ORC: (150, 0, 0),
            EntityType.POTION: (0, 255, 0),
            EntityType.WEAPON: (0, 255, 255),
            EntityType.SHIELD: (0, 200, 255),
            EntityType.GOLD: (255, 255, 0),
            EntityType.SHOPKEEPER: (255, 0, 255),
            EntityType.SPELLBOOK: (128, 0, 255),
            EntityType.BOSS: (255, 0, 0)
        }
        
        # Minimap settings
        self.minimap_size = 150
        self.minimap_x = width - self.minimap_size - 10
        self.minimap_y = 10
        
    def render_scene(self, game, player_x: float, player_y: float, player_angle: float):
        """Render the 3D scene using raycasting"""
        # Clear the 3D rendering area
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, self.width, self.height))
        
        # Draw floor and ceiling
        self.draw_floor_ceiling()
        
        # Cast rays for each column of pixels
        for x in range(self.width):
            # Calculate ray angle
            camera_x = 2 * x / self.width - 1  # -1 to 1
            ray_angle = player_angle + math.atan(camera_x * math.tan(self.fov / 2))
            
            # Cast ray
            distance, hit_vertical = self.cast_ray(game.dungeon, player_x, player_y, ray_angle)
            
            if distance < self.max_depth:
                # Calculate wall height on screen
                wall_height = int(self.height / distance) if distance > 0 else self.height
                
                # Calculate draw start and end
                draw_start = max(0, (-wall_height // 2) + (self.height // 2))
                draw_end = min(self.height - 1, (wall_height // 2) + (self.height // 2))
                
                # Choose wall color based on direction (vertical walls darker)
                wall_color = self.dark_wall_color if hit_vertical else self.wall_color
                
                # Draw wall column
                if draw_end > draw_start:
                    pygame.draw.line(self.screen, wall_color, (x, draw_start), (x, draw_end))
        
        # Render entities in 3D space
        self.render_entities_3d(game, player_x, player_y, player_angle)
        
        # Draw weapon sprite
        self.draw_weapon_sprite(game)
        
        # Draw minimap
        self.draw_minimap(game, player_x, player_y, player_angle)
    
    def cast_ray(self, dungeon, start_x: float, start_y: float, angle: float) -> Tuple[float, bool]:
        """Cast a ray and return distance to wall and whether it hit a vertical wall"""
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # DDA algorithm for raycasting
        map_x = int(start_x)
        map_y = int(start_y)
        
        if dx == 0:
            delta_dist_x = float('inf')
        else:
            delta_dist_x = abs(1 / dx)
            
        if dy == 0:
            delta_dist_y = float('inf')
        else:
            delta_dist_y = abs(1 / dy)
        
        if dx < 0:
            step_x = -1
            side_dist_x = (start_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - start_x) * delta_dist_x
            
        if dy < 0:
            step_y = -1
            side_dist_y = (start_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - start_y) * delta_dist_y
        
        # Perform DDA
        hit = False
        side = 0  # 0 for x-side, 1 for y-side
        
        while not hit:
            # Jump to next map square, either in x-direction, or in y-direction
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            # Check if ray is out of bounds or hit a wall
            if (map_x < 0 or map_x >= dungeon.width or 
                map_y < 0 or map_y >= dungeon.height or
                dungeon.grid[map_y][map_x] == CellType.WALL):
                hit = True
        
        # Calculate distance
        if side == 0:
            perp_wall_dist = (map_x - start_x + (1 - step_x) / 2) / dx
        else:
            perp_wall_dist = (map_y - start_y + (1 - step_y) / 2) / dy
        
        return abs(perp_wall_dist), side == 0
    
    def draw_floor_ceiling(self):
        """Draw floor and ceiling"""
        # Ceiling (top half)
        pygame.draw.rect(self.screen, self.ceiling_color, 
                        (0, 0, self.width, self.height // 2))
        
        # Floor (bottom half)
        pygame.draw.rect(self.screen, self.floor_color,
                        (0, self.height // 2, self.width, self.height // 2))
    
    def render_entities_3d(self, game, player_x: float, player_y: float, player_angle: float):
        """Render entities in 3D space as sprites"""
        # Collect all visible entities with their distances
        entities_to_render = []
        
        # Add entities
        for entity in game.dungeon.entities:
            if entity.hp > 0 and entity.type != EntityType.PLAYER:
                dx = entity.pos.x + 0.5 - player_x
                dy = entity.pos.y + 0.5 - player_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < self.max_depth:
                    entities_to_render.append((entity, distance, dx, dy, 'entity'))
        
        # Add items
        for item_pos, item in game.dungeon.items:
            dx = item_pos.x + 0.5 - player_x
            dy = item_pos.y + 0.5 - player_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < self.max_depth:
                entities_to_render.append((item, distance, dx, dy, 'item'))
        
        # Sort by distance (farthest first for proper depth rendering)
        entities_to_render.sort(key=lambda x: x[1], reverse=True)
        
        # Render each entity
        for obj, distance, dx, dy, obj_type in entities_to_render:
            self.render_sprite(obj, distance, dx, dy, player_angle, obj_type)
    
    def render_sprite(self, obj, distance: float, dx: float, dy: float, 
                     player_angle: float, obj_type: str):
        """Render a single sprite (entity or item)"""
        # Calculate sprite angle relative to player
        sprite_angle = math.atan2(dy, dx) - player_angle
        
        # Normalize angle to [-pi, pi]
        while sprite_angle > math.pi:
            sprite_angle -= 2 * math.pi
        while sprite_angle < -math.pi:
            sprite_angle += 2 * math.pi
        
        # Check if sprite is in field of view
        if abs(sprite_angle) > self.fov / 2:
            return
        
        # Calculate screen position
        screen_x = int((sprite_angle / (self.fov / 2) + 1) * self.width / 2)
        
        # Calculate sprite size based on distance
        sprite_height = int(self.height / distance) if distance > 0 else self.height
        sprite_width = sprite_height  # Square sprites
        
        # Don't render if too small
        if sprite_height < 4:
            return
        
        # Calculate draw bounds
        draw_start_y = max(0, (self.height - sprite_height) // 2)
        draw_end_y = min(self.height, (self.height + sprite_height) // 2)
        draw_start_x = max(0, screen_x - sprite_width // 2)
        draw_end_x = min(self.width, screen_x + sprite_width // 2)
        
        # Get color for this object
        if obj_type == 'entity':
            color = self.entity_colors.get(obj.type, (255, 255, 255))
            # Special handling for boss - make it larger and more prominent
            if obj.type == EntityType.BOSS:
                sprite_height = int(sprite_height * 1.5)
                draw_start_y = max(0, (self.height - sprite_height) // 2)
                draw_end_y = min(self.height, (self.height + sprite_height) // 2)
        else:  # item
            color = self.entity_colors.get(obj.type, (255, 255, 255))
        
        # Draw sprite as a colored rectangle
        sprite_rect = pygame.Rect(draw_start_x, draw_start_y, 
                                 draw_end_x - draw_start_x, draw_end_y - draw_start_y)
        pygame.draw.rect(self.screen, color, sprite_rect)
        
        # Add a border for better visibility
        pygame.draw.rect(self.screen, (255, 255, 255), sprite_rect, 1)
        
        # For entities, draw a simple character representation
        if obj_type == 'entity' and sprite_height > 16:
            font = pygame.font.Font(None, min(24, sprite_height // 2))
            char_surface = font.render(obj.type.value, True, (0, 0, 0))
            char_rect = char_surface.get_rect(center=sprite_rect.center)
            self.screen.blit(char_surface, char_rect)
    
    def draw_weapon_sprite(self, game):
        """Draw the player's weapon at the bottom of the screen"""
        if not game.dungeon.player or not game.dungeon.player.weapon:
            return
        
        weapon = game.dungeon.player.weapon
        
        # Simple weapon sprite at bottom center
        weapon_width = 100
        weapon_height = 150
        weapon_x = self.width // 2 - weapon_width // 2
        weapon_y = self.height - weapon_height
        
        # Draw weapon based on type
        weapon_color = (150, 150, 150)  # Default gray
        
        if 'sword' in weapon.name.lower():
            # Draw a sword shape
            pygame.draw.rect(self.screen, weapon_color, 
                           (weapon_x + 40, weapon_y, 20, 120))  # Blade
            pygame.draw.rect(self.screen, (100, 50, 0),
                           (weapon_x + 30, weapon_y + 100, 40, 20))  # Hilt
        elif 'staff' in weapon.name.lower():
            # Draw a staff shape
            pygame.draw.rect(self.screen, (139, 69, 19),
                           (weapon_x + 45, weapon_y, 10, 140))  # Staff
            pygame.draw.circle(self.screen, (255, 0, 255),
                             (weapon_x + 50, weapon_y + 10), 15)  # Orb
        else:
            # Generic weapon
            pygame.draw.polygon(self.screen, weapon_color, [
                (weapon_x + 50, weapon_y),
                (weapon_x + 30, weapon_y + 80),
                (weapon_x + 70, weapon_y + 80)
            ])
    
    def draw_minimap(self, game, player_x: float, player_y: float, player_angle: float):
        """Draw a minimap in the corner"""
        if not game.dungeon:
            return
        
        # Minimap background
        minimap_rect = pygame.Rect(self.minimap_x, self.minimap_y, 
                                  self.minimap_size, self.minimap_size)
        pygame.draw.rect(self.screen, (0, 0, 0), minimap_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), minimap_rect, 2)
        
        # Calculate scale
        scale_x = self.minimap_size / game.dungeon.width
        scale_y = self.minimap_size / game.dungeon.height
        
        # Draw dungeon layout
        for y in range(game.dungeon.height):
            for x in range(game.dungeon.width):
                cell = game.dungeon.grid[y][x]
                
                mini_x = self.minimap_x + int(x * scale_x)
                mini_y = self.minimap_y + int(y * scale_y)
                mini_w = max(1, int(scale_x))
                mini_h = max(1, int(scale_y))
                
                if cell == CellType.WALL:
                    color = (100, 100, 100)
                elif cell == CellType.FLOOR:
                    color = (30, 30, 30)
                elif cell == CellType.STAIRS_DOWN:
                    color = (0, 255, 0)
                else:
                    continue
                
                pygame.draw.rect(self.screen, color,
                               (mini_x, mini_y, mini_w, mini_h))
        
        # Draw entities on minimap
        for entity in game.dungeon.entities:
            if entity.hp > 0 and entity.type != EntityType.PLAYER:
                mini_x = self.minimap_x + int(entity.pos.x * scale_x)
                mini_y = self.minimap_y + int(entity.pos.y * scale_y)
                
                color = (255, 0, 0) if entity.type in [EntityType.GOBLIN, EntityType.ORC, EntityType.BOSS] else (255, 255, 0)
                pygame.draw.circle(self.screen, color, (mini_x, mini_y), 2)
        
        # Draw items on minimap
        for item_pos, item in game.dungeon.items:
            mini_x = self.minimap_x + int(item_pos.x * scale_x)
            mini_y = self.minimap_y + int(item_pos.y * scale_y)
            
            color = (0, 255, 0) if item.type == EntityType.POTION else (255, 255, 0)
            pygame.draw.circle(self.screen, color, (mini_x, mini_y), 1)
        
        # Draw player position and direction
        player_mini_x = self.minimap_x + int(player_x * scale_x)
        player_mini_y = self.minimap_y + int(player_y * scale_y)
        
        # Player dot
        pygame.draw.circle(self.screen, (0, 255, 255), 
                          (player_mini_x, player_mini_y), 3)
        
        # Player direction line
        dir_length = 8
        dir_end_x = player_mini_x + int(math.cos(player_angle) * dir_length)
        dir_end_y = player_mini_y + int(math.sin(player_angle) * dir_length)
        pygame.draw.line(self.screen, (0, 255, 255),
                        (player_mini_x, player_mini_y), (dir_end_x, dir_end_y), 2)