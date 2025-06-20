"""
Boss system for AIRogue - final boss mechanics and abilities
"""

import random
from game.entities import Entity, EntityType, Position, SpellType
from game.dungeon import CellType


class BossSystem:
    """Handles boss creation, mechanics and special abilities"""
    
    def __init__(self):
        self.boss_names = [
            "Ancient Lich King",
            "Shadow Dragon",
            "Demon Lord Malthazar",
            "The Void Sovereign",
            "Necromancer Supreme"
        ]
        
        self.boss_abilities = {
            "summon_minions": {
                "name": "Summon Minions",
                "description": "Summons 2-3 creatures to fight",
                "cooldown": 5
            },
            "dark_magic": {
                "name": "Dark Magic Blast",
                "description": "Powerful magic attack with area damage",
                "cooldown": 3
            },
            "teleport_attack": {
                "name": "Teleport Strike",
                "description": "Teleports next to player and attacks",
                "cooldown": 4
            },
            "drain_life": {
                "name": "Life Drain",
                "description": "Drains player's health and heals boss",
                "cooldown": 6
            },
            "phase_shift": {
                "name": "Phase Shift",
                "description": "Becomes partially incorporeal, reducing damage",
                "cooldown": 8
            }
        }
    
    def create_boss(self, level):
        """Create a powerful boss entity appropriate for the level"""
        # Boss stats scale significantly with level
        base_hp = 150 + (level * 25)
        base_attack = 15 + (level * 3)
        base_defense = 8 + (level * 2)
        
        boss_name = random.choice(self.boss_names)
        
        # Create boss entity
        boss = Entity(
            pos=Position(0, 0),  # Position will be set when spawned
            type=EntityType.BOSS,
            hp=base_hp,
            max_hp=base_hp,
            attack=base_attack,
            defense=base_defense,
            name=boss_name,
            gold=500 + (level * 100),
            xp_value=1000 + (level * 200),
            level=level,
            mana=100 + (level * 20),
            max_mana=100 + (level * 20),
            boss_phase=1,
            special_abilities=list(self.boss_abilities.keys()),
            last_ability_turn=0
        )
        
        return boss
    
    def should_spawn_boss(self, level):
        """Determine if a boss should spawn at this level"""
        # Boss spawns every 10 levels, or with small chance at deep levels
        if level % 10 == 0:
            return True
        elif level >= 15 and random.random() < 0.1:  # 10% chance at level 15+
            return True
        return False
    
    def get_boss_spawn_position(self, dungeon):
        """Find a good position to spawn the boss"""
        # Try to find a position far from the player
        player_pos = dungeon.player.pos
        best_positions = []
        
        for y in range(1, dungeon.height - 1):
            for x in range(1, dungeon.width - 1):
                if dungeon.grid[y][x] == CellType.FLOOR:
                    # Check if position is empty
                    position_empty = True
                    for entity in dungeon.entities:
                        if entity.pos.x == x and entity.pos.y == y:
                            position_empty = False
                            break
                    
                    if position_empty:
                        # Calculate distance from player
                        distance = max(abs(x - player_pos.x), abs(y - player_pos.y))
                        if distance >= 8:  # Far from player
                            best_positions.append(Position(x, y))
        
        if best_positions:
            return random.choice(best_positions)
        else:
            # Fallback: find any empty floor position
            for y in range(1, dungeon.height - 1):
                for x in range(1, dungeon.width - 1):
                    if dungeon.grid[y][x] == CellType.FLOOR:
                        position_empty = True
                        for entity in dungeon.entities:
                            if entity.pos.x == x and entity.pos.y == y:
                                position_empty = False
                                break
                        if position_empty:
                            return Position(x, y)
        
        return Position(1, 1)  # Last resort
    
    def update_boss_phase(self, boss):
        """Update boss phase based on health percentage"""
        health_percent = boss.hp / boss.max_hp
        
        if health_percent > 0.66:
            boss.boss_phase = 1
        elif health_percent > 0.33:
            boss.boss_phase = 2
        else:
            boss.boss_phase = 3
    
    def should_use_ability(self, boss, current_turn):
        """Determine if boss should use a special ability this turn"""
        # More aggressive in later phases
        base_chance = 0.3 + (boss.boss_phase - 1) * 0.15
        
        # Check if enough turns have passed since last ability
        if current_turn - boss.last_ability_turn < 2:
            return False
        
        return random.random() < base_chance
    
    def choose_boss_ability(self, boss, dungeon, current_turn):
        """Choose which ability the boss should use"""
        available_abilities = []
        
        for ability_name in boss.special_abilities:
            ability = self.boss_abilities[ability_name]
            # Check cooldown
            if current_turn - boss.last_ability_turn >= ability["cooldown"]:
                available_abilities.append(ability_name)
        
        if not available_abilities:
            return None
        
        # Weight abilities based on situation and boss phase
        weights = {}
        player_distance = max(abs(boss.pos.x - dungeon.player.pos.x), 
                            abs(boss.pos.y - dungeon.player.pos.y))
        
        for ability_name in available_abilities:
            if ability_name == "summon_minions":
                # More likely when low on health and few enemies around
                enemy_count = sum(1 for e in dungeon.entities if e.type in [EntityType.GOBLIN, EntityType.ORC])
                weights[ability_name] = (4 - boss.boss_phase) * (3 - min(enemy_count, 3))
            elif ability_name == "teleport_attack":
                # More likely when far from player
                weights[ability_name] = max(1, player_distance - 2)
            elif ability_name == "drain_life":
                # More likely when boss is wounded
                health_percent = boss.hp / boss.max_hp
                weights[ability_name] = (1 - health_percent) * 5
            elif ability_name == "phase_shift":
                # More likely in phase 3
                weights[ability_name] = boss.boss_phase
            else:
                weights[ability_name] = 2
        
        # Choose weighted random ability
        total_weight = sum(weights.values())
        if total_weight <= 0:
            return random.choice(available_abilities)
        
        r = random.random() * total_weight
        for ability_name, weight in weights.items():
            r -= weight
            if r <= 0:
                return ability_name
        
        return available_abilities[0]
    
    def execute_boss_ability(self, boss, ability_name, dungeon, current_turn):
        """Execute a boss special ability"""
        boss.last_ability_turn = current_turn
        messages = []
        
        if ability_name == "summon_minions":
            messages.extend(self._summon_minions(boss, dungeon))
        elif ability_name == "dark_magic":
            messages.extend(self._dark_magic_blast(boss, dungeon))
        elif ability_name == "teleport_attack":
            messages.extend(self._teleport_attack(boss, dungeon))
        elif ability_name == "drain_life":
            messages.extend(self._drain_life(boss, dungeon))
        elif ability_name == "phase_shift":
            messages.extend(self._phase_shift(boss))
        
        return messages
    
    def _summon_minions(self, boss, dungeon):
        """Summon 2-3 creatures to fight alongside the boss"""
        messages = [f"{boss.name} raises their hands and chants in a dark tongue!"]
        
        # Find empty positions around the boss
        summon_positions = []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                
                x, y = boss.pos.x + dx, boss.pos.y + dy
                if (0 <= x < dungeon.width and 0 <= y < dungeon.height and
                    dungeon.grid[y][x] == CellType.FLOOR):
                    
                    # Check if position is empty
                    position_empty = True
                    for entity in dungeon.entities:
                        if entity.pos.x == x and entity.pos.y == y:
                            position_empty = False
                            break
                    
                    if position_empty:
                        summon_positions.append(Position(x, y))
        
        # Summon 2-3 creatures
        num_summons = min(random.randint(2, 3), len(summon_positions))
        for i in range(num_summons):
            pos = random.choice(summon_positions)
            summon_positions.remove(pos)
            
            # Create a summoned creature (slightly weaker than normal)
            creature_type = random.choice([EntityType.GOBLIN, EntityType.ORC])
            if creature_type == EntityType.GOBLIN:
                creature = Entity(
                    pos=pos,
                    type=EntityType.GOBLIN,
                    hp=8,
                    max_hp=8,
                    attack=4,
                    defense=1,
                    name="Summoned Goblin",
                    xp_value=15
                )
            else:
                creature = Entity(
                    pos=pos,
                    type=EntityType.ORC,
                    hp=12,
                    max_hp=12,
                    attack=6,
                    defense=2,
                    name="Summoned Orc",
                    xp_value=25
                )
            
            dungeon.entities.append(creature)
            messages.append(f"A {creature.name} appears!")
        
        return messages
    
    def _dark_magic_blast(self, boss, dungeon):
        """Powerful area-effect magic attack"""
        messages = [f"{boss.name} channels dark energy and unleashes a devastating blast!"]
        
        player = dungeon.player
        distance = max(abs(boss.pos.x - player.pos.x), abs(boss.pos.y - player.pos.y))
        
        if distance <= 6:  # Player is in range
            # Area damage around player
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    target_x, target_y = player.pos.x + dx, player.pos.y + dy
                    
                    # Check if player is at this position
                    if target_x == player.pos.x and target_y == player.pos.y:
                        damage = random.randint(15, 25) + boss.boss_phase * 3
                        player.hp -= damage
                        messages.append(f"Dark magic hits you for {damage} damage!")
                    
                    # Check for other entities at this position
                    for entity in dungeon.entities:
                        if (entity.pos.x == target_x and entity.pos.y == target_y and 
                            entity != boss and entity.type != EntityType.PLAYER):
                            damage = random.randint(8, 12)
                            entity.hp -= damage
                            if entity.hp <= 0:
                                messages.append(f"{entity.name} is destroyed by dark magic!")
        else:
            messages.append("The blast dissipates before reaching you.")
        
        return messages
    
    def _teleport_attack(self, boss, dungeon):
        """Teleport next to player and attack"""
        messages = [f"{boss.name} vanishes in a swirl of darkness!"]
        
        player = dungeon.player
        
        # Find positions adjacent to player
        adjacent_positions = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                
                x, y = player.pos.x + dx, player.pos.y + dy
                if (0 <= x < dungeon.width and 0 <= y < dungeon.height and
                    dungeon.grid[y][x] == CellType.FLOOR):
                    
                    # Check if position is empty
                    position_empty = True
                    for entity in dungeon.entities:
                        if entity.pos.x == x and entity.pos.y == y:
                            position_empty = False
                            break
                    
                    if position_empty:
                        adjacent_positions.append(Position(x, y))
        
        if adjacent_positions:
            # Teleport to position next to player
            new_pos = random.choice(adjacent_positions)
            boss.pos = new_pos
            messages.append(f"{boss.name} appears right next to you!")
            
            # Powerful attack
            damage = boss.attack + random.randint(5, 15)
            player.hp -= damage
            messages.append(f"{boss.name} strikes you for {damage} damage!")
        else:
            messages.append(f"{boss.name} fails to find a suitable teleport location.")
        
        return messages
    
    def _drain_life(self, boss, dungeon):
        """Drain player's health and heal boss"""
        messages = [f"{boss.name} extends their hand toward you, dark energy flowing!"]
        
        player = dungeon.player
        distance = max(abs(boss.pos.x - player.pos.x), abs(boss.pos.y - player.pos.y))
        
        if distance <= 8:  # In range
            drain_amount = random.randint(10, 20)
            actual_drain = min(drain_amount, player.hp - 1)  # Don't kill player outright
            
            player.hp -= actual_drain
            heal_amount = min(actual_drain, boss.max_hp - boss.hp)
            boss.hp += heal_amount
            
            messages.append(f"You feel your life force being drained for {actual_drain} damage!")
            if heal_amount > 0:
                messages.append(f"{boss.name} heals for {heal_amount} health!")
        else:
            messages.append("The life drain fails to reach you at this distance.")
        
        return messages
    
    def _phase_shift(self, boss):
        """Boss becomes partially incorporeal, reducing incoming damage"""
        messages = [f"{boss.name} begins to flicker between dimensions!"]
        
        # Add phase shift effect
        boss.active_effects.append(("phase_shift", 5))
        messages.append(f"{boss.name} becomes partially incorporeal!")
        
        return messages
    
    def get_boss_damage_reduction(self, boss):
        """Check if boss has damage reduction from phase shift"""
        for effect_name, _ in boss.active_effects:
            if effect_name == "phase_shift":
                return 0.5  # 50% damage reduction
        return 1.0  # No reduction