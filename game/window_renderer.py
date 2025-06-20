"""
Windowed renderer for AIRogue using pygame
Replaces curses-based terminal rendering with a proper window
"""

import pygame
import math
import sys
from typing import Dict, Tuple, Optional, List
from .entities import EntityType, Entity, Position
from .dungeon import CellType


class Colors:
    """Color constants for rendering"""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    DARK_GREEN = (0, 128, 0)
    DARK_RED = (128, 0, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    BROWN = (139, 69, 19)


class WindowRenderer:
    """Main window renderer using pygame"""
    
    def __init__(self, width=1024, height=768):
        pygame.init()
        pygame.font.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("AIRogue - Windowed Edition")
        
        # Fonts for different UI elements
        self.font_mono = pygame.font.Font(None, 16)  # Monospace for ASCII
        self.font_ui = pygame.font.Font(None, 24)    # UI text
        self.font_title = pygame.font.Font(None, 32) # Titles
        
        # Cell size for 2D ASCII mode
        self.cell_width = 12
        self.cell_height = 16
        
        # Color mapping for entities and cells
        self.entity_colors = {
            EntityType.PLAYER: Colors.YELLOW,
            EntityType.GOBLIN: Colors.RED,
            EntityType.ORC: Colors.DARK_RED,
            EntityType.POTION: Colors.GREEN,
            EntityType.WEAPON: Colors.CYAN,
            EntityType.SHIELD: Colors.CYAN,
            EntityType.GOLD: Colors.YELLOW,
            EntityType.SHOPKEEPER: Colors.MAGENTA,
            EntityType.SPELLBOOK: Colors.PURPLE,
            EntityType.BOSS: Colors.RED
        }
        
        self.cell_colors = {
            CellType.FLOOR: Colors.DARK_GRAY,
            CellType.WALL: Colors.WHITE,
            CellType.STAIRS_DOWN: Colors.WHITE
        }
        
        # 3D renderer for raycasting mode
        self.renderer_3d = None
        
        # UI layout constants
        self.game_area_height = 400  # Height reserved for game area
        self.ui_area_y = self.game_area_height + 10  # Y position where UI starts
        
        self.clock = pygame.time.Clock()
        
    def handle_events(self) -> List[str]:
        """Handle pygame events and return list of key commands"""
        commands = []
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                commands.append('quit')
            elif event.type == pygame.KEYDOWN:
                # Map pygame keys to game commands
                key_map = {
                    pygame.K_w: 'move_up',
                    pygame.K_s: 'move_down', 
                    pygame.K_a: 'move_left',
                    pygame.K_d: 'move_right',
                    pygame.K_UP: 'move_up',
                    pygame.K_DOWN: 'move_down',
                    pygame.K_LEFT: 'move_left',
                    pygame.K_RIGHT: 'move_right',
                    pygame.K_h: 'move_left',
                    pygame.K_j: 'move_down',
                    pygame.K_k: 'move_up',
                    pygame.K_l: 'move_right',
                    pygame.K_i: 'inventory',
                    pygame.K_m: 'spells',
                    pygame.K_f: 'cast_spell',
                    pygame.K_g: 'godmode',
                    pygame.K_s: 'move_down',
                    pygame.K_q: 'quit',
                    pygame.K_e: 'exit_shop',
                    pygame.K_ESCAPE: 'cancel',
                    pygame.K_RETURN: 'confirm',
                    pygame.K_1: 'num_1',
                    pygame.K_2: 'num_2',
                    pygame.K_3: 'num_3',
                    pygame.K_4: 'num_4',
                    pygame.K_5: 'num_5',
                    pygame.K_6: 'num_6',
                    pygame.K_7: 'num_7',
                    pygame.K_8: 'num_8',
                    pygame.K_9: 'num_9',
                }
                
                # Handle shift+numbers for selling and save
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    shift_map = {
                        pygame.K_1: 'sell_1',
                        pygame.K_2: 'sell_2',
                        pygame.K_3: 'sell_3',
                        pygame.K_4: 'sell_4',
                        pygame.K_5: 'sell_5',
                        pygame.K_6: 'sell_6',
                        pygame.K_7: 'sell_7',
                        pygame.K_8: 'sell_8',
                        pygame.K_9: 'sell_9',
                        pygame.K_s: 'save',
                    }
                    if event.key in shift_map:
                        commands.append(shift_map[event.key])
                        continue
                
                if event.key in key_map:
                    commands.append(key_map[event.key])
                    
        return commands
    
    def clear_screen(self):
        """Clear the screen"""
        self.screen.fill(Colors.BLACK)
    
    def draw_2d_ascii(self, game):
        """Draw the game in 2D ASCII mode"""
        if not game.dungeon:
            return
            
        # Calculate game area offset to center the dungeon
        dungeon_pixel_width = game.dungeon.width * self.cell_width
        dungeon_pixel_height = game.dungeon.height * self.cell_height
        offset_x = max(0, (self.width - dungeon_pixel_width) // 2)
        offset_y = max(0, (self.game_area_height - dungeon_pixel_height) // 2)
        
        # Draw dungeon grid
        for y in range(game.dungeon.height):
            for x in range(game.dungeon.width):
                cell = game.dungeon.grid[y][x]
                px = offset_x + x * self.cell_width
                py = offset_y + y * self.cell_height
                
                # Background color based on cell type
                bg_color = self.cell_colors.get(cell, Colors.BLACK)
                if cell == CellType.FLOOR:
                    bg_color = Colors.DARK_GRAY
                elif cell == CellType.WALL:
                    bg_color = Colors.GRAY
                
                # Draw cell background
                pygame.draw.rect(self.screen, bg_color, 
                               (px, py, self.cell_width, self.cell_height))
                
                # Draw cell character
                char = cell.value
                color = Colors.WHITE if cell == CellType.WALL else Colors.LIGHT_GRAY
                self.draw_text(char, px + 2, py + 2, self.font_mono, color)
        
        # Draw items
        for item_pos, item in game.dungeon.items:
            px = offset_x + item_pos.x * self.cell_width
            py = offset_y + item_pos.y * self.cell_height
            
            # Item background
            pygame.draw.rect(self.screen, Colors.BLACK,
                           (px, py, self.cell_width, self.cell_height))
            
            # Item character and color
            char = item.type.value
            color = self.entity_colors.get(item.type, Colors.WHITE)
            self.draw_text(char, px + 2, py + 2, self.font_mono, color)
        
        # Draw entities
        for entity in game.dungeon.entities:
            if entity.hp > 0:
                px = offset_x + entity.pos.x * self.cell_width
                py = offset_y + entity.pos.y * self.cell_height
                
                # Entity background
                pygame.draw.rect(self.screen, Colors.BLACK,
                               (px, py, self.cell_width, self.cell_height))
                
                # Entity character and color
                char = entity.type.value
                color = self.entity_colors.get(entity.type, Colors.WHITE)
                
                # Special handling for boss - make it bold/larger
                if entity.type == EntityType.BOSS:
                    pygame.draw.circle(self.screen, color, 
                                     (px + self.cell_width//2, py + self.cell_height//2), 
                                     self.cell_width//2 - 1)
                    self.draw_text(char, px + 2, py + 2, self.font_mono, Colors.BLACK)
                else:
                    self.draw_text(char, px + 2, py + 2, self.font_mono, color)
    
    def draw_3d_scene(self, game):
        """Draw the game in 3D raycasting mode"""
        if not game.dungeon or not game.dungeon.player:
            return
            
        # Initialize 3D renderer if needed
        if not self.renderer_3d:
            from .renderer3d_pygame import PygameRenderer3D
            self.renderer_3d = PygameRenderer3D(self.screen, self.width, self.game_area_height)
        
        player = game.dungeon.player
        # Render 3D scene
        self.renderer_3d.render_scene(game, float(player.pos.x) + 0.5, 
                                    float(player.pos.y) + 0.5, player.angle)
    
    def draw_ui(self, game):
        """Draw the game UI (health, inventory, messages, etc.)"""
        if not game.dungeon or not game.dungeon.player:
            return
            
        player = game.dungeon.player
        ui_y = self.ui_area_y
        
        # Player stats
        hp_text = f"HP: {player.hp}/{player.max_hp}"
        hp_color = Colors.RED if player.hp < player.max_hp * 0.3 else Colors.WHITE
        self.draw_text(hp_text, 10, ui_y, self.font_ui, hp_color)
        
        mp_text = f"MP: {player.mana}/{player.max_mana}"
        self.draw_text(mp_text, 10, ui_y + 25, self.font_ui, Colors.CYAN)
        
        # Attack and Defense
        attack_total = player.attack + (player.weapon.attack_bonus if player.weapon else 0)
        defense_total = (player.defense + 
                        (player.weapon.defense_bonus if player.weapon else 0) +
                        (player.shield.defense_bonus if player.shield else 0))
        
        self.draw_text(f"Attack: {attack_total}", 200, ui_y + 25, self.font_ui, Colors.WHITE)
        self.draw_text(f"Defense: {defense_total}", 300, ui_y + 25, self.font_ui, Colors.WHITE)
        
        # Gold and level
        self.draw_text(f"Gold: {player.gold}", 450, ui_y, self.font_ui, Colors.YELLOW)
        self.draw_text(f"Floor: {game.current_level}", 450, ui_y + 25, self.font_ui, Colors.WHITE)
        
        # Character level and XP or godmode
        if game.godmode:
            self.draw_text("GODMODE", 600, ui_y, self.font_ui, Colors.YELLOW, bold=True)
            self.draw_text(f"Lv: {player.level}", 600, ui_y + 25, self.font_ui, Colors.WHITE)
        else:
            from .levelup import LevelingSystem
            xp_for_next = LevelingSystem.xp_for_next_level(player.level)
            xp_progress = LevelingSystem.get_xp_progress(player.xp, player.level)
            self.draw_text(f"Char Lv: {player.level}", 600, ui_y, self.font_ui, Colors.WHITE)
            self.draw_text(f"XP: {xp_progress}/{xp_for_next}", 600, ui_y + 25, self.font_ui, Colors.WHITE)
        
        # Equipment
        equipment_y = ui_y + 60
        if player.weapon:
            weapon_text = f"Weapon: {player.weapon.name}"
            self.draw_text(weapon_text, 10, equipment_y, self.font_ui, Colors.CYAN)
            equipment_y += 25
            
        if player.shield:
            if player.shield.type == EntityType.SPELLBOOK:
                shield_text = f"Spellbook: {player.shield.name} (+{player.shield.magic_bonus})"
                color = Colors.PURPLE
            else:
                shield_text = f"Shield: {player.shield.name} (+{player.shield.defense_bonus})"
                color = Colors.CYAN
            self.draw_text(shield_text, 10, equipment_y, self.font_ui, color)
            equipment_y += 25
        
        # Messages
        message_y = equipment_y + 10
        for i, msg in enumerate(game.messages[-5:]):  # Show last 5 messages
            self.draw_text(msg, 10, message_y + i * 20, self.font_ui, Colors.LIGHT_GRAY)
        
        # Controls/Instructions
        controls_y = self.height - 60
        if game.render_3d:
            controls = "3D: Arrows turn, WASD move, I: inventory, M: spells, F: cast, G: godmode, 3: toggle 2D/3D, S: save, Q: quit"
        else:
            controls = "Move: wasd/hjkl/arrows, Inventory: i, M: spells, F: cast, G: godmode, 3: toggle 2D/3D, Save: S, Quit: q"
        
        self.draw_text(controls, 10, controls_y, self.font_ui, Colors.GRAY)
    
    def draw_inventory_screen(self, game):
        """Draw the inventory screen"""
        self.clear_screen()
        
        # Background
        pygame.draw.rect(self.screen, Colors.DARK_GRAY, 
                        (50, 50, self.width - 100, self.height - 100))
        pygame.draw.rect(self.screen, Colors.WHITE,
                        (50, 50, self.width - 100, self.height - 100), 2)
        
        # Title
        self.draw_text("=== INVENTORY ===", 70, 70, self.font_title, Colors.YELLOW)
        
        player = game.dungeon.player
        self.draw_text(f"Gold: {player.gold}", 70, 110, self.font_ui, Colors.YELLOW)
        
        y = 150
        
        # Equipped items
        if player.weapon:
            if player.weapon.defense_bonus > 0:
                weapon_text = f"Weapon: {player.weapon.name} (+{player.weapon.defense_bonus} defense)"
            else:
                weapon_text = f"Weapon: {player.weapon.name} (+{player.weapon.attack_bonus} attack)"
            self.draw_text(weapon_text, 70, y, self.font_ui, Colors.CYAN)
            y += 25
            
        if player.shield:
            if player.shield.type == EntityType.SPELLBOOK:
                shield_text = f"Spellbook: {player.shield.name} (+{player.shield.magic_bonus} magic)"
                color = Colors.PURPLE
            else:
                shield_text = f"Shield: {player.shield.name} (+{player.shield.defense_bonus} defense)"
                color = Colors.CYAN
            self.draw_text(shield_text, 70, y, self.font_ui, color)
            y += 25
        
        # Items
        y += 20
        self.draw_text("Items:", 70, y, self.font_title, Colors.WHITE)
        y += 30
        
        if player.inventory:
            for i, item in enumerate(player.inventory):
                prefix = f"{i+1}. "
                if item.type == EntityType.WEAPON:
                    if item.defense_bonus > 0:
                        desc = f"{item.name} (+{item.defense_bonus} defense) - Press {i+1} to equip"
                    else:
                        desc = f"{item.name} (+{item.attack_bonus} attack) - Press {i+1} to equip"
                    color = Colors.CYAN
                elif item.type == EntityType.SHIELD:
                    desc = f"{item.name} (+{item.defense_bonus} defense) - Press {i+1} to equip"
                    color = Colors.CYAN
                elif item.type == EntityType.SPELLBOOK:
                    desc = f"{item.name} (+{item.magic_bonus} magic) - Press {i+1} to equip"
                    color = Colors.PURPLE
                elif item.type == EntityType.POTION:
                    desc = f"{item.name} (heals {item.heal_amount} HP) - Press {i+1} to use"
                    color = Colors.GREEN
                else:
                    desc = item.name
                    color = Colors.WHITE
                
                self.draw_text(prefix + desc, 70, y, self.font_ui, color)
                y += 25
        else:
            self.draw_text("(Empty)", 70, y, self.font_ui, Colors.GRAY)
        
        # Close instruction
        self.draw_text("Press 'i' to close inventory", 70, self.height - 120, self.font_ui, Colors.YELLOW)
    
    def draw_shop_screen(self, game):
        """Draw the shop screen"""
        self.clear_screen()
        
        # Background
        pygame.draw.rect(self.screen, Colors.DARK_GRAY,
                        (50, 50, self.width - 100, self.height - 100))
        pygame.draw.rect(self.screen, Colors.WHITE,
                        (50, 50, self.width - 100, self.height - 100), 2)
        
        # Title and gold
        self.draw_text("=== MYSTICAL SHOP ===", 70, 70, self.font_title, Colors.MAGENTA)
        self.draw_text(f"Your Gold: {game.dungeon.player.gold}", 70, 110, self.font_ui, Colors.YELLOW)
        self.draw_text("Shopkeeper: 'Welcome, traveler! Buy or sell your wares!'", 
                      70, 140, self.font_ui, Colors.MAGENTA)
        
        y = 180
        
        # Shop inventory
        self.draw_text("SHOP INVENTORY (Press number to BUY):", 70, y, self.font_title, Colors.WHITE)
        y += 30
        
        for i, item in enumerate(game.shop.items):
            color = Colors.CYAN if item.type in [EntityType.WEAPON, EntityType.SHIELD] else Colors.GREEN
            if item.type == EntityType.WEAPON:
                if item.defense_bonus > 0:
                    desc = f"{i+1}. {item.name} (+{item.defense_bonus} defense) - {item.value} gold"
                else:
                    desc = f"{i+1}. {item.name} (+{item.attack_bonus} attack) - {item.value} gold"
            elif item.type == EntityType.SHIELD:
                desc = f"{i+1}. {item.name} (+{item.defense_bonus} defense) - {item.value} gold"
            else:
                desc = f"{i+1}. {item.name} (heals {item.heal_amount} HP) - {item.value} gold"
            
            self.draw_text(desc, 70, y, self.font_ui, color)
            y += 25
        
        # Player inventory for selling
        y += 20
        self.draw_text("YOUR INVENTORY (Press Shift+number to SELL):", 70, y, self.font_title, Colors.WHITE)
        y += 30
        
        for i, item in enumerate(game.dungeon.player.inventory[:9]):  # Show first 9
            sell_price = max(1, item.value // 2)
            color = Colors.CYAN if item.type in [EntityType.WEAPON, EntityType.SHIELD] else Colors.GREEN
            
            if item.type == EntityType.WEAPON:
                if item.defense_bonus > 0:
                    desc = f"Shift+{i+1}. {item.name} (+{item.defense_bonus} defense) - Sell for {sell_price} gold"
                else:
                    desc = f"Shift+{i+1}. {item.name} (+{item.attack_bonus} attack) - Sell for {sell_price} gold"
            elif item.type == EntityType.SHIELD:
                desc = f"Shift+{i+1}. {item.name} (+{item.defense_bonus} defense) - Sell for {sell_price} gold"
            else:
                desc = f"Shift+{i+1}. {item.name} (heals {item.heal_amount} HP) - Sell for {sell_price} gold"
            
            self.draw_text(desc, 70, y, self.font_ui, color)
            y += 25
        
        # Exit instruction
        self.draw_text("Press 'e' to exit shop", 70, self.height - 120, self.font_ui, Colors.YELLOW)
    
    def draw_spell_screen(self, game):
        """Draw the spell screen"""
        self.clear_screen()
        
        # Background
        pygame.draw.rect(self.screen, Colors.DARK_GRAY,
                        (50, 50, self.width - 100, self.height - 100))
        pygame.draw.rect(self.screen, Colors.WHITE,
                        (50, 50, self.width - 100, self.height - 100), 2)
        
        # Title
        self.draw_text("=== SPELLBOOK ===", 70, 70, self.font_title, Colors.PURPLE, bold=True)
        
        player = game.dungeon.player
        if not player:
            return
        
        # Mana display
        self.draw_text(f"Mana: {player.mana}/{player.max_mana}", 70, 110, self.font_ui, Colors.CYAN)
        
        # Equipped spellbook
        y = 140
        if player.shield and player.shield.type == EntityType.SPELLBOOK:
            self.draw_text(f"Equipped: {player.shield.name}", 70, y, self.font_ui, Colors.PURPLE)
        y += 40
        
        # Known spells
        self.draw_text("Known Spells:", 70, y, self.font_title, Colors.WHITE)
        y += 30
        
        if player.known_spells:
            for spell in player.known_spells:
                color = Colors.GREEN if player.mana >= spell.mana_cost else Colors.RED
                spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP)"
                self.draw_text(spell_text, 70, y, self.font_ui, color)
                self.draw_text(f"    {spell.description}", 70, y + 20, self.font_ui, Colors.GRAY)
                y += 50
        else:
            self.draw_text("  (No spells learned)", 70, y, self.font_ui, Colors.GRAY)
            y += 30
        
        # Available spells from equipped spellbook
        spellbook_spells = game.magic_system.get_equipped_spellbook_spells(player)
        if spellbook_spells:
            y += 20
            self.draw_text("Available from Equipped Spellbook:", 70, y, self.font_title, Colors.WHITE)
            y += 30
            
            for spell in spellbook_spells:
                already_known = any(s.spell_type == spell.spell_type for s in player.known_spells)
                
                if already_known:
                    color = Colors.GRAY
                    spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP) - Already Known"
                else:
                    color = Colors.YELLOW
                    spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP) - Press L to Learn"
                
                self.draw_text(spell_text, 70, y, self.font_ui, color)
                self.draw_text(f"    {spell.description}", 70, y + 20, self.font_ui, Colors.GRAY)
                y += 50
        
        # Instructions
        self.draw_text("Press 'L' to learn available spells", 70, self.height - 150, self.font_ui, Colors.YELLOW)
        self.draw_text("Press 'M' to close spellbook", 70, self.height - 120, self.font_ui, Colors.YELLOW)
    
    def draw_death_screen(self, game):
        """Draw the death screen"""
        self.clear_screen()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Center position
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Death message
        death_msg = "YOU HAVE DIED!"
        self.draw_text_centered(death_msg, center_y - 100, self.font_title, Colors.RED, bold=True)
        
        # Game stats
        level_msg = f"You reached level {game.current_level}"
        self.draw_text_centered(level_msg, center_y - 60, self.font_ui, Colors.WHITE)
        
        if game.dungeon.player:
            gold_msg = f"Final gold: {game.dungeon.player.gold}"
            self.draw_text_centered(gold_msg, center_y - 30, self.font_ui, Colors.WHITE)
        
        # Options
        self.draw_text_centered("What would you like to do?", center_y + 20, self.font_ui, Colors.WHITE)
        self.draw_text_centered("1) Restart from scratch", center_y + 60, self.font_ui, Colors.WHITE)
        self.draw_text_centered("2) Load saved game", center_y + 90, self.font_ui, Colors.WHITE)
        self.draw_text_centered("3) Quit to desktop", center_y + 120, self.font_ui, Colors.WHITE)
        
        # Instructions
        self.draw_text_centered("Press 1, 2, or 3 to select an option", center_y + 160, self.font_ui, Colors.YELLOW)
    
    def draw_victory_screen(self, game):
        """Draw the victory screen"""
        self.clear_screen()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Center position
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Victory message
        self.draw_text_centered("VICTORY!", center_y - 120, self.font_title, Colors.YELLOW, bold=True)
        self.draw_text_centered("You are the Champion of the Dungeon!", center_y - 80, self.font_ui, Colors.WHITE)
        
        # Game stats
        level_msg = f"You conquered {game.current_level} levels of the dungeon"
        self.draw_text_centered(level_msg, center_y - 40, self.font_ui, Colors.WHITE)
        
        if game.dungeon.player:
            char_level_msg = f"Character level: {game.dungeon.player.level}"
            self.draw_text_centered(char_level_msg, center_y - 10, self.font_ui, Colors.WHITE)
            
            gold_msg = f"Final treasure: {game.dungeon.player.gold} gold"
            self.draw_text_centered(gold_msg, center_y + 20, self.font_ui, Colors.YELLOW)
        
        # Options
        self.draw_text_centered("What would you like to do?", center_y + 60, self.font_ui, Colors.WHITE)
        self.draw_text_centered("1) Start a new adventure", center_y + 100, self.font_ui, Colors.WHITE)
        self.draw_text_centered("2) Load saved game", center_y + 130, self.font_ui, Colors.WHITE)
        self.draw_text_centered("3) Quit to desktop", center_y + 160, self.font_ui, Colors.WHITE)
        
        # Instructions
        self.draw_text_centered("Press 1, 2, or 3 to select an option", center_y + 200, self.font_ui, Colors.YELLOW)
    
    def draw_levelup_screen(self, game):
        """Draw the level up screen"""
        self.clear_screen()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Center position
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Level up message
        level_msg = f"LEVEL UP! You are now level {game.dungeon.player.level}!"
        self.draw_text_centered(level_msg, center_y - 120, self.font_title, Colors.YELLOW, bold=True)
        
        # Instruction
        self.draw_text_centered("Choose your reward:", center_y - 80, self.font_ui, Colors.WHITE)
        
        # Reward options
        for i, reward in enumerate(game.levelup_rewards):
            option_text = f"{i+1}) {reward.name}"
            desc_text = f"   {reward.description}"
            
            self.draw_text_centered(option_text, center_y - 40 + i * 40, self.font_ui, Colors.WHITE, bold=True)
            self.draw_text_centered(desc_text, center_y - 20 + i * 40, self.font_ui, Colors.WHITE)
        
        # Bottom instruction
        bottom_instruction = f"Press 1-{len(game.levelup_rewards)} to select your reward"
        self.draw_text_centered(bottom_instruction, center_y + 120, self.font_ui, Colors.YELLOW)
    
    def draw_text(self, text: str, x: int, y: int, font: pygame.font.Font, 
                  color: Tuple[int, int, int], bold: bool = False):
        """Draw text at specified position"""
        if bold:
            font.set_bold(True)
        
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))
        
        if bold:
            font.set_bold(False)
    
    def draw_text_centered(self, text: str, y: int, font: pygame.font.Font,
                          color: Tuple[int, int, int], bold: bool = False):
        """Draw text centered horizontally at specified y position"""
        if bold:
            font.set_bold(True)
        
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.width // 2, y))
        self.screen.blit(text_surface, text_rect)
        
        if bold:
            font.set_bold(False)
    
    def update_display(self):
        """Update the display"""
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS
    
    def quit(self):
        """Clean up and quit"""
        pygame.quit()