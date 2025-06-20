#!/usr/bin/env python3
"""
AIRogue - A CLI-based roguelike game
Cross-platform compatible (Windows, macOS, Linux)
"""

import random
import sys
import os
import math
import platform

# Windows-compatible curses import
try:
    import curses
except ImportError:
    print("Error: curses module not found!")
    print("On Windows, install with: pip install windows-curses")
    print("On other systems, curses should be included with Python")
    sys.exit(1)

from game.entities import Entity, EntityType, Item, Position
from game.dungeon import Dungeon, CellType
from game.shop import Shop
from game.combat import CombatSystem
from game.levelup import LevelingSystem, LevelUpReward
from game.save_load import SaveLoadSystem
from game.intro import IntroScreen
from game.renderer3d import Renderer3D
from game.magic import MagicSystem
from game.boss import BossSystem


class WindowsCompatibility:
    """Handle Windows-specific terminal compatibility"""
    
    @staticmethod
    def setup_windows_terminal():
        """Configure Windows terminal for better compatibility"""
        if platform.system() == "Windows":
            # Enable ANSI escape sequences on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass  # Ignore if it fails
    
    @staticmethod
    def get_safe_char(char, fallback='?'):
        """Get a Windows-safe character with fallback"""
        if platform.system() == "Windows":
            # Windows-safe character replacements
            replacements = {
                '▼': 'v',  # Down stairs
                '▲': '^',  # Up stairs (if used)
                '►': '>',  # Right arrow
                '◄': '<',  # Left arrow
                '♦': '*',  # Diamond
                '♠': '*',  # Spade
                '♣': '*',  # Club
                '♥': '*',  # Heart
                '█': '#',  # Block
                '▒': ':',  # Medium shade
                '░': '.',  # Light shade
            }
            return replacements.get(char, char)
        return char


