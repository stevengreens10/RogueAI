#!/usr/bin/env python3
"""
AIRogue - Windowed Edition
A windowed roguelike game using pygame instead of curses
Cross-platform compatible (Windows, macOS, Linux)
"""

import random
import sys
import os
import math
import platform
import pygame

from game.entities import Entity, EntityType, Item, Position
from game.dungeon import Dungeon, CellType
from game.shop import Shop
from game.combat import CombatSystem
from game.levelup import LevelingSystem, LevelUpReward
from game.save_load import SaveLoadSystem
from game.intro import IntroScreen
from game.window_renderer import WindowRenderer
from game.magic import MagicSystem
from game.boss import BossSystem


class GameWindow:
    """Main game class for windowed version"""
    
    def __init__(self, load_game=False):
        # Initialize pygame and renderer
        self.renderer = WindowRenderer()
        
        # Game state
        self.messages = []
        self.game_over = False
        self.show_inventory = False
        self.in_shop = False
        self.shop = None
        self.current_level = 1
        self.show_death_screen = False
        self.show_levelup_screen = False
        self.levelup_rewards = []
        self.show_victory = False
        self.godmode = False
        self.running = True
        
        # 3D rendering
        self.render_3d = False
        
        # Magic system
        self.magic_system = MagicSystem()
        self.spell_targeting = False
        self.targeting_spell = None
        self.show_spells = False
        
        # Boss system
        self.boss_system = BossSystem()
        
        # Spell casting UI state
        self.show_spell_casting = False
        self.available_spells = []
        
        if load_game and os.path.exists('savegame.json'):
            success, message = SaveLoadSystem.load_game(self)
            if success:
                self.add_message(message)
            else:
                self.add_message(message)
                self.start_new_game()
        else:
            self.start_new_game()
    
    def start_new_game(self):
        """Start a new game"""
        self.dungeon = Dungeon(level=self.current_level)
        self.dungeon.generate()
    
    def add_message(self, msg: str):
        """Add a message to the message log"""
        self.messages.append(msg)
        if len(self.messages) > 5:
            self.messages.pop(0)
    
    def handle_commands(self, commands):
        """Handle a list of commands from input"""
        for command in commands:
            # Handle different game states
            if self.show_victory:
                if not self.handle_victory_screen_command(command):
                    return False
            elif self.show_death_screen:
                if not self.handle_death_screen_command(command):
                    return False
            elif self.show_levelup_screen:
                if not self.handle_levelup_command(command):
                    return False
            elif self.in_shop:
                if not self.handle_shop_command(command):
                    return False
            elif self.show_spell_casting:
                if not self.handle_spell_casting_command(command):
                    return False
            elif self.spell_targeting:
                if not self.handle_spell_targeting_command(command):
                    return False
            elif self.show_spells:
                if not self.handle_spell_screen_command(command):
                    return False
            elif self.show_inventory:
                if not self.handle_inventory_command(command):
                    return False
            else:
                if not self.handle_game_command(command):
                    return False
        return True
    
    def handle_game_command(self, command):
        """Handle commands during normal gameplay"""
        if command == 'quit':
            return False
        
        elif command == 'save':
            success, message = SaveLoadSystem.save_game(self)
            self.add_message(message)
        
        elif command == 'inventory':
            self.show_inventory = not self.show_inventory
        
        elif command == 'toggle_3d':
            self.render_3d = not self.render_3d
            self.add_message(f"3D mode: {'ON' if self.render_3d else 'OFF'}")
        
        elif command == 'cast_spell':
            return self.initiate_spell_casting()
        
        elif command == 'spells':
            self.show_spells = not self.show_spells
        
        elif command == 'godmode':
            self.godmode = not self.godmode
            status = "ON" if self.godmode else "OFF"
            self.add_message(f"Godmode: {status}")
            if self.godmode and self.dungeon.player:
                player = self.dungeon.player
                player.hp = player.max_hp
                player.mana = player.max_mana
                self.add_message("Health and mana restored!")
        
        elif command.startswith('move_'):
            self.handle_movement_command(command)
        
        return True
    
    def handle_movement_command(self, command):
        """Handle movement commands"""
        if not self.dungeon.player or self.dungeon.player.hp <= 0:
            return
        
        # 3D Movement and rotation
        if self.render_3d:
            player = self.dungeon.player
            player_moved = False
            
            # Arrow keys for rotation (90-degree increments)
            if command == 'move_left':
                player.angle -= math.pi / 2  # Rotate left 90 degrees
            elif command == 'move_right':
                player.angle += math.pi / 2  # Rotate right 90 degrees
            
            # WASD for movement (progresses game state)
            elif command == 'move_up':  # W - Move forward
                dx = int(round(math.cos(player.angle)))
                dy = int(round(math.sin(player.angle)))
                self.move_player(dx, dy)
                player_moved = True
            elif command == 'move_down':  # S - Move backward
                dx = int(round(-math.cos(player.angle)))
                dy = int(round(-math.sin(player.angle)))
                self.move_player(dx, dy)
                player_moved = True
            # Note: In windowed version, we can implement strafe with A/D if needed
            
            # Only update monsters when player actually moves
            if player_moved:
                self.update_monsters()
        else:
            # Original 2D movement
            dx, dy = 0, 0
            if command == 'move_up':
                dy = -1
            elif command == 'move_down':
                dy = 1
            elif command == 'move_left':
                dx = -1
            elif command == 'move_right':
                dx = 1
            
            if dx != 0 or dy != 0:
                self.move_player(dx, dy)
                self.update_monsters()
    
    def move_player(self, dx: int, dy: int):
        """Move the player"""
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
        """Handle combat between entities"""
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
        """Update monster AI and effects"""
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
        """Move a monster using AI"""
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
        """Handle boss AI"""
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
        """Pick up an item"""
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
    
    def next_level(self):
        """Progress to the next level"""
        self.current_level += 1
        
        # 50% chance of encountering a shop
        if random.random() < 0.5:
            self.enter_shop()
        else:
            self.generate_next_dungeon()
            self.add_message(f"Welcome to level {self.current_level}!")
    
    def enter_shop(self):
        """Enter a shop"""
        self.in_shop = True
        self.shop = Shop(level=self.current_level)
        self.add_message("You found a mysterious shop!")
    
    def exit_shop(self):
        """Exit the shop"""
        self.in_shop = False
        self.shop = None
        
        # Generate new dungeon after leaving shop and advance to next level
        self.generate_next_dungeon()
        
        self.add_message(f"Welcome to level {self.current_level}!")
    
    def generate_next_dungeon(self):
        """Generate the next dungeon level"""
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
    
    # Inventory, shop, spell, and other UI handling methods...
    def handle_inventory_command(self, command):
        """Handle inventory commands"""
        if command == 'inventory':
            self.show_inventory = False
            return True
        
        if command.startswith('num_'):
            index = int(command[-1]) - 1
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
    
    def handle_shop_command(self, command):
        """Handle shop commands"""
        if command == 'exit_shop':
            self.exit_shop()
            return True
        
        # Handle buying (1-9)
        if command.startswith('num_'):
            index = int(command[-1]) - 1
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
        
        # Handle selling (Shift+1-9)
        elif command.startswith('sell_'):
            index = int(command[-1]) - 1
            if index < len(self.dungeon.player.inventory):
                item = self.dungeon.player.inventory[index]
                sell_price = max(1, item.value // 2)
                self.dungeon.player.gold += sell_price
                self.dungeon.player.inventory.pop(index)
                self.add_message(f"Sold {item.name} for {sell_price} gold!")
        
        return True
    
    def handle_spell_screen_command(self, command):
        """Handle spell screen commands"""
        if command in ['spells', 'cancel']:
            self.show_spells = False
        elif command == 'move_right':  # 'l' key for learning spells in spell screen
            # Learn spell from equipped spellbook
            player = self.dungeon.player
            if player and player.shield and player.shield.type == EntityType.SPELLBOOK:
                success, message = self.magic_system.learn_spell_from_book(player, player.shield)
                self.add_message(message)
        
        return True
    
    def initiate_spell_casting(self):
        """Initiate spell casting"""
        if not self.dungeon.player or self.dungeon.player.hp <= 0:
            return True
        
        player = self.dungeon.player
        self.available_spells = self.magic_system.get_available_spells(player)
        
        if not self.available_spells:
            self.add_message("You don't know any spells!")
            return True
        
        self.show_spell_casting = True
        return True
    
    def handle_spell_casting_command(self, command):
        """Handle spell casting menu commands"""
        if command in ['cancel', 'cast_spell']:
            self.show_spell_casting = False
            return True
        
        if command.startswith('num_'):
            spell_index = int(command[-1]) - 1
            if spell_index < len(self.available_spells):
                spell, can_cast = self.available_spells[spell_index]
                if can_cast:
                    self.show_spell_casting = False
                    return self.cast_selected_spell(spell)
                else:
                    self.add_message("Not enough mana to cast that spell.")
        
        return True
    
    def cast_selected_spell(self, spell):
        """Cast a selected spell"""
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
    
    def handle_spell_targeting_command(self, command):
        """Handle spell targeting commands"""
        player = self.dungeon.player
        
        if command == 'cancel':
            self.spell_targeting = False
            self.targeting_spell = None
            self.add_message("Spell casting cancelled.")
            return True
        
        if command == 'confirm':
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
        
        return True
    
    def handle_victory_screen_command(self, command):
        """Handle victory screen commands"""
        if command == 'num_1':
            # Start new adventure
            self.restart_game()
            return True
        elif command == 'num_2':
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
        elif command == 'num_3':
            # Quit to desktop
            return False
        return True
    
    def handle_death_screen_command(self, command):
        """Handle death screen commands"""
        if command == 'num_1':
            # Restart from scratch
            self.restart_game()
            return True
        elif command == 'num_2':
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
            return True
        elif command == 'num_3':
            # Quit to desktop
            return False
        return True
    
    def handle_levelup_command(self, command):
        """Handle level up screen commands"""
        if command.startswith('num_'):
            index = int(command[-1]) - 1
            if index < len(self.levelup_rewards):
                # Apply the selected reward
                reward = self.levelup_rewards[index]
                reward.apply_func()
                
                # Close level up screen
                self.show_levelup_screen = False
                self.levelup_rewards = []
        
        return True
    
    def trigger_level_up(self):
        """Trigger a level up"""
        self.add_message(f"LEVEL UP! You are now level {self.dungeon.player.level}!")
        self.show_levelup_screen = True
        self.levelup_rewards = LevelingSystem.generate_levelup_rewards(self)
    
    def restart_game(self):
        """Restart the game from scratch"""
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
        self.show_spell_casting = False
        self.spell_targeting = False
        self.targeting_spell = None
        
        # Generate new dungeon
        self.dungeon = Dungeon(level=self.current_level)
        self.dungeon.generate()
        
        self.add_message("New adventure begins!")
    
    def draw(self):
        """Draw the current game state"""
        self.renderer.clear_screen()
        
        # Draw different screens based on game state
        if self.show_victory:
            self.renderer.draw_victory_screen(self)
        elif self.show_death_screen:
            self.renderer.draw_death_screen(self)
        elif self.show_levelup_screen:
            self.renderer.draw_levelup_screen(self)
        elif self.in_shop:
            self.renderer.draw_shop_screen(self)
        elif self.show_spells:
            self.renderer.draw_spell_screen(self)
        elif self.show_inventory:
            self.renderer.draw_inventory_screen(self)
        elif self.show_spell_casting:
            self.draw_spell_casting_screen()
        else:
            # Main game view
            if self.render_3d and self.dungeon.player:
                self.renderer.draw_3d_scene(self)
            else:
                self.renderer.draw_2d_ascii(self)
            
            # Always draw UI
            self.renderer.draw_ui(self)
        
        self.renderer.update_display()
    
    def draw_spell_casting_screen(self):
        """Draw the spell casting selection screen"""
        # Similar to inventory but for spells
        self.renderer.clear_screen()
        
        # Background
        pygame.draw.rect(self.renderer.screen, (50, 50, 50), 
                        (50, 50, self.renderer.width - 100, self.renderer.height - 100))
        pygame.draw.rect(self.renderer.screen, (255, 255, 255),
                        (50, 50, self.renderer.width - 100, self.renderer.height - 100), 2)
        
        # Title
        self.renderer.draw_text("Cast Spell (ESC to cancel)", 70, 70, 
                               self.renderer.font_title, (255, 255, 255), bold=True)
        
        player = self.dungeon.player
        mana_info = f"Mana: {player.mana}/{player.max_mana}"
        self.renderer.draw_text(mana_info, 70, 110, self.renderer.font_ui, (0, 255, 255))
        
        y = 150
        for i, (spell, can_cast) in enumerate(self.available_spells):
            if i >= 9:  # Only show first 9 spells
                break
            
            color = (255, 255, 255) if can_cast else (100, 100, 100)
            spell_text = f"{i+1}. {spell.name} (Cost: {spell.mana_cost})"
            if not can_cast:
                spell_text += " - Not enough mana"
            
            self.renderer.draw_text(spell_text, 70, y, self.renderer.font_ui, color)
            self.renderer.draw_text(f"   {spell.description}", 70, y + 20, 
                                   self.renderer.font_ui, (150, 150, 150))
            y += 50
        
        self.renderer.draw_text("Select spell (1-9) or ESC to cancel", 70, y + 20, 
                               self.renderer.font_ui, (255, 255, 255))
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            commands = self.renderer.handle_events()
            if not self.handle_commands(commands):
                break
            
            # Draw everything
            self.draw()
        
        # Clean up
        self.renderer.quit()


def main():
    """Main function"""
    try:
        # Check for load argument
        load_game = len(sys.argv) > 1 and sys.argv[1] == '--load'
        
        # Show intro screen only for new games (could be implemented later)
        # if not load_game:
        #     intro = IntroScreen()
        #     intro.run()
        
        game = GameWindow(load_game)
        game.run()
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    except Exception as e:
        # Handle any other errors
        pygame.quit()
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("AIRogue - Windowed Edition")
        print("A windowed roguelike game using pygame")
        print("Cross-platform compatible (Windows, macOS, Linux)")
        print("")
        print("Usage:")
        print("  python main_windowed.py          # Start new game")
        print("  python main_windowed.py --load   # Load saved game")
        print("  python main_windowed.py --help   # Show this help")
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
        print("Requirements:")
        print("  pip install pygame")
    else:
        main()