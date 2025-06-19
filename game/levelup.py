"""
Character leveling and reward system
"""

from .entities import Entity


class LevelUpReward:
    def __init__(self, name: str, description: str, apply_func):
        self.name = name
        self.description = description
        self.apply_func = apply_func


class LevelingSystem:
    @staticmethod
    def xp_for_next_level(current_level: int) -> int:
        """Calculate XP needed for next level"""
        if current_level == 1:
            return 50  # Level 1 to 2: only 50 XP
        else:
            return int(50 + (current_level - 1) * 25)  # Level 2: 75, Level 3: 100, etc.
    
    @staticmethod
    def get_xp_progress(total_xp: int, current_level: int) -> int:
        """Calculate how much XP the player has towards their next level"""
        xp_spent = 0
        for level in range(1, current_level):
            xp_spent += LevelingSystem.xp_for_next_level(level)
        return total_xp - xp_spent
    
    @staticmethod
    def calculate_level_from_xp(total_xp: int) -> int:
        """Calculate what level a player should be based on total XP"""
        level = 1
        xp_spent = 0
        while True:
            xp_for_level = LevelingSystem.xp_for_next_level(level)
            if total_xp >= xp_spent + xp_for_level:
                xp_spent += xp_for_level
                level += 1
            else:
                break
        return level
    
    @staticmethod
    def generate_levelup_rewards(game) -> list:
        """Generate 3 random level-up reward options"""
        all_rewards = [
            LevelUpReward(
                "Vitality Boost",
                "+10 Max HP and fully heal",
                lambda: game.apply_vitality_boost()
            ),
            LevelUpReward(
                "Warrior Training",
                "+2 Attack damage",
                lambda: game.apply_attack_boost()
            ),
            LevelUpReward(
                "Iron Skin",
                "+1 Defense",
                lambda: game.apply_defense_boost()
            ),
            LevelUpReward(
                "Treasure Hunter",
                "+50 Gold and better loot luck",
                lambda: game.apply_treasure_boost()
            ),
            LevelUpReward(
                "Battle Hardened",
                "+5 Max HP and +1 Attack",
                lambda: game.apply_balanced_boost()
            )
        ]
        
        import random
        return random.sample(all_rewards, min(3, len(all_rewards)))