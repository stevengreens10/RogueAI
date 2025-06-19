"""
Game entities: Items, Entities, and related data structures
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class EntityType(Enum):
    PLAYER = '@'
    GOBLIN = 'g'
    ORC = 'o'
    POTION = '!'
    WEAPON = ')'
    SHIELD = ']'
    GOLD = '$'
    SHOPKEEPER = 'S'


@dataclass
class Position:
    x: int
    y: int
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)


@dataclass
class Item:
    name: str
    type: EntityType
    value: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    heal_amount: int = 0


@dataclass
class Entity:
    pos: Position
    type: EntityType
    hp: int = 10
    max_hp: int = 10
    attack: int = 1
    defense: int = 0
    name: str = ""
    inventory: List['Item'] = None
    weapon: Optional['Item'] = None
    shield: Optional['Item'] = None
    gold: int = 0
    xp: int = 0
    level: int = 1
    xp_value: int = 0  # XP this entity gives when killed
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []
    
    @property
    def equipment(self):
        """Backwards compatibility - returns weapon for old code"""
        return self.weapon
    
    @equipment.setter
    def equipment(self, value):
        """Backwards compatibility - sets weapon for old code"""
        self.weapon = value