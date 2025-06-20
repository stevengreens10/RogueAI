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
    SPELLBOOK = '&'
    BOSS = 'B'


class SpellType(Enum):
    FIREBALL = "fireball"
    HEAL = "heal"
    MAGIC_MISSILE = "magic_missile"
    LIGHTNING_BOLT = "lightning_bolt"
    SHIELD = "shield"
    TELEPORT = "teleport"
    FREEZE = "freeze"
    POISON_CLOUD = "poison_cloud"


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
    magic_bonus: int = 0  # For spellbooks - increases spell damage/healing
    spell_type: Optional['SpellType'] = None  # For spellbooks


@dataclass
class Spell:
    spell_type: SpellType
    name: str
    description: str
    mana_cost: int
    damage: int = 0
    heal_amount: int = 0
    range: int = 1
    area_effect: bool = False
    status_effect: Optional[str] = None
    duration: int = 0  # For temporary effects


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
    angle: float = 0.0  # Player rotation angle for 3D rendering
    mana: int = 20  # Magic points
    max_mana: int = 20
    known_spells: List['Spell'] = None  # Spells the entity knows
    active_effects: List[tuple] = None  # (effect_name, duration) tuples
    # Boss-specific attributes
    boss_phase: int = 1  # Boss phases (1, 2, 3)
    special_abilities: List[str] = None  # Boss special abilities
    last_ability_turn: int = 0  # Cooldown tracking
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []
        if self.known_spells is None:
            self.known_spells = []
        if self.active_effects is None:
            self.active_effects = []
        if self.special_abilities is None:
            self.special_abilities = []
    
    @property
    def equipment(self):
        """Backwards compatibility - returns weapon for old code"""
        return self.weapon
    
    @equipment.setter
    def equipment(self, value):
        """Backwards compatibility - sets weapon for old code"""
        self.weapon = value