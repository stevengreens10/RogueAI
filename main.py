#!/usr/bin/env python3
"""
AIRogue - A CLI-based roguelike game
"""

import curses
import random
import sys
import os
import math

from game.entities import Entity, EntityType, Item, Position
from game.dungeon import Dungeon, CellType
from game.shop import Shop
from game.combat import CombatSystem
from game.levelup import LevelingSystem, LevelUpReward
from game.save_load import SaveLoadSystem
from game.intro import IntroScreen
from game.renderer3d import Renderer3D


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
        
        if load_game and os.path.exists('savegame.json'):
            success, message = SaveLoadSystem.load_game(self)
            if success:
                self.add_message(message)
            else:
                self.add_message(message)
                self.start_new_game()
        else:
            self.start_new_game()
        
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
        if self.render_3d and self.dungeon.player and not self.show_inventory and not self.in_shop and not self.show_death_screen and not self.show_levelup_screen:
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
                    color = self.get_color_pair(cell_type=self.dungeon.grid[y][x])
                    self.stdscr.addch(y, x, char, color)
                except curses.error:
                    pass
        
        # Draw items
        for item_pos, item in self.dungeon.items:
            try:
                color = self.get_color_pair(entity_type=item.type)
                self.stdscr.addch(item_pos.y, item_pos.x, item.type.value, color)
            except curses.error:
                pass
        
        # Draw entities
        for entity in self.dungeon.entities:
            if entity.hp > 0:
                try:
                    color = self.get_color_pair(entity_type=entity.type)
                    self.stdscr.addch(entity.pos.y, entity.pos.x, entity.type.value, color)
                except curses.error:
                    pass
        
        if self.show_death_screen:
            self.draw_death_screen()
        elif self.show_levelup_screen:
            self.draw_levelup_screen()
        elif self.in_shop:
            self.draw_shop()
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
                    
                    attack_total = player.attack + (player.weapon.attack_bonus if player.weapon else 0)
                    defense_total = player.defense + (player.weapon.defense_bonus if player.weapon else 0) + (player.shield.defense_bonus if player.shield else 0)
                    self.stdscr.addstr(ui_y, 20, f"Attack: {attack_total}", ui_color)
                    self.stdscr.addstr(ui_y, 35, f"Defense: {defense_total}", ui_color)
                    
                    # Gold with color
                    gold_color = curses.color_pair(6) if curses.has_colors() else 0
                    self.stdscr.addstr(ui_y, 50, f"Gold: {player.gold}", gold_color)
                    
                    # Character level and XP
                    xp_for_next = LevelingSystem.xp_for_next_level(player.level)
                    xp_progress = LevelingSystem.get_xp_progress(player.xp, player.level)
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
                        shield_color = curses.color_pair(5) if curses.has_colors() else 0
                        self.stdscr.addstr(ui_y + 1 + equipment_line, 0, f"Shield: {player.shield.name}", shield_color)
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
                    self.stdscr.addstr(ui_y + 8, 0, "3D: Arrows turn, WASD move, I: inventory, 3: toggle 2D/3D, S: save, Q: quit", ui_color)
                else:
                    self.stdscr.addstr(ui_y + 8, 0, "Move: wasd/hjkl/arrows, Inventory: i, 3: toggle 2D/3D, Save: S, Quit: q", ui_color)
                
            except curses.error:
                pass
        
        self.stdscr.refresh()
    
    def handle_input(self):
        key = self.stdscr.getch()
        
        # Handle death screen input first
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
        damage = CombatSystem.calculate_damage(attacker, defender)
        is_dead = CombatSystem.apply_damage(defender, damage)
        
        self.add_message(f"{attacker.name} attacks {defender.name} for {damage} damage!")
        
        if is_dead:
            self.add_message(f"{defender.name} dies!")
            if defender == self.dungeon.player:
                self.show_death_screen = True
                self.game_over = True
            else:
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
        for entity in self.dungeon.entities:
            if entity.type in [EntityType.GOBLIN, EntityType.ORC] and entity.hp > 0:
                self.move_monster(entity)
    
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
        elif item.type in [EntityType.WEAPON, EntityType.SHIELD]:
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
        self.in_shop = False
        self.shop = None
        self.current_level = 1
        self.show_death_screen = False
        self.show_levelup_screen = False
        self.levelup_rewards = []
        
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
    # Check for load argument
    load_game = len(sys.argv) > 1 and sys.argv[1] == '--load'
    
    # Show intro screen only for new games
    if not load_game:
        intro = IntroScreen(stdscr)
        intro.run()
    
    game = Game(stdscr, load_game)
    game.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("AIRogue - A CLI-based roguelike game")
        print("Usage:")
        print("  python3 main.py          # Start new game")
        print("  python3 main.py --load   # Load saved game")
        print("  python3 main.py --help   # Show this help")
        print("")
        print("In-game controls:")
        print("  3D Mode: Arrow keys turn, WASD move")
        print("  2D Mode: wasd/hjkl/arrows move")
        print("  i         - Toggle inventory")
        print("  3         - Toggle 2D/3D mode")
        print("  S         - Save game")
        print("  q         - Quit")
    else:
        curses.wrapper(main)
