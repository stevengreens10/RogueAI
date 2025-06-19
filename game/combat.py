"""
Combat system and related mechanics
"""

import random
from .entities import Entity


class CombatSystem:
    @staticmethod
    def calculate_damage(attacker: Entity, defender: Entity) -> int:
        """Calculate damage from attacker to defender"""
        # Calculate attack bonus from weapon
        attack_bonus = 0
        if attacker.weapon:
            attack_bonus += attacker.weapon.attack_bonus
        
        # Calculate defense bonus from both weapon and shield
        defense_bonus = 0
        if defender.weapon:
            defense_bonus += defender.weapon.defense_bonus
        if defender.shield:
            defense_bonus += defender.shield.defense_bonus
        
        damage = max(1, (attacker.attack + attack_bonus + random.randint(0, 2)) - 
                    (defender.defense + defense_bonus))
        return damage
    
    @staticmethod
    def apply_damage(defender: Entity, damage: int) -> bool:
        """Apply damage to defender. Returns True if defender dies."""
        defender.hp -= damage
        return defender.hp <= 0