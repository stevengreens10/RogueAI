"""
Dungeon generation and management
"""

import random
from enum import Enum
from typing import List, Tuple, Optional

from .entities import Entity, EntityType, Item, Position


class CellType(Enum):
    WALL = '#'
    FLOOR = '.'
    DOOR = '+'
    EMPTY = ' '
    STAIRS_DOWN = '▼'


class Dungeon:
    def __init__(self, width: int = 80, height: int = 24, level: int = 1):
        self.width = width
        self.height = height
        self.level = level
        self.grid = [[CellType.WALL for _ in range(width)] for _ in range(height)]
        self.entities: List[Entity] = []
        self.items: List[Tuple[Position, Item]] = []
        self.player: Optional[Entity] = None
        self.stairs_pos: Optional[Position] = None
        
    def generate(self):
        # Simple room generation
        rooms = []
        for _ in range(random.randint(5, 8)):
            w = random.randint(4, 10)
            h = random.randint(3, 6)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            # Carve out room
            for dy in range(h):
                for dx in range(w):
                    self.grid[y + dy][x + dx] = CellType.FLOOR
            
            rooms.append((x, y, w, h))
        
        # Connect rooms with corridors
        for i in range(len(rooms) - 1):
            x1, y1, w1, h1 = rooms[i]
            x2, y2, w2, h2 = rooms[i + 1]
            
            # Connect room centers
            cx1, cy1 = x1 + w1 // 2, y1 + h1 // 2
            cx2, cy2 = x2 + w2 // 2, y2 + h2 // 2
            
            # Horizontal corridor
            for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                self.grid[cy1][x] = CellType.FLOOR
            
            # Vertical corridor
            for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
                self.grid[y][cx2] = CellType.FLOOR
        
        # Place player in first room (only if no player exists yet)
        if rooms and not self.player:
            x, y, w, h = rooms[0]
            self.player = Entity(
                pos=Position(x + w // 2, y + h // 2),
                type=EntityType.PLAYER,
                hp=20,
                max_hp=20,
                attack=3,
                defense=1,
                name="Player",
                inventory=[],
                gold=10,
                xp=0,
                level=1,
                xp_value=0
            )
            self.entities.append(self.player)
        elif rooms and self.player:
            # Player already exists, just move them to the first room
            x, y, w, h = rooms[0]
            self.player.pos = Position(x + w // 2, y + h // 2)
            # Make sure player is in entities list
            if self.player not in self.entities:
                self.entities.append(self.player)
        
        # Place stairs in the last room
        if rooms:
            last_room = rooms[-1]
            x, y, w, h = last_room
            self.stairs_pos = Position(x + w // 2, y + h // 2)
            self.grid[self.stairs_pos.y][self.stairs_pos.x] = CellType.STAIRS_DOWN
        
        # Place monsters and items in other rooms (but not the last room with stairs)
        for room in rooms[1:-1]:  # Skip first room (player) and last room (stairs)
            x, y, w, h = room
            
            # Place monster (70% chance, scaled with level)
            if random.random() < 0.7:
                monster_type = random.choice([EntityType.GOBLIN, EntityType.ORC])
                # Scale monster stats with level
                base_hp = random.randint(3, 8) + (self.level - 1) * 2
                monster_hp = base_hp
                monster = Entity(
                    pos=Position(x + random.randint(1, w-2), y + random.randint(1, h-2)),
                    type=monster_type,
                    hp=monster_hp,
                    max_hp=monster_hp,
                    attack=random.randint(1, 3) + (self.level - 1),
                    defense=random.randint(0, 1) + max(0, (self.level - 1) // 2),
                    name=monster_type.name.title(),
                    inventory=[],
                    gold=random.randint(1, 5) + (self.level - 1) * 2,
                    xp=0,
                    level=1,
                    xp_value=random.randint(5, 15) + (self.level - 1) * 3
                )
                self.entities.append(monster)
            
            # Place items (50% chance)
            if random.random() < 0.5:
                item_pos = Position(x + random.randint(1, w-2), y + random.randint(1, h-2))
                # Make sure item doesn't spawn on entities
                if not self.get_entity_at(item_pos):
                    # Add shields to possible loot at level 2+
                    possible_items = [EntityType.POTION, EntityType.WEAPON, EntityType.GOLD]
                    if self.level >= 2:
                        possible_items.append(EntityType.SHIELD)
                    
                    item_type = random.choice(possible_items)
                    if item_type == EntityType.POTION:
                        heal_amount = random.randint(5, 15) + (self.level - 1) * 3
                        item = Item("Health Potion", item_type, value=10 + (self.level - 1) * 5, heal_amount=heal_amount)
                    elif item_type == EntityType.WEAPON:
                        weapons = [("Dagger", 2), ("Sword", 4), ("Axe", 6), ("Mace", 8)]
                        weapon_name, base_attack = random.choice(weapons)
                        attack_bonus = base_attack + (self.level - 1)
                        item = Item(weapon_name, item_type, value=attack_bonus * 5, attack_bonus=attack_bonus)
                    elif item_type == EntityType.SHIELD:
                        shields = [("Buckler", 1), ("Shield", 2), ("Large Shield", 3)]
                        shield_name, base_defense = random.choice(shields)
                        defense_bonus = base_defense + max(0, (self.level - 2))
                        item = Item(shield_name, item_type, value=defense_bonus * 7, defense_bonus=defense_bonus)
                    else:  # GOLD
                        gold_amount = random.randint(3, 15) + (self.level - 1) * 5
                        item = Item("Gold Coins", item_type, value=gold_amount)
                    
                    self.items.append((item_pos, item))
    
    def get_cell(self, pos: Position) -> CellType:
        if 0 <= pos.x < self.width and 0 <= pos.y < self.height:
            return self.grid[pos.y][pos.x]
        return CellType.WALL
    
    def is_walkable(self, pos: Position) -> bool:
        return self.get_cell(pos) == CellType.FLOOR
    
    def get_entity_at(self, pos: Position) -> Optional[Entity]:
        for entity in self.entities:
            if entity.pos.x == pos.x and entity.pos.y == pos.y:
                return entity
        return None
    
    def get_item_at(self, pos: Position) -> Optional[Item]:
        for item_pos, item in self.items:
            if item_pos.x == pos.x and item_pos.y == pos.y:
                return item
        return None
    
    def remove_item_at(self, pos: Position):
        self.items = [(item_pos, item) for item_pos, item in self.items 
                      if not (item_pos.x == pos.x and item_pos.y == pos.y)]