class Game:
    def __init__(self, stdscr, load_game=False):
        self.stdscr = stdscr
        self.messages = []
        self.game_over = False
        self.show_inventory = False
        self.in_shop = False
        self.shop = None
        self.current_level = 1
        self.show_death_screen = False
        self.show_levelup_screen = False
        self.levelup_rewards = []
        
        # 3D rendering
        self.render_3d = False
        self.renderer_3d = Renderer3D(stdscr)
        
        # Magic system
        self.magic_system = MagicSystem()
        self.spell_targeting = False
        self.targeting_spell = None
        self.show_spells = False
        
        # Boss system
        self.boss_system = BossSystem()
        self.show_victory = False
        
        # Godmode
        self.godmode = False
        
        if load_game and os.path.exists('savegame.json'):
            success, message = SaveLoadSystem.load_game(self)
            if success:
                self.add_message(message)
            else:
                self.add_message(message)
                self.start_new_game()
        else:
            self.start_new_game()
        
        # Setup Windows compatibility
        WindowsCompatibility.setup_windows_terminal()
        
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(100)  # 100ms timeout
        
        # Initialize colors
        self.setup_colors()
    
    def start_new_game(self):
        self.dungeon = Dungeon(level=self.current_level)
        self.dungeon.generate()
        
    def setup_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            
            # Define color pairs
            curses.init_pair(1, curses.COLOR_WHITE, -1)    # Default/Walls
            curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Player
            curses.init_pair(3, curses.COLOR_RED, -1)      # Monsters
            curses.init_pair(4, curses.COLOR_GREEN, -1)    # Items/Potions
            curses.init_pair(5, curses.COLOR_CYAN, -1)     # Weapons
            curses.init_pair(6, curses.COLOR_YELLOW, -1)   # Gold
            curses.init_pair(7, curses.COLOR_BLUE, -1)     # Floor
            curses.init_pair(8, curses.COLOR_MAGENTA, -1)  # UI text
            curses.init_pair(9, curses.COLOR_WHITE, -1)    # Stairs
            curses.init_pair(10, curses.COLOR_MAGENTA, -1) # Shopkeeper
            curses.init_pair(11, curses.COLOR_MAGENTA, -1) # Spellbooks
            curses.init_pair(12, curses.COLOR_RED, -1)     # Boss - red and bold
    
    def get_color_pair(self, entity_type=None, cell_type=None):
        if not curses.has_colors():
            return 0
        
        if entity_type:
            if entity_type == EntityType.PLAYER:
                return curses.color_pair(2)
            elif entity_type in [EntityType.GOBLIN, EntityType.ORC]:
                return curses.color_pair(3)
            elif entity_type == EntityType.POTION:
                return curses.color_pair(4)
            elif entity_type == EntityType.WEAPON:
                return curses.color_pair(5)
            elif entity_type == EntityType.SHIELD:
                return curses.color_pair(5)  # Same color as weapons for now
            elif entity_type == EntityType.GOLD:
                return curses.color_pair(6)
            elif entity_type == EntityType.SPELLBOOK:
                return curses.color_pair(11)  # Purple for spellbooks
            elif entity_type == EntityType.BOSS:
                return curses.color_pair(12) | curses.A_BOLD  # Red and bold for boss
        
        if cell_type:
            if cell_type == CellType.FLOOR:
                return curses.color_pair(7)
            elif cell_type == CellType.WALL:
                return curses.color_pair(1)
            elif cell_type == CellType.STAIRS_DOWN:
                return curses.color_pair(9)
        
        if entity_type == EntityType.SHOPKEEPER:
            return curses.color_pair(10)
        
        return curses.color_pair(1)  # Default
    
    def add_message(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > 5:
            self.messages.pop(0)
    
    def draw(self):
        if self.render_3d and self.dungeon.player and not self.show_inventory and not self.show_spells and not self.in_shop and not self.show_death_screen and not self.show_levelup_screen:
            # 3D rendering mode - player is at center of their tile
            player = self.dungeon.player
            self.renderer_3d.render_scene(self, float(player.pos.x) + 0.5, float(player.pos.y) + 0.5, player.angle)
            return
        
        # Original 2D rendering for menus and inventory
        self.stdscr.clear()
        
        # Draw dungeon
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                try:
                    char = self.dungeon.grid[y][x].value
                    # Use Windows-safe characters
                    safe_char = WindowsCompatibility.get_safe_char(char)
                    color = self.get_color_pair(cell_type=self.dungeon.grid[y][x])
                    self.stdscr.addch(y, x, safe_char, color)
                except curses.error:
                    pass
        
        # Draw items
        for item_pos, item in self.dungeon.items:
            try:
                char = WindowsCompatibility.get_safe_char(item.type.value)
                color = self.get_color_pair(entity_type=item.type)
                self.stdscr.addch(item_pos.y, item_pos.x, char, color)
            except curses.error:
                pass
        
        # Draw entities
        for entity in self.dungeon.entities:
            if entity.hp > 0:
                try:
                    char = WindowsCompatibility.get_safe_char(entity.type.value)
                    color = self.get_color_pair(entity_type=entity.type)
                    self.stdscr.addch(entity.pos.y, entity.pos.x, char, color)
                except curses.error:
                    pass
        
        if self.show_victory:
            self.draw_victory_screen()
        elif self.show_death_screen:
            self.draw_death_screen()
        elif self.show_levelup_screen:
            self.draw_levelup_screen()
        elif self.in_shop:
            self.draw_shop()
        elif self.show_spells:
            self.draw_spell_screen()
        elif self.show_inventory:
            self.draw_inventory()
        else:
            # Draw UI
            ui_y = self.dungeon.height + 1
            try:
                player = self.dungeon.player
                ui_color = self.get_color_pair() if curses.has_colors() else 0
                
                if player:
                    # HP display with color coding
                    hp_color = curses.color_pair(3) if player.hp < player.max_hp * 0.3 else ui_color
                    self.stdscr.addstr(ui_y, 0, f"HP: {player.hp}/{player.max_hp}", hp_color)
                    
                    # Mana display with color coding
                    mana_color = curses.color_pair(11) if curses.has_colors() else ui_color
                    self.stdscr.addstr(ui_y + 1, 0, f"MP: {player.mana}/{player.max_mana}", mana_color)
                    
                    attack_total = player.attack + (player.weapon.attack_bonus if player.weapon else 0)
                    defense_total = player.defense + (player.weapon.defense_bonus if player.weapon else 0) + (player.shield.defense_bonus if player.shield else 0)
                    self.stdscr.addstr(ui_y + 1, 20, f"Attack: {attack_total}", ui_color)
                    self.stdscr.addstr(ui_y + 1, 35, f"Defense: {defense_total}", ui_color)
                    
                    # Gold with color
                    gold_color = curses.color_pair(6) if curses.has_colors() else 0
                    self.stdscr.addstr(ui_y, 50, f"Gold: {player.gold}", gold_color)
                    
                    # Character level and XP
                    xp_for_next = LevelingSystem.xp_for_next_level(player.level)
                    xp_progress = LevelingSystem.get_xp_progress(player.xp, player.level)
                    
                    if self.godmode:
                        # Show godmode instead of level info
                        godmode_color = curses.color_pair(6) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
                        self.stdscr.addstr(ui_y, 65, "GODMODE", godmode_color)
                        self.stdscr.addstr(ui_y + 1, 65, f"Lv: {player.level}", ui_color)
                    else:
                        self.stdscr.addstr(ui_y, 65, f"Char Lv: {player.level}", ui_color)
                        self.stdscr.addstr(ui_y + 1, 65, f"XP: {xp_progress}/{xp_for_next}", ui_color)
                    
                    # Dungeon level
                    self.stdscr.addstr(ui_y + 1, 50, f"Floor: {self.current_level}", ui_color)
                    
                    # Equipment display
                    equipment_line = 0
                    if player.weapon:
                        weapon_color = curses.color_pair(5) if curses.has_colors() else 0
                        self.stdscr.addstr(ui_y + 1 + equipment_line, 0, f"Weapon: {player.weapon.name}", weapon_color)
                        equipment_line += 1
                    
                    if player.shield:
                        if player.shield.type == EntityType.SPELLBOOK:
                            spellbook_color = curses.color_pair(11) if curses.has_colors() else 0
                            self.stdscr.addstr(ui_y + 1 + equipment_line, 0, f"Spellbook: {player.shield.name} (+{player.shield.magic_bonus})", spellbook_color)
                        else:
                            shield_color = curses.color_pair(5) if curses.has_colors() else 0
                            self.stdscr.addstr(ui_y + 1 + equipment_line, 0, f"Shield: {player.shield.name} (+{player.shield.defense_bonus})", shield_color)
                        equipment_line += 1
                
                # Draw messages
                equipment_lines = 0
                if player and player.weapon:
                    equipment_lines += 1
                if player and player.shield:
                    equipment_lines += 1
                
                msg_start = ui_y + 2 + equipment_lines
                for i, msg in enumerate(self.messages):
                    self.stdscr.addstr(msg_start + i, 0, msg, ui_color)
                
                # Instructions
                if self.render_3d:
                    self.stdscr.addstr(ui_y + 8, 0, "3D: Arrows turn, WASD move, I: inventory, M: spells, F: cast, G: godmode, 3: toggle 2D/3D, S: save, Q: quit", ui_color)
                else:
                    self.stdscr.addstr(ui_y + 8, 0, "Move: wasd/hjkl/arrows, Inventory: i, M: spells, F: cast, G: godmode, 3: toggle 2D/3D, Save: S, Quit: q", ui_color)
                
            except curses.error:
                pass
        
        self.stdscr.refresh()
    
    def handle_input(self):
        key = self.stdscr.getch()
        
        # Handle victory screen input first
        if self.show_victory:
            return self.handle_victory_screen_input(key)
        
        # Handle death screen input
        if self.show_death_screen:
            return self.handle_death_screen_input(key)
        
        # Handle level up screen
        if self.show_levelup_screen:
            return self.handle_levelup_input(key)
        
        # Handle shop input (before global quit)
        if self.in_shop:
            return self.handle_shop_input(key)
        
        # Global quit only when not in special screens
        if key == ord('q'):
            return False
        
        if key == ord('S'):  # Capital S for save
            success, message = SaveLoadSystem.save_game(self)
            self.add_message(message)
            return True
        
        if key == ord('i'):
            if not self.in_shop:
                self.show_inventory = not self.show_inventory
            return True
        
        if key == ord('3'):  # Toggle 3D mode
            self.render_3d = not self.render_3d
            self.add_message(f"3D mode: {'ON' if self.render_3d else 'OFF'}")
            return True
        
        if key == ord('f') or key == ord('F'):  # Cast spell
            return self.handle_spell_casting()
        
        if key == ord('m') or key == ord('M'):  # View spells
            if not self.in_shop:
                self.show_spells = not self.show_spells
            return True
        
        if key == ord('g') or key == ord('G'):  # Toggle godmode
            self.godmode = not self.godmode
            status = "ON" if self.godmode else "OFF"
            self.add_message(f"Godmode: {status}")
            if self.godmode and self.dungeon.player:
                # Restore full health and mana when enabling godmode
                player = self.dungeon.player
                player.hp = player.max_hp
                player.mana = player.max_mana
                self.add_message("Health and mana restored!")
            return True
        
        if self.spell_targeting:
            return self.handle_spell_targeting(key)
        
        if self.show_spells:
            return self.handle_spell_screen_input(key)
        
        if self.show_inventory:
            return self.handle_inventory_input(key)
        
        if not self.dungeon.player or self.dungeon.player.hp <= 0:
            return True
        
        # 3D Movement and rotation
        if self.render_3d:
            player = self.dungeon.player
            player_moved = False
            
            # Arrow keys for rotation (90-degree increments, no game state progression)
            if key == curses.KEY_LEFT:
                player.angle -= math.pi / 2  # Rotate left 90 degrees
                # Don't update monsters - just turning
            elif key == curses.KEY_RIGHT:
                player.angle += math.pi / 2  # Rotate right 90 degrees
                # Don't update monsters - just turning
            
            # WASD for movement (progresses game state) - exactly one tile
            elif key == ord('w'):  # Move forward
                dx = int(round(math.cos(player.angle)))
                dy = int(round(math.sin(player.angle)))
                self.move_player(dx, dy)
                player_moved = True
            elif key == ord('s'):  # Move backward
                dx = int(round(-math.cos(player.angle)))
                dy = int(round(-math.sin(player.angle)))
                self.move_player(dx, dy)
                player_moved = True
            elif key == ord('a'):  # Strafe left
                dx = int(round(math.cos(player.angle - math.pi/2)))
                dy = int(round(math.sin(player.angle - math.pi/2)))
                self.move_player(dx, dy)
                player_moved = True
            elif key == ord('d'):  # Strafe right
                dx = int(round(math.cos(player.angle + math.pi/2)))
                dy = int(round(math.sin(player.angle + math.pi/2)))
                self.move_player(dx, dy)
                player_moved = True
            
            # Only update monsters when player actually moves, not when turning
            if player_moved:
                self.update_monsters()
        else:
            # Original 2D movement
            dx, dy = 0, 0
            if key in [ord('w'), ord('k'), curses.KEY_UP]:
                dy = -1
            elif key in [ord('s'), ord('j'), curses.KEY_DOWN]:
                dy = 1
            elif key in [ord('a'), ord('h'), curses.KEY_LEFT]:
                dx = -1
            elif key in [ord('d'), ord('l'), curses.KEY_RIGHT]:
                dx = 1
            
            if dx != 0 or dy != 0:
                self.move_player(dx, dy)
                self.update_monsters()
        
        return True
    
    def move_player_3d(self, dx: float, dy: float):
        """Move player in 3D mode with floating point precision"""
        player = self.dungeon.player
        
        # Calculate new position
        new_x = player.pos.x + dx
        new_y = player.pos.y + dy
        new_pos = Position(int(new_x), int(new_y))
        
        # Check bounds
        if (new_pos.x < 0 or new_pos.x >= self.dungeon.width or 
            new_pos.y < 0 or new_pos.y >= self.dungeon.height):
            return
        
        # Check for walls
        if not self.dungeon.is_walkable(new_pos):
            return
        
        # Check for monsters
        target = self.dungeon.get_entity_at(new_pos)
        if target and target != player and target.hp > 0:
            self.combat(player, target)
            return
        
        # Check for stairs
        if (self.dungeon.stairs_pos and 
            new_pos.x == self.dungeon.stairs_pos.x and 
            new_pos.y == self.dungeon.stairs_pos.y):
            self.next_level()
            return
        
        # Check for items to pick up
        item = self.dungeon.get_item_at(new_pos)
        if item:
            self.pickup_item(item, new_pos)
        
        # Move player
        player.pos = new_pos
    
    def move_player(self, dx: int, dy: int):
        player = self.dungeon.player
        new_pos = Position(player.pos.x + dx, player.pos.y + dy)
        
        # Check for monsters
        target = self.dungeon.get_entity_at(new_pos)
        if target and target != player and target.hp > 0:
            self.combat(player, target)
            return
        
        # Check for stairs
        if (self.dungeon.stairs_pos and 
            new_pos.x == self.dungeon.stairs_pos.x and 
            new_pos.y == self.dungeon.stairs_pos.y):
            self.next_level()
            return
        
        # Check if walkable
        if self.dungeon.is_walkable(new_pos):
            # Check for items to pick up
            item = self.dungeon.get_item_at(new_pos)
            if item:
                self.pickup_item(item, new_pos)
            
            player.pos = new_pos
    
    def combat(self, attacker: Entity, defender: Entity):
        damage = CombatSystem.calculate_damage(attacker, defender, self.godmode)
        
        # Check for godmode protection
        if self.godmode and defender == self.dungeon.player:
            self.add_message(f"{attacker.name} attacks {defender.name} but godmode protects them!")
            return
        
        is_dead = CombatSystem.apply_damage(defender, damage)
        
        self.add_message(f"{attacker.name} attacks {defender.name} for {damage} damage!")
        
        if is_dead:
            self.add_message(f"{defender.name} dies!")
            if defender == self.dungeon.player:
                self.show_death_screen = True
                self.game_over = True
            else:
                # Check if boss was defeated - victory condition!
                if defender.type == EntityType.BOSS:
                    self.add_message(f"You have defeated the mighty {defender.name}!")
                    self.add_message("Victory! You are the champion of the dungeon!")
                    self.show_victory = True
                    self.game_over = True
                
                # Drop gold when monster dies
                if defender.gold > 0:
                    self.dungeon.player.gold += defender.gold
                    self.add_message(f"You gained {defender.gold} gold!")
                
                # Give XP to player
                if defender.xp_value > 0:
                    old_level = self.dungeon.player.level
                    self.dungeon.player.xp += defender.xp_value
                    self.add_message(f"You gained {defender.xp_value} XP!")
                    
                    # Check for level up
                    new_level = LevelingSystem.calculate_level_from_xp(self.dungeon.player.xp)
                    if new_level > old_level:
                        self.dungeon.player.level = new_level
                        self.trigger_level_up()
    
    def update_monsters(self):
        # Regenerate player mana each turn
        player = self.dungeon.player
        if player and player.hp > 0:
            if self.godmode:
                # In godmode, keep health and mana at maximum
                player.hp = player.max_hp
                player.mana = player.max_mana
            elif player.mana < player.max_mana:
                player.mana = min(player.max_mana, player.mana + 1)  # Slow mana regen
            
            # Update magical effects
            effect_messages = self.magic_system.update_effects(player, is_player_in_godmode=self.godmode)
            for msg in effect_messages:
                self.add_message(msg)
        
        # Initialize turn counter for boss abilities
        if not hasattr(self, 'current_turn'):
            self.current_turn = 0
        self.current_turn += 1
        
        for entity in self.dungeon.entities:
            if entity.type in [EntityType.GOBLIN, EntityType.ORC] and entity.hp > 0:
                # Update magical effects on monsters too
                effect_messages = self.magic_system.update_effects(entity, is_player_in_godmode=False)
                for msg in effect_messages:
                    self.add_message(msg)
                
                # Check if monster is frozen
                if not self.magic_system.is_frozen(entity):
                    self.move_monster(entity)
            
            elif entity.type == EntityType.BOSS and entity.hp > 0:
                # Update magical effects on boss
                effect_messages = self.magic_system.update_effects(entity, is_player_in_godmode=False)
                for msg in effect_messages:
                    self.add_message(msg)
                
                # Check if boss is frozen
                if not self.magic_system.is_frozen(entity):
                    self.update_boss(entity)
    
    def move_monster(self, monster: Entity):
        player = self.dungeon.player
        if not player or player.hp <= 0:
            return
        
        # Calculate distance to player
        dx = player.pos.x - monster.pos.x
        dy = player.pos.y - monster.pos.y
        distance = abs(dx) + abs(dy)
        
        if distance <= 5:  # Monster can see player - aggressive behavior
            # Move one step towards player
            move_x = 1 if dx > 0 else -1 if dx < 0 else 0
            move_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            new_pos = Position(monster.pos.x + move_x, monster.pos.y + move_y)
            
            # Check if attacking player
            if new_pos.x == player.pos.x and new_pos.y == player.pos.y:
                self.combat(monster, player)
                return
            
            # Check if can move towards player
            if (self.dungeon.is_walkable(new_pos) and 
                not self.dungeon.get_entity_at(new_pos)):
                monster.pos = new_pos
        else:  # Player not detected - wander randomly
            # 30% chance to move each turn when wandering
            if random.random() < 0.3:
                # Choose a random direction
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                move_x, move_y = random.choice(directions)
                
                new_pos = Position(monster.pos.x + move_x, monster.pos.y + move_y)
                
                # Check if can wander to this position
                if (self.dungeon.is_walkable(new_pos) and 
                    not self.dungeon.get_entity_at(new_pos)):
                    monster.pos = new_pos
    
    def update_boss(self, boss: Entity):
        """Handle boss AI including movement, attacks, and special abilities"""
        player = self.dungeon.player
        if not player or player.hp <= 0:
            return
        
        # Update boss phase based on health
        self.boss_system.update_boss_phase(boss)
        
        # Check if boss should use a special ability
        if self.boss_system.should_use_ability(boss, self.current_turn):
            ability = self.boss_system.choose_boss_ability(boss, self.dungeon, self.current_turn)
            if ability:
                messages = self.boss_system.execute_boss_ability(boss, ability, self.dungeon, self.current_turn)
                for msg in messages:
                    self.add_message(msg)
                return  # Boss used ability instead of moving
        
        # Normal boss movement towards player
        dx = player.pos.x - boss.pos.x
        dy = player.pos.y - boss.pos.y
        distance = max(abs(dx), abs(dy))
        
        if distance <= 8:  # Boss can see player - move towards them
            # Move one step towards player (diagonal movement allowed)
            move_x = 1 if dx > 0 else -1 if dx < 0 else 0
            move_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            new_pos = Position(boss.pos.x + move_x, boss.pos.y + move_y)
            
            # Check if attacking player
            if new_pos.x == player.pos.x and new_pos.y == player.pos.y:
                # Boss attacks are more powerful
                self.boss_combat(boss, player)
                return
            
            # Check if can move towards player
            if (self.dungeon.is_walkable(new_pos) and 
                not self.dungeon.get_entity_at(new_pos)):
                boss.pos = new_pos
    
    def boss_combat(self, boss: Entity, player: Entity):
        """Handle boss combat with special mechanics"""
        damage = CombatSystem.calculate_damage(boss, player, self.godmode)
        
        # Bosses hit harder
        damage = int(damage * 1.5)
        
        # Check for godmode protection
        if self.godmode and player == self.dungeon.player:
            self.add_message(f"{boss.name} unleashes a devastating attack but godmode protects you!")
            return
        
        is_dead = CombatSystem.apply_damage(player, damage)
        
        self.add_message(f"{boss.name} unleashes a devastating attack on {player.name} for {damage} damage!")
        
        if is_dead:
            self.add_message(f"{player.name} is defeated by the {boss.name}!")
            self.show_death_screen = True
            self.game_over = True
    
    def pickup_item(self, item: Item, pos: Position):
        player = self.dungeon.player
        
        if item.type == EntityType.GOLD:
            player.gold += item.value
            self.add_message(f"You picked up {item.value} gold!")
        elif item.type == EntityType.POTION:
            if len(player.inventory) < 10:
                player.inventory.append(item)
                self.add_message(f"You picked up a {item.name}!")
            else:
                self.add_message("Your inventory is full!")
                return
        elif item.type in [EntityType.WEAPON, EntityType.SHIELD, EntityType.SPELLBOOK]:
            if len(player.inventory) < 10:
                player.inventory.append(item)
                self.add_message(f"You picked up a {item.name}!")
            else:
                self.add_message("Your inventory is full!")
                return
        
        self.dungeon.remove_item_at(pos)
    
    def draw_inventory(self):
        self.stdscr.clear()
        try:
            # Use colors for inventory
            title_color = curses.color_pair(8) if curses.has_colors() else 0
            gold_color = curses.color_pair(6) if curses.has_colors() else 0
            weapon_color = curses.color_pair(5) if curses.has_colors() else 0
            potion_color = curses.color_pair(4) if curses.has_colors() else 0
            default_color = curses.color_pair(1) if curses.has_colors() else 0
            
            self.stdscr.addstr(0, 0, "=== INVENTORY ===", title_color)
            self.stdscr.addstr(1, 0, f"Gold: {self.dungeon.player.gold}", gold_color)
            
            line = 3
            if self.dungeon.player.weapon:
                if self.dungeon.player.weapon.defense_bonus > 0:
                    self.stdscr.addstr(line, 0, f"Weapon: {self.dungeon.player.weapon.name} (+{self.dungeon.player.weapon.defense_bonus} defense)", weapon_color)
                else:
                    self.stdscr.addstr(line, 0, f"Weapon: {self.dungeon.player.weapon.name} (+{self.dungeon.player.weapon.attack_bonus} attack)", weapon_color)
                line += 1
            
            if self.dungeon.player.shield:
                if self.dungeon.player.shield.type == EntityType.SPELLBOOK:
                    spellbook_color = curses.color_pair(11) if curses.has_colors() else weapon_color
                    self.stdscr.addstr(line, 0, f"Spellbook: {self.dungeon.player.shield.name} (+{self.dungeon.player.shield.magic_bonus} magic)", spellbook_color)
                else:
                    self.stdscr.addstr(line, 0, f"Shield: {self.dungeon.player.shield.name} (+{self.dungeon.player.shield.defense_bonus} defense)", weapon_color)
                line += 1
            
            self.stdscr.addstr(line + 1, 0, "Items:", title_color)
            for i, item in enumerate(self.dungeon.player.inventory):
                prefix = f"{i+1}. "
                if item.type == EntityType.WEAPON:
                    if item.defense_bonus > 0:
                        desc = f"{item.name} (+{item.defense_bonus} defense) - Press {i+1} to equip"
                    else:
                        desc = f"{item.name} (+{item.attack_bonus} attack) - Press {i+1} to equip"
                    color = weapon_color
                elif item.type == EntityType.SHIELD:
                    desc = f"{item.name} (+{item.defense_bonus} defense) - Press {i+1} to equip"
                    color = weapon_color
                elif item.type == EntityType.SPELLBOOK:
                    desc = f"{item.name} (+{item.magic_bonus} magic) - Press {i+1} to equip"
                    color = curses.color_pair(11) if curses.has_colors() else default_color
                elif item.type == EntityType.POTION:
                    desc = f"{item.name} (heals {item.heal_amount} HP) - Press {i+1} to use"
                    color = potion_color
                else:
                    desc = item.name
                    color = default_color
                
                self.stdscr.addstr(line + 2 + i, 0, prefix + desc, color)
            
            if not self.dungeon.player.inventory:
                self.stdscr.addstr(line + 2, 0, "(Empty)", default_color)
            
            self.stdscr.addstr(18, 0, "Press 'i' to close inventory", title_color)
            
        except curses.error:
            pass
    
    def handle_inventory_input(self, key):
        if key >= ord('1') and key <= ord('9'):
            index = key - ord('1')
            if index < len(self.dungeon.player.inventory):
                item = self.dungeon.player.inventory[index]
                
                if item.type == EntityType.WEAPON:
                    # Equip weapon
                    if self.dungeon.player.weapon:
                        # Put current weapon back in inventory
                        self.dungeon.player.inventory.append(self.dungeon.player.weapon)
                    
                    self.dungeon.player.weapon = item
                    self.dungeon.player.inventory.pop(index)
                    self.add_message(f"You equipped {item.name}!")
                    
                elif item.type == EntityType.SHIELD:
                    # Equip shield
                    if self.dungeon.player.shield:
                        # Put current shield back in inventory
                        self.dungeon.player.inventory.append(self.dungeon.player.shield)
                    
                    self.dungeon.player.shield = item
                    self.dungeon.player.inventory.pop(index)
                    self.add_message(f"You equipped {item.name}!")
                    
                elif item.type == EntityType.POTION:
                    # Use potion
                    old_hp = self.dungeon.player.hp
                    self.dungeon.player.hp = min(self.dungeon.player.max_hp, 
                                               self.dungeon.player.hp + item.heal_amount)
                    healed = self.dungeon.player.hp - old_hp
                    self.dungeon.player.inventory.pop(index)
                    self.add_message(f"You used {item.name} and healed {healed} HP!")
                    
                elif item.type == EntityType.SPELLBOOK:
                    # Equip spellbook in shield slot
                    if self.dungeon.player.shield:
                        # Put current shield/spellbook back in inventory
                        self.dungeon.player.inventory.append(self.dungeon.player.shield)
                    
                    self.dungeon.player.shield = item
                    self.dungeon.player.inventory.pop(index)
                    self.add_message(f"You equipped {item.name}!")
        
        return True
    
    def draw_spell_screen(self):
        """Draw the spell viewing screen"""
        self.stdscr.clear()
        try:
            title_color = curses.color_pair(8) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
            default_color = curses.color_pair(1) if curses.has_colors() else 0
            
            # Title
            self.stdscr.addstr(1, 0, "=== SPELLBOOK ===", title_color)
            
            player = self.dungeon.player
            if not player:
                return
            
            # Mana display
            mana_color = curses.color_pair(11) if curses.has_colors() else default_color
            self.stdscr.addstr(3, 0, f"Mana: {player.mana}/{player.max_mana}", mana_color)
            
            # Equipped spellbook
            if player.shield and player.shield.type == EntityType.SPELLBOOK:
                spellbook_color = curses.color_pair(11) if curses.has_colors() else default_color
                self.stdscr.addstr(4, 0, f"Equipped: {player.shield.name}", spellbook_color)
            
            # Known spells
            line = 6
            self.stdscr.addstr(line, 0, "Known Spells:", title_color)
            line += 1
            
            if player.known_spells:
                for i, spell in enumerate(player.known_spells):
                    spell_color = default_color
                    if player.mana >= spell.mana_cost:
                        spell_color = curses.color_pair(4) if curses.has_colors() else default_color  # Green if castable
                    else:
                        spell_color = curses.color_pair(3) if curses.has_colors() else default_color  # Red if not enough mana
                    
                    spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP)"
                    self.stdscr.addstr(line, 0, spell_text, spell_color)
                    self.stdscr.addstr(line + 1, 4, spell.description, curses.A_DIM)
                    line += 3
            else:
                self.stdscr.addstr(line, 0, "  (No spells learned)", default_color)
                line += 1
            
            # Available spells from equipped spellbook
            spellbook_spells = self.magic_system.get_equipped_spellbook_spells(player)
            if spellbook_spells:
                line += 1
                self.stdscr.addstr(line, 0, "Available from Equipped Spellbook:", title_color)
                line += 1
                
                for spell in spellbook_spells:
                    # Check if already known
                    already_known = any(s.spell_type == spell.spell_type for s in player.known_spells)
                    
                    if already_known:
                        spell_color = curses.A_DIM
                        spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP) - Already Known"
                    else:
                        spell_color = curses.color_pair(6) if curses.has_colors() else default_color  # Gold for available
                        spell_text = f"  {spell.name} (Cost: {spell.mana_cost} MP) - Press L to Learn"
                    
                    self.stdscr.addstr(line, 0, spell_text, spell_color)
                    self.stdscr.addstr(line + 1, 4, spell.description, curses.A_DIM)
                    line += 3
            
            # Instructions
            self.stdscr.addstr(line + 1, 0, "Press 'L' to learn available spells", title_color)
            self.stdscr.addstr(line + 2, 0, "Press 'M' to close spellbook", title_color)
            
        except curses.error:
            pass
    
    def handle_spell_screen_input(self, key):
        """Handle input in the spell screen"""
        if key == ord('l') or key == ord('L'):
            # Learn spell from equipped spellbook
            player = self.dungeon.player
            if player and player.shield and player.shield.type == EntityType.SPELLBOOK:
                success, message = self.magic_system.learn_spell_from_book(player, player.shield)
                self.add_message(message)
        
        return True
    
    def next_level(self):
        self.current_level += 1
        
        # 50% chance of encountering a shop
        if random.random() < 0.5:
            self.enter_shop()
        else:
            self.generate_next_dungeon()
            self.add_message(f"Welcome to level {self.current_level}!")
    
    def enter_shop(self):
        self.in_shop = True
        self.shop = Shop(level=self.current_level)
        self.add_message("You found a mysterious shop!")
    
    def exit_shop(self):
        self.in_shop = False
        self.shop = None
        
        # Generate new dungeon after leaving shop and advance to next level
        self.generate_next_dungeon()
        
        self.add_message(f"Welcome to level {self.current_level}!")
    
    def generate_next_dungeon(self):
        # Store reference to current player
        current_player = self.dungeon.player
        if not current_player:
            self.add_message("Error: No player found!")
            return
        
        # Generate new dungeon with existing player
        new_dungeon = Dungeon(level=self.current_level)
        new_dungeon.player = current_player  # Pass existing player to new dungeon
        new_dungeon.generate()  # This will now position the existing player correctly
        
        self.dungeon = new_dungeon
    
    def draw_shop(self):
        self.stdscr.clear()
        try:
            title_color = curses.color_pair(10) if curses.has_colors() else 0
            gold_color = curses.color_pair(6) if curses.has_colors() else 0
            weapon_color = curses.color_pair(5) if curses.has_colors() else 0
            potion_color = curses.color_pair(4) if curses.has_colors() else 0
            default_color = curses.color_pair(1) if curses.has_colors() else 0
            
            self.stdscr.addstr(0, 0, "=== MYSTICAL SHOP ===", title_color)
            self.stdscr.addstr(1, 0, f"Your Gold: {self.dungeon.player.gold}", gold_color)
            self.stdscr.addstr(2, 0, "Shopkeeper: 'Welcome, traveler! Buy or sell your wares!'", title_color)
            
            self.stdscr.addstr(4, 0, "SHOP INVENTORY (Press number to BUY):", title_color)
            for i, item in enumerate(self.shop.items):
                color = weapon_color if item.type in [EntityType.WEAPON, EntityType.SHIELD] else potion_color
                if item.type == EntityType.WEAPON:
                    if item.defense_bonus > 0:
                        desc = f"{i+1}. {item.name} (+{item.defense_bonus} defense) - {item.value} gold"
                    else:
                        desc = f"{i+1}. {item.name} (+{item.attack_bonus} attack) - {item.value} gold"
                elif item.type == EntityType.SHIELD:
                    desc = f"{i+1}. {item.name} (+{item.defense_bonus} defense) - {item.value} gold"
                else:
                    desc = f"{i+1}. {item.name} (heals {item.heal_amount} HP) - {item.value} gold"
                self.stdscr.addstr(5 + i, 0, desc, color)
            
            self.stdscr.addstr(12, 0, "YOUR INVENTORY (Press Shift+number to SELL):", title_color)
            for i, item in enumerate(self.dungeon.player.inventory):
                if i >= 9:  # Only show first 9 items
                    break
                sell_price = max(1, item.value // 2)  # Sell for half price
                color = weapon_color if item.type in [EntityType.WEAPON, EntityType.SHIELD] else potion_color
                if item.type == EntityType.WEAPON:
                    if item.defense_bonus > 0:
                        desc = f"Shift+{i+1}. {item.name} (+{item.defense_bonus} defense) - Sell for {sell_price} gold"
                    else:
                        desc = f"Shift+{i+1}. {item.name} (+{item.attack_bonus} attack) - Sell for {sell_price} gold"
                elif item.type == EntityType.SHIELD:
                    desc = f"Shift+{i+1}. {item.name} (+{item.defense_bonus} defense) - Sell for {sell_price} gold"
                else:
                    desc = f"Shift+{i+1}. {item.name} (heals {item.heal_amount} HP) - Sell for {sell_price} gold"
                self.stdscr.addstr(13 + i, 0, desc, color)
            
            self.stdscr.addstr(23, 0, "Press 'e' to exit shop", title_color)
            
        except curses.error:
            pass
    
    def handle_spell_casting(self):
        """Handle spell casting - show spell selection menu"""
        if not self.dungeon.player or self.dungeon.player.hp <= 0:
            return True
        
        player = self.dungeon.player
        available_spells = self.magic_system.get_available_spells(player)
        
        if not available_spells:
            self.add_message("You don't know any spells!")
            return True
        
        self.stdscr.clear()
        
        try:
            title = "Cast Spell (ESC to cancel)"
            self.stdscr.addstr(1, 2, title, curses.A_BOLD)
            
            mana_info = f"Mana: {player.mana}/{player.max_mana}"
            self.stdscr.addstr(2, 2, mana_info)
            
            y = 4
            for i, (spell, can_cast) in enumerate(available_spells):
                if i >= 9:  # Only show first 9 spells
                    break
                
                color = curses.A_NORMAL if can_cast else curses.A_DIM
                spell_text = f"{i+1}. {spell.name} (Cost: {spell.mana_cost})"
                if not can_cast:
                    spell_text += " - Not enough mana"
                
                self.stdscr.addstr(y, 4, spell_text, color)
                self.stdscr.addstr(y+1, 6, spell.description, curses.A_DIM)
                y += 3
            
            self.stdscr.addstr(y+1, 2, "Select spell (1-9) or ESC to cancel")
            self.stdscr.refresh()
            
            # Wait for input
            key = self.stdscr.getch()
            
            if key == 27:  # ESC
                return True
            
            if key >= ord('1') and key <= ord('9'):
                spell_index = key - ord('1')
                if spell_index < len(available_spells):
                    spell, can_cast = available_spells[spell_index]
                    if can_cast:
                        return self.initiate_spell_casting(spell)
                    else:
                        self.add_message("Not enough mana to cast that spell.")
            
        except curses.error:
            pass
        
        return True
    
    def initiate_spell_casting(self, spell):
        """Start the spell casting process - may require targeting"""
        player = self.dungeon.player
        
        # Spells that don't need targeting
        if spell.spell_type.value in ['heal', 'shield']:
            success, message = self.magic_system.cast_spell(player, spell, self.dungeon, godmode=self.godmode)
            self.add_message(message)
            if success:
                self.update_monsters()  # End turn after casting
            return True
        
        # Spells that need targeting
        self.spell_targeting = True
        self.targeting_spell = spell
        self.add_message(f"Select target for {spell.name} (Arrow keys to aim, ENTER to cast, ESC to cancel)")
        return True
    
    def handle_spell_targeting(self, key):
        """Handle targeting mode for spells"""
        player = self.dungeon.player
        
        if key == 27:  # ESC - cancel targeting
            self.spell_targeting = False
            self.targeting_spell = None
            self.add_message("Spell casting cancelled.")
            return True
        
        if key == ord('\n') or key == ord('\r') or key == 10:  # ENTER - cast spell
            # Calculate target position based on player facing direction
            if self.render_3d:
                # In 3D mode, cast in facing direction
                target_x = player.pos.x + int(round(math.cos(player.angle)))
                target_y = player.pos.y + int(round(math.sin(player.angle)))
            else:
                # In 2D mode, default to 1 tile ahead (facing down)
                target_x = player.pos.x
                target_y = player.pos.y + 1
            
            target_pos = Position(target_x, target_y)
            
            success, message = self.magic_system.cast_spell(player, self.targeting_spell, self.dungeon, target_pos, godmode=self.godmode)
            self.add_message(message)
            
            self.spell_targeting = False
            self.targeting_spell = None
            
            if success:
                self.update_monsters()  # End turn after casting
            
            return True
        
        # Arrow keys for targeting in 2D mode (in 3D mode, just use facing direction)
        if not self.render_3d:
            # TODO: Implement cursor-based targeting for 2D mode
            pass
        
        return True
    
    def handle_shop_input(self, key):
        if key == ord('e') or key == ord('E'):  # Use 'e' to exit shop
            self.exit_shop()
            return True
        
        # Handle buying (1-9)
        if key >= ord('1') and key <= ord('9'):
            index = key - ord('1')
            if index < len(self.shop.items):
                item = self.shop.items[index]
                if self.dungeon.player.gold >= item.value:
                    if len(self.dungeon.player.inventory) < 10:
                        self.dungeon.player.gold -= item.value
                        self.dungeon.player.inventory.append(item)
                        self.shop.items.pop(index)  # Remove item from shop
                        self.add_message(f"Bought {item.name} for {item.value} gold!")
                    else:
                        self.add_message("Your inventory is full!")
                else:
                    self.add_message(f"Not enough gold! Need {item.value} gold.")
        
        # Handle selling (Shift+1-9, which are typically ! @ # $ % ^ & * ()
        sell_keys = [ord('!'), ord('@'), ord('#'), ord('$'), ord('%'), ord('^'), ord('&'), ord('*'), ord('(')]
        if key in sell_keys:
            index = sell_keys.index(key)
            if index < len(self.dungeon.player.inventory):
                item = self.dungeon.player.inventory[index]
                sell_price = max(1, item.value // 2)
                self.dungeon.player.gold += sell_price
                self.dungeon.player.inventory.pop(index)
                self.add_message(f"Sold {item.name} for {sell_price} gold!")
        
        return True
    
    def trigger_level_up(self):
        self.add_message(f"LEVEL UP! You are now level {self.dungeon.player.level}!")
        self.show_levelup_screen = True
        self.levelup_rewards = LevelingSystem.generate_levelup_rewards(self)
    
    def apply_vitality_boost(self):
        player = self.dungeon.player
        player.max_hp += 10
        player.hp = player.max_hp  # Full heal
        self.add_message("You feel much more robust! (+10 Max HP, fully healed)")
    
    def apply_attack_boost(self):
        player = self.dungeon.player
        player.attack += 2
        self.add_message("Your combat skills improve! (+2 Attack)")
    
    def apply_defense_boost(self):
        player = self.dungeon.player
        player.defense += 1
        self.add_message("Your skin hardens like iron! (+1 Defense)")
    
    def apply_treasure_boost(self):
        player = self.dungeon.player
        player.gold += 50
        # Could add a luck modifier for future loot here
        self.add_message("You feel luckier! (+50 Gold, better treasure sense)")
    
    def apply_balanced_boost(self):
        player = self.dungeon.player
        player.max_hp += 5
        player.hp = min(player.hp + 5, player.max_hp)  # Heal 5 HP
        player.attack += 1
        self.add_message("You grow stronger in body and mind! (+5 Max HP, +1 Attack)")
    
    def draw_levelup_screen(self):
        self.stdscr.clear()
        try:
            # Calculate center of screen
            height, width = self.stdscr.getmaxyx()
            center_y = height // 2
            center_x = width // 2
            
            # Colors
            level_color = curses.color_pair(6) if curses.has_colors() else 0  # Yellow
            title_color = curses.color_pair(8) if curses.has_colors() else 0  # Magenta
            option_color = curses.color_pair(1) if curses.has_colors() else 0  # White
            
            # Level up message
            level_msg = f"LEVEL UP! You are now level {self.dungeon.player.level}!"
            self.stdscr.addstr(center_y - 8, center_x - len(level_msg) // 2, level_msg, level_color | curses.A_BOLD)
            
            # Instruction
            instruction = "Choose your reward:"
            self.stdscr.addstr(center_y - 6, center_x - len(instruction) // 2, instruction, title_color)
            
            # Reward options
            for i, reward in enumerate(self.levelup_rewards):
                option_text = f"{i+1}) {reward.name}"
                desc_text = f"   {reward.description}"
                
                self.stdscr.addstr(center_y - 4 + i * 2, center_x - 20, option_text, option_color | curses.A_BOLD)
                self.stdscr.addstr(center_y - 3 + i * 2, center_x - 20, desc_text, option_color)
            
            # Bottom instruction
            bottom_instruction = f"Press 1-{len(self.levelup_rewards)} to select your reward"
            self.stdscr.addstr(center_y + 4, center_x - len(bottom_instruction) // 2, bottom_instruction, title_color)
            
        except curses.error:
            pass
    
    def handle_levelup_input(self, key):
        if key >= ord('1') and key <= ord('9'):
            index = key - ord('1')
            if index < len(self.levelup_rewards):
                # Apply the selected reward
                reward = self.levelup_rewards[index]
                reward.apply_func()
                
                # Close level up screen
                self.show_levelup_screen = False
                self.levelup_rewards = []
                
                return True
        return True
    
    def draw_death_screen(self):
        self.stdscr.clear()
        try:
            # Calculate center of screen
            height, width = self.stdscr.getmaxyx()
            center_y = height // 2
            center_x = width // 2
            
            # Colors
            death_color = curses.color_pair(3) if curses.has_colors() else 0  # Red
            title_color = curses.color_pair(8) if curses.has_colors() else 0  # Magenta
            option_color = curses.color_pair(1) if curses.has_colors() else 0  # White
            
            # Death message
            death_msg = "YOU HAVE DIED!"
            self.stdscr.addstr(center_y - 6, center_x - len(death_msg) // 2, death_msg, death_color | curses.A_BOLD)
            
            # Game stats
            level_msg = f"You reached level {self.current_level}"
            self.stdscr.addstr(center_y - 4, center_x - len(level_msg) // 2, level_msg, title_color)
            
            if self.dungeon.player:
                gold_msg = f"Final gold: {self.dungeon.player.gold}"
                self.stdscr.addstr(center_y - 3, center_x - len(gold_msg) // 2, gold_msg, title_color)
            
            # Options
            self.stdscr.addstr(center_y - 1, center_x - 10, "What would you like to do?", title_color)
            
            self.stdscr.addstr(center_y + 1, center_x - 12, "1) Restart from scratch", option_color)
            self.stdscr.addstr(center_y + 2, center_x - 12, "2) Load saved game", option_color)
            self.stdscr.addstr(center_y + 3, center_x - 12, "3) Quit to desktop", option_color)
            
            # Instructions
            instruction = "Press 1, 2, or 3 to select an option"
            self.stdscr.addstr(center_y + 5, center_x - len(instruction) // 2, instruction, title_color)
            
        except curses.error:
            pass
    
    def draw_victory_screen(self):
        self.stdscr.clear()
        try:
            # Calculate center of screen
            height, width = self.stdscr.getmaxyx()
            center_y = height // 2
            center_x = width // 2
            
            # Colors
            victory_color = curses.color_pair(6) if curses.has_colors() else 0  # Gold/Yellow
            title_color = curses.color_pair(8) if curses.has_colors() else 0  # Magenta
            option_color = curses.color_pair(1) if curses.has_colors() else 0  # White
            
            # Victory message
            victory_msg = "VICTORY!"
            self.stdscr.addstr(center_y - 8, center_x - len(victory_msg) // 2, victory_msg, victory_color | curses.A_BOLD)
            
            champion_msg = "You are the Champion of the Dungeon!"
            self.stdscr.addstr(center_y - 6, center_x - len(champion_msg) // 2, champion_msg, title_color)
            
            # Game stats
            level_msg = f"You conquered {self.current_level} levels of the dungeon"
            self.stdscr.addstr(center_y - 4, center_x - len(level_msg) // 2, level_msg, title_color)
            
            if self.dungeon.player:
                char_level_msg = f"Character level: {self.dungeon.player.level}"
                self.stdscr.addstr(center_y - 3, center_x - len(char_level_msg) // 2, char_level_msg, title_color)
                
                gold_msg = f"Final treasure: {self.dungeon.player.gold} gold"
                self.stdscr.addstr(center_y - 2, center_x - len(gold_msg) // 2, gold_msg, victory_color)
            
            # Options
            self.stdscr.addstr(center_y, center_x - 10, "What would you like to do?", title_color)
            
            self.stdscr.addstr(center_y + 2, center_x - 12, "1) Start a new adventure", option_color)
            self.stdscr.addstr(center_y + 3, center_x - 12, "2) Load saved game", option_color)
            self.stdscr.addstr(center_y + 4, center_x - 12, "3) Quit to desktop", option_color)
            
            # Instructions
            instruction = "Press 1, 2, or 3 to select an option"
            self.stdscr.addstr(center_y + 6, center_x - len(instruction) // 2, instruction, title_color)
            
        except curses.error:
            pass
    
    def handle_victory_screen_input(self, key):
        if key == ord('1'):
            # Start new adventure
            self.restart_game()
            return True
        elif key == ord('2'):
            # Load saved game
            if os.path.exists('savegame.json'):
                success, message = SaveLoadSystem.load_game(self)
                if success:
                    self.show_victory = False
                    self.game_over = False
                    self.add_message(message)
                else:
                    self.add_message(message)
            else:
                self.add_message("No save file found!")
            return True
        elif key == ord('3'):
            # Quit to desktop
            return False
        return True
    
    def handle_death_screen_input(self, key):
        if key == ord('1'):
            # Restart from scratch
            self.restart_game()
            return True
        elif key == ord('2'):
            # Load saved game
            if os.path.exists('savegame.json'):
                success, message = SaveLoadSystem.load_game(self)
                if success:
                    self.show_death_screen = False
                    self.game_over = False
                    self.add_message(message)
                else:
                    self.add_message(message)
            else:
                self.add_message("No save file found!")
                # Stay on death screen
            return True
        elif key == ord('3'):
            # Quit to desktop
            return False
        return True
    
    def restart_game(self):
        # Reset all game state
        self.messages = []
        self.game_over = False
        self.show_inventory = False
        self.show_spells = False
        self.in_shop = False
        self.shop = None
        self.current_level = 1
        self.show_death_screen = False
        self.show_victory = False
        self.show_levelup_screen = False
        self.levelup_rewards = []
        self.godmode = False
        
        # Generate new dungeon
        self.dungeon = Dungeon(level=self.current_level)
        self.dungeon.generate()
        
        self.add_message("New adventure begins!")
    
    def run(self):
        while True:
            self.draw()
            if not self.handle_input():
                break


def main(stdscr):
    try:
        # Check for load argument
        load_game = len(sys.argv) > 1 and sys.argv[1] == '--load'
        
        # Show intro screen only for new games
        if not load_game:
            intro = IntroScreen(stdscr)
            intro.run()
        
        game = Game(stdscr, load_game)
        game.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    except Exception as e:
        # Handle any other errors
        curses.endwin()
        print(f"Error: {e}")
        if platform.system() == "Windows":
            print("\nIf you're having trouble on Windows:")
            print("1. Install windows-curses: pip install windows-curses")
            print("2. Use Windows Terminal or PowerShell for better compatibility")
            print("3. Ensure your terminal supports Unicode characters")
        raise


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("AIRogue - A CLI-based roguelike game")
        print("Cross-platform compatible (Windows, macOS, Linux)")
        print("")
        print("Usage:")
        print("  python main.py          # Start new game")
        print("  python main.py --load   # Load saved game")
        print("  python main.py --help   # Show this help")
        print("")
        print("In-game controls:")
        print("  3D Mode: Arrow keys turn, WASD move")
        print("  2D Mode: wasd/hjkl/arrows move")
        print("  i         - Toggle inventory")
        print("  m/M       - View/cast spells")
        print("  f/F       - Cast spell")
        print("  g/G       - Toggle godmode")
        print("  3         - Toggle 2D/3D mode")
        print("  S         - Save game")
        print("  q         - Quit")
        print("")
        if platform.system() == "Windows":
            print("Windows Setup:")
            print("  pip install windows-curses")
            print("  Use Windows Terminal for best experience")
    else:
        try:
            curses.wrapper(main)
        except Exception as e:
            print(f"Failed to start game: {e}")
            if platform.system() == "Windows":
                print("\nWindows troubleshooting:")
                print("1. Install: pip install windows-curses")
                print("2. Use Windows Terminal instead of Command Prompt")
                print("3. Try: python -m pip install --upgrade windows-curses")
            else:
                print("Make sure you have a compatible terminal that supports curses")
            sys.exit(1)
