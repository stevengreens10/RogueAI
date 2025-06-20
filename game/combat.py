"""
Combat system and related mechanics
"""

import random
from .entities import Entity, EntityType


class CombatSystem:
    @staticmethod
    def calculate_damage(attacker: Entity, defender: Entity, godmode=False) -> int:
        """Calculate damage from attacker to defender"""
        # Godmode protection for player
        if godmode and defender.type == EntityType.PLAYER:
            return 0
        
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
        
        # Check for boss damage reduction
        boss_damage_multiplier = 1.0
        if defender.type == EntityType.BOSS:
            from .boss import BossSystem
            boss_system = BossSystem()
            boss_damage_multiplier = boss_system.get_boss_damage_reduction(defender)
        
        damage = max(1, (attacker.attack + attack_bonus + random.randint(0, 2)) - 
                    (defender.defense + defense_bonus))
        
        # Apply boss damage reduction
        if boss_damage_multiplier < 1.0:
            damage = int(damage * boss_damage_multiplier)
            damage = max(1, damage)  # Always at least 1 damage
        
        return damage
    
    @staticmethod
    def apply_damage(defender: Entity, damage: int) -> bool:
        """Apply damage to defender. Returns True if defender dies."""
        defender.hp -= damage
        return defender.hp <= 0