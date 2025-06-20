"""
Magic system for AIRogue - spell casting, effects, and spellbook management
"""

import random
import math
from game.entities import Spell, SpellType, EntityType, Item
from game.dungeon import CellType


class MagicSystem:
    """Handles all magic-related functionality"""
    
    def __init__(self):
        self.spell_definitions = self._create_spell_definitions()
    
    def _create_spell_definitions(self):
        """Define all available spells in the game"""
        return {
            SpellType.FIREBALL: Spell(
                spell_type=SpellType.FIREBALL,
                name="Fireball",
                description="Launches a fiery projectile that deals damage",
                mana_cost=8,
                damage=15,
                range=5,
                area_effect=True
            ),
            SpellType.HEAL: Spell(
                spell_type=SpellType.HEAL,
                name="Heal",
                description="Restores health to the caster",
                mana_cost=6,
                heal_amount=20,
                range=0
            ),
            SpellType.MAGIC_MISSILE: Spell(
                spell_type=SpellType.MAGIC_MISSILE,
                name="Magic Missile",
                description="An unerring magical projectile",
                mana_cost=4,
                damage=8,
                range=6
            ),
            SpellType.LIGHTNING_BOLT: Spell(
                spell_type=SpellType.LIGHTNING_BOLT,
                name="Lightning Bolt",
                description="A crackling bolt of electricity",
                mana_cost=10,
                damage=18,
                range=8
            ),
            SpellType.SHIELD: Spell(
                spell_type=SpellType.SHIELD,
                name="Magic Shield",
                description="Creates a magical barrier that increases defense",
                mana_cost=5,
                status_effect="shield",
                duration=10
            ),
            SpellType.TELEPORT: Spell(
                spell_type=SpellType.TELEPORT,
                name="Teleport",
                description="Instantly moves the caster to a nearby location",
                mana_cost=12,
                range=3
            ),
            SpellType.FREEZE: Spell(
                spell_type=SpellType.FREEZE,
                name="Freeze",
                description="Freezes an enemy, preventing movement",
                mana_cost=7,
                status_effect="frozen",
                duration=3,
                range=4
            ),
            SpellType.POISON_CLOUD: Spell(
                spell_type=SpellType.POISON_CLOUD,
                name="Poison Cloud",
                description="Creates a toxic cloud that damages over time",
                mana_cost=9,
                damage=5,
                area_effect=True,
                status_effect="poisoned",
                duration=5,
                range=3
            )
        }
    
    def create_spellbook(self, spell_type, level=1):
        """Create a spellbook item for a specific spell"""
        spell = self.spell_definitions[spell_type]
        spellbook_names = {
            SpellType.FIREBALL: ["Tome of Flames", "Fireball Grimoire", "Pyromancer's Manual"],
            SpellType.HEAL: ["Book of Healing", "Restoration Codex", "Life Magic Primer"],
            SpellType.MAGIC_MISSILE: ["Arcane Projectiles", "Force Magic Guide", "Missile Mastery"],
            SpellType.LIGHTNING_BOLT: ["Storm Caller's Text", "Lightning Grimoire", "Thunder Manual"],
            SpellType.SHIELD: ["Defensive Magic", "Ward Casting Guide", "Protection Primer"],
            SpellType.TELEPORT: ["Dimensional Travel", "Teleportation Theory", "Blink Mastery"],
            SpellType.FREEZE: ["Frost Magic", "Ice Shard Codex", "Cryomancer's Guide"],
            SpellType.POISON_CLOUD: ["Toxic Secrets", "Poison Mastery", "Venom Grimoire"]
        }
        
        name = random.choice(spellbook_names[spell_type])
        magic_bonus = random.randint(1, 3) + (level - 1)  # 1-3 base + level scaling
        value = spell.mana_cost * 10 + (level * 5) + (magic_bonus * 15)
        
        return Item(
            name=name,
            type=EntityType.SPELLBOOK,
            value=value,
            magic_bonus=magic_bonus,
            spell_type=spell_type
        )
    
    def learn_spell_from_book(self, player, spellbook):
        """Learn a spell from a spellbook"""
        if spellbook.spell_type is None:
            return False, "This is not a valid spellbook."
        
        spell = self.spell_definitions[spellbook.spell_type]
        
        # Check if player already knows this spell
        for known_spell in player.known_spells:
            if known_spell.spell_type == spell.spell_type:
                return False, f"You already know {spell.name}."
        
        # Learn the spell
        player.known_spells.append(spell)
        return True, f"You learned {spell.name}!"
    
    def get_equipped_spellbook_spells(self, player):
        """Get spells available from equipped spellbook"""
        if not player.shield or player.shield.type != EntityType.SPELLBOOK:
            return []
        
        if player.shield.spell_type is None:
            return []
        
        spell = self.spell_definitions[player.shield.spell_type]
        return [spell]
    
    def can_cast_spell(self, caster, spell):
        """Check if a caster can cast a specific spell"""
        # Check if spell is known or available from equipped spellbook
        spell_known = spell in caster.known_spells
        spell_from_book = False
        
        if not spell_known:
            spellbook_spells = self.get_equipped_spellbook_spells(caster)
            spell_from_book = any(s.spell_type == spell.spell_type for s in spellbook_spells)
        
        if not spell_known and not spell_from_book:
            return False, "You don't know this spell."
        
        if caster.mana < spell.mana_cost:
            return False, f"Not enough mana. Need {spell.mana_cost}, have {caster.mana}."
        
        return True, ""
    
    def cast_spell(self, caster, spell, dungeon, target_pos=None, godmode=False):
        """Cast a spell and apply its effects"""
        can_cast, reason = self.can_cast_spell(caster, spell)
        if not can_cast and not godmode:  # Godmode bypasses mana requirements
            return False, reason
        
        # Consume mana (unless in godmode)
        if not godmode:
            caster.mana -= spell.mana_cost
        
        # Apply spell effects based on spell type
        result_message = ""
        
        if spell.spell_type == SpellType.HEAL:
            magic_bonus = self._get_magic_bonus(caster)
            heal_amount = min(spell.heal_amount + magic_bonus, caster.max_hp - caster.hp)
            caster.hp += heal_amount
            result_message = f"You heal for {heal_amount} HP!"
        
        elif spell.spell_type == SpellType.SHIELD:
            self._apply_status_effect(caster, spell.status_effect, spell.duration)
            result_message = "You are protected by a magical shield!"
        
        elif spell.spell_type == SpellType.TELEPORT:
            if target_pos:
                result_message = self._cast_teleport(caster, dungeon, target_pos, spell.range)
            else:
                result_message = "Choose a target location for teleport."
        
        elif spell.spell_type in [SpellType.FIREBALL, SpellType.MAGIC_MISSILE, SpellType.LIGHTNING_BOLT]:
            if target_pos:
                result_message = self._cast_projectile_spell(caster, spell, dungeon, target_pos)
            else:
                result_message = f"Choose a target for {spell.name}."
        
        elif spell.spell_type == SpellType.FREEZE:
            if target_pos:
                result_message = self._cast_target_spell(caster, spell, dungeon, target_pos)
            else:
                result_message = "Choose a target to freeze."
        
        elif spell.spell_type == SpellType.POISON_CLOUD:
            if target_pos:
                result_message = self._cast_area_spell(caster, spell, dungeon, target_pos)
            else:
                result_message = "Choose a location for the poison cloud."
        
        return True, result_message
    
    def _cast_projectile_spell(self, caster, spell, dungeon, target_pos):
        """Cast a projectile spell that travels to target"""
        distance = self._calculate_distance(caster.pos, target_pos)
        
        if distance > spell.range:
            return f"{spell.name} is out of range!"
        
        # Check line of sight
        if not self._has_line_of_sight(caster.pos, target_pos, dungeon):
            return f"{spell.name} is blocked!"
        
        # Calculate magic bonus from equipped spellbook
        magic_bonus = self._get_magic_bonus(caster)
        
        # Find target entity
        target = self._find_entity_at_position(dungeon, target_pos)
        if target and target != caster:
            damage = spell.damage + magic_bonus + random.randint(-2, 2)  # Add magic bonus and variance
            target.hp -= damage
            
            if target.hp <= 0:
                return f"{spell.name} hits {target.name} for {damage} damage, killing them!"
            else:
                return f"{spell.name} hits {target.name} for {damage} damage!"
        
        return f"{spell.name} hits the ground harmlessly."
    
    def _cast_target_spell(self, caster, spell, dungeon, target_pos):
        """Cast a spell that targets a specific entity"""
        distance = self._calculate_distance(caster.pos, target_pos)
        
        if distance > spell.range:
            return f"{spell.name} is out of range!"
        
        target = self._find_entity_at_position(dungeon, target_pos)
        if target and target != caster:
            if spell.status_effect:
                self._apply_status_effect(target, spell.status_effect, spell.duration)
                return f"{target.name} is affected by {spell.name}!"
            
            if spell.damage > 0:
                target.hp -= spell.damage
                return f"{spell.name} hits {target.name} for {spell.damage} damage!"
        
        return f"{spell.name} has no target."
    
    def _cast_area_spell(self, caster, spell, dungeon, target_pos):
        """Cast an area effect spell"""
        distance = self._calculate_distance(caster.pos, target_pos)
        
        if distance > spell.range:
            return f"{spell.name} is out of range!"
        
        magic_bonus = self._get_magic_bonus(caster)
        affected_count = 0
        
        # Affect entities in a 3x3 area around target
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                check_pos = type(target_pos)(target_pos.x + dx, target_pos.y + dy)
                target = self._find_entity_at_position(dungeon, check_pos)
                
                if target and target != caster:
                    if spell.damage > 0:
                        damage = spell.damage + magic_bonus
                        target.hp -= damage
                    
                    if spell.status_effect:
                        self._apply_status_effect(target, spell.status_effect, spell.duration)
                    
                    affected_count += 1
        
        if affected_count > 0:
            return f"{spell.name} affects {affected_count} targets!"
        else:
            return f"{spell.name} hits an empty area."
    
    def _cast_teleport(self, caster, dungeon, target_pos, max_range):
        """Cast teleport spell"""
        distance = self._calculate_distance(caster.pos, target_pos)
        
        if distance > max_range:
            return "Teleport destination is too far!"
        
        # Check if target position is valid
        if (target_pos.x < 0 or target_pos.x >= dungeon.width or
            target_pos.y < 0 or target_pos.y >= dungeon.height):
            return "Cannot teleport outside the dungeon!"
        
        if dungeon.grid[target_pos.y][target_pos.x] == CellType.WALL:
            return "Cannot teleport into a wall!"
        
        # Check if position is occupied
        if self._find_entity_at_position(dungeon, target_pos):
            return "Cannot teleport into an occupied space!"
        
        # Teleport the caster
        caster.pos = target_pos
        return "You teleport successfully!"
    
    def _apply_status_effect(self, entity, effect_name, duration):
        """Apply a temporary status effect to an entity"""
        # Remove existing effect of the same type
        entity.active_effects = [effect for effect in entity.active_effects 
                                if effect[0] != effect_name]
        
        # Add new effect
        entity.active_effects.append((effect_name, duration))
    
    def update_effects(self, entity, is_player_in_godmode=False):
        """Update temporary effects on an entity (call each turn)"""
        effects_to_remove = []
        messages = []
        
        for i, (effect_name, duration) in enumerate(entity.active_effects):
            if duration <= 1:
                effects_to_remove.append(i)
                messages.append(self._remove_effect(entity, effect_name))
            else:
                # Reduce duration
                entity.active_effects[i] = (effect_name, duration - 1)
                
                # Apply ongoing effects
                if effect_name == "poisoned":
                    if is_player_in_godmode:
                        messages.append(f"{entity.name} resists poison damage (godmode)!")
                    else:
                        entity.hp -= 2
                        messages.append(f"{entity.name} takes 2 poison damage!")
        
        # Remove expired effects (in reverse order to maintain indices)
        for i in reversed(effects_to_remove):
            entity.active_effects.pop(i)
        
        return messages
    
    def _remove_effect(self, entity, effect_name):
        """Remove a status effect and return a message"""
        if effect_name == "shield":
            return f"{entity.name}'s magical shield fades."
        elif effect_name == "frozen":
            return f"{entity.name} thaws out."
        elif effect_name == "poisoned":
            return f"{entity.name} recovers from poison."
        return f"{entity.name}'s {effect_name} effect ends."
    
    def get_defense_bonus(self, entity):
        """Get defense bonus from active magical effects"""
        bonus = 0
        for effect_name, _ in entity.active_effects:
            if effect_name == "shield":
                bonus += 5
        return bonus
    
    def is_frozen(self, entity):
        """Check if entity is frozen and cannot move"""
        for effect_name, _ in entity.active_effects:
            if effect_name == "frozen":
                return True
        return False
    
    def _calculate_distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))
    
    def _has_line_of_sight(self, start_pos, end_pos, dungeon):
        """Check if there's a clear line of sight between two positions"""
        dx = abs(end_pos.x - start_pos.x)
        dy = abs(end_pos.y - start_pos.y)
        
        x, y = start_pos.x, start_pos.y
        x_inc = 1 if end_pos.x > start_pos.x else -1
        y_inc = 1 if end_pos.y > start_pos.y else -1
        
        error = dx - dy
        
        while True:
            if x == end_pos.x and y == end_pos.y:
                break
            
            # Check if current position blocks line of sight
            if (0 <= x < dungeon.width and 0 <= y < dungeon.height and 
                dungeon.grid[y][x] == CellType.WALL):
                return False
            
            if error * 2 > -dy:
                error -= dy
                x += x_inc
            
            if error * 2 < dx:
                error += dx
                y += y_inc
        
        return True
    
    def _find_entity_at_position(self, dungeon, pos):
        """Find an entity at a specific position"""
        for entity in dungeon.entities:
            if entity.pos.x == pos.x and entity.pos.y == pos.y and entity.hp > 0:
                return entity
        return None
    
    def get_available_spells(self, caster):
        """Get list of spells the caster can currently cast"""
        available = []
        
        # Add learned spells
        for spell in caster.known_spells:
            can_cast, _ = self.can_cast_spell(caster, spell)
            available.append((spell, can_cast))
        
        # Add spells from equipped spellbook
        spellbook_spells = self.get_equipped_spellbook_spells(caster)
        for spell in spellbook_spells:
            # Check if we already have this spell in the list (avoid duplicates)
            spell_already_listed = any(s.spell_type == spell.spell_type for s, _ in available)
            if not spell_already_listed:
                can_cast, _ = self.can_cast_spell_from_item(caster, spell)
                available.append((spell, can_cast))
        
        return available
    
    def can_cast_spell_from_item(self, caster, spell):
        """Check if a caster can cast a spell from an equipped item"""
        if caster.mana < spell.mana_cost:
            return False, f"Not enough mana. Need {spell.mana_cost}, have {caster.mana}."
        
        return True, ""
    
    def _get_magic_bonus(self, caster):
        """Get magic bonus from equipped spellbook"""
        if hasattr(caster, 'shield') and caster.shield and caster.shield.type == EntityType.SPELLBOOK:
            return caster.shield.magic_bonus
        return 0