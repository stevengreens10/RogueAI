"""
Shop system and item generation
"""

import random
from .entities import Item, EntityType


class Shop:
    def __init__(self, level: int = 1):
        self.level = level
        self.items = self.generate_shop_inventory()
    
    def generate_shop_inventory(self):
        items = []
        
        # Generate 2-3 potions of varying quality
        potion_count = random.randint(2, 3)
        for _ in range(potion_count):
            # Choose between two fixed potion tiers
            if self.level >= 3 and random.random() < 0.4:
                # Greater potion - fixed heal amount, variable price
                base_heal = 40  # Fixed healing
                base_value = random.randint(25, 35)  # Variable price
                name = "Greater Health Potion"
            else:
                # Regular potion - fixed heal amount, variable price
                base_heal = 20  # Fixed healing
                base_value = random.randint(12, 18)  # Variable price
                name = "Health Potion"
            
            items.append(Item(name, EntityType.POTION, value=base_value, heal_amount=base_heal))
        
        # Generate 2-4 weapons with level-appropriate power
        weapon_count = random.randint(2, 4)
        weapon_types = [
            ("Dagger", 2), ("Short Sword", 3), ("Sword", 4), 
            ("Battle Axe", 5), ("War Hammer", 6), ("Great Sword", 7),
            ("Enchanted Blade", 8), ("Legendary Weapon", 10)
        ]
        
        for _ in range(weapon_count):
            # Choose weapons appropriate for current level
            min_power = max(2, self.level - 2)
            max_power = min(len(weapon_types), self.level + 3)
            
            # Filter weapons by power level
            available_weapons = [(name, power) for name, power in weapon_types 
                               if min_power <= power <= max_power]
            
            if available_weapons:
                weapon_name, base_attack = random.choice(available_weapons)
                # Add some randomization and level scaling
                attack_bonus = base_attack + random.randint(-1, 2) + (self.level - 1)
                attack_bonus = max(2, attack_bonus)  # Minimum 2 attack
                
                # Price scales moderately with attack power
                value = attack_bonus * random.randint(6, 10) + (self.level - 1) * 5
                
                # Add level prefix for higher level items
                if self.level >= 4 and attack_bonus >= 7:
                    if random.random() < 0.3:
                        weapon_name = f"Masterwork {weapon_name}"
                        attack_bonus += 1
                        value = int(value * 1.2)  # Reduced from 1.3
                elif self.level >= 6 and attack_bonus >= 9:
                    if random.random() < 0.2:
                        weapon_name = f"Legendary {weapon_name}"
                        attack_bonus += 2
                        value = int(value * 1.4)  # Reduced from 1.6
                
                items.append(Item(weapon_name, EntityType.WEAPON, value=value, attack_bonus=attack_bonus))
        
        # Generate 1-2 shields at higher levels
        if self.level >= 2:
            shield_count = random.randint(1, 2) if self.level >= 4 else random.randint(0, 1)
            shield_types = [
                ("Buckler", 1), ("Iron Shield", 2), ("Steel Shield", 3), 
                ("Tower Shield", 4), ("Enchanted Shield", 5), ("Legendary Shield", 6)
            ]
            
            for _ in range(shield_count):
                # Choose shields appropriate for current level
                min_defense = max(1, self.level - 3)
                max_defense = min(len(shield_types), self.level)
                
                # Filter shields by defense level
                available_shields = [(name, defense) for name, defense in shield_types 
                                   if min_defense <= defense <= max_defense]
                
                if available_shields:
                    shield_name, base_defense = random.choice(available_shields)
                    # Add some randomization and level scaling
                    defense_bonus = base_defense + random.randint(0, 1) + max(0, (self.level - 2) // 2)
                    defense_bonus = max(1, defense_bonus)  # Minimum 1 defense
                    
                    # Price scales with defense power
                    value = defense_bonus * random.randint(8, 12) + (self.level - 1) * 3
                    
                    # Add level prefix for higher level items
                    if self.level >= 5 and defense_bonus >= 4:
                        if random.random() < 0.3:
                            shield_name = f"Masterwork {shield_name}"
                            defense_bonus += 1
                            value = int(value * 1.3)
                    elif self.level >= 7 and defense_bonus >= 6:
                        if random.random() < 0.2:
                            shield_name = f"Legendary {shield_name}"
                            defense_bonus += 2
                            value = int(value * 1.5)
                    
                    items.append(Item(shield_name, EntityType.SHIELD, value=value, defense_bonus=defense_bonus))
        
        return items