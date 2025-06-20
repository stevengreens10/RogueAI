"""
Save and load game functionality
"""

import json
import os
from .entities import Entity, EntityType, Item, Position, SpellType, Spell
from .dungeon import CellType, Dungeon
from .shop import Shop


class SaveLoadSystem:
    @staticmethod
    def save_game(game):
        """Save the current game state to a JSON file"""
        try:
            # Convert game state to serializable format
            save_data = {
                'dungeon': {
                    'width': game.dungeon.width,
                    'height': game.dungeon.height,
                    'level': game.dungeon.level,
                    'grid': [[cell.value for cell in row] for row in game.dungeon.grid],
                    'entities': [],
                    'items': [],
                    'stairs_pos': {'x': game.dungeon.stairs_pos.x, 'y': game.dungeon.stairs_pos.y} if game.dungeon.stairs_pos else None
                },
                'messages': game.messages,
                'game_over': game.game_over,
                'current_level': game.current_level,
                'in_shop': game.in_shop
            }
            
            # Save entities
            for entity in game.dungeon.entities:
                entity_data = {
                    'pos': {'x': entity.pos.x, 'y': entity.pos.y},
                    'type': entity.type.value,
                    'hp': entity.hp,
                    'max_hp': entity.max_hp,
                    'attack': entity.attack,
                    'defense': entity.defense,
                    'name': entity.name,
                    'gold': entity.gold,
                    'xp': entity.xp,
                    'level': entity.level,
                    'xp_value': entity.xp_value,
                    'inventory': [],
                    'equipment': None,
                    'mana': entity.mana,
                    'max_mana': entity.max_mana,
                    'angle': entity.angle,
                    'known_spells': [],
                    'active_effects': entity.active_effects
                }
                
                # Save inventory
                for item in entity.inventory:
                    item_data = {
                        'name': item.name,
                        'type': item.type.value,
                        'value': item.value,
                        'attack_bonus': item.attack_bonus,
                        'defense_bonus': item.defense_bonus,
                        'heal_amount': item.heal_amount,
                        'spell_type': item.spell_type.value if item.spell_type else None
                    }
                    entity_data['inventory'].append(item_data)
                
                # Save known spells
                for spell in entity.known_spells:
                    entity_data['known_spells'].append({
                        'spell_type': spell.spell_type.value,
                        'name': spell.name,
                        'description': spell.description,
                        'mana_cost': spell.mana_cost,
                        'damage': spell.damage,
                        'heal_amount': spell.heal_amount,
                        'range': spell.range,
                        'area_effect': spell.area_effect,
                        'status_effect': spell.status_effect,
                        'duration': spell.duration
                    })
                
                # Save weapon
                if entity.weapon:
                    entity_data['weapon'] = {
                        'name': entity.weapon.name,
                        'type': entity.weapon.type.value,
                        'value': entity.weapon.value,
                        'attack_bonus': entity.weapon.attack_bonus,
                        'defense_bonus': entity.weapon.defense_bonus,
                        'heal_amount': entity.weapon.heal_amount,
                        'spell_type': entity.weapon.spell_type.value if entity.weapon.spell_type else None
                    }
                else:
                    entity_data['weapon'] = None
                
                # Save shield
                if entity.shield:
                    entity_data['shield'] = {
                        'name': entity.shield.name,
                        'type': entity.shield.type.value,
                        'value': entity.shield.value,
                        'attack_bonus': entity.shield.attack_bonus,
                        'defense_bonus': entity.shield.defense_bonus,
                        'heal_amount': entity.shield.heal_amount,
                        'spell_type': entity.shield.spell_type.value if entity.shield.spell_type else None
                    }
                else:
                    entity_data['shield'] = None
                
                # Save equipment (backwards compatibility)
                if entity.equipment:
                    entity_data['equipment'] = {
                        'name': entity.equipment.name,
                        'type': entity.equipment.type.value,
                        'value': entity.equipment.value,
                        'attack_bonus': entity.equipment.attack_bonus,
                        'defense_bonus': entity.equipment.defense_bonus,
                        'heal_amount': entity.equipment.heal_amount
                    }
                else:
                    entity_data['equipment'] = None
                
                save_data['dungeon']['entities'].append(entity_data)
            
            # Save items
            for item_pos, item in game.dungeon.items:
                save_data['dungeon']['items'].append({
                    'pos': {'x': item_pos.x, 'y': item_pos.y},
                    'item': {
                        'name': item.name,
                        'type': item.type.value,
                        'value': item.value,
                        'attack_bonus': item.attack_bonus,
                        'defense_bonus': item.defense_bonus,
                        'heal_amount': item.heal_amount,
                        'spell_type': item.spell_type.value if item.spell_type else None
                    }
                })
            
            with open('savegame.json', 'w') as f:
                json.dump(save_data, f, indent=2)
            
            return True, "Game saved!"
            
        except Exception as e:
            return False, f"Failed to save game: {str(e)}"
    
    @staticmethod
    def load_game(game):
        """Load game state from JSON file"""
        try:
            with open('savegame.json', 'r') as f:
                save_data = json.load(f)
            
            # Restore dungeon
            level = save_data['dungeon'].get('level', 1)
            game.current_level = save_data.get('current_level', level)
            game.in_shop = save_data.get('in_shop', False)
            game.dungeon = Dungeon(save_data['dungeon']['width'], save_data['dungeon']['height'], level)
            
            # Restore stairs position
            stairs_data = save_data['dungeon'].get('stairs_pos')
            if stairs_data:
                game.dungeon.stairs_pos = Position(stairs_data['x'], stairs_data['y'])
            
            # Restore grid
            for y in range(game.dungeon.height):
                for x in range(game.dungeon.width):
                    cell_value = save_data['dungeon']['grid'][y][x]
                    for cell_type in CellType:
                        if cell_type.value == cell_value:
                            game.dungeon.grid[y][x] = cell_type
                            break
            
            # Initialize shop if needed
            if game.in_shop:
                game.shop = Shop(level=game.current_level)
            
            # Restore entities
            for entity_data in save_data['dungeon']['entities']:
                # Find entity type
                entity_type = None
                for et in EntityType:
                    if et.value == entity_data['type']:
                        entity_type = et
                        break
                
                entity = Entity(
                    pos=Position(entity_data['pos']['x'], entity_data['pos']['y']),
                    type=entity_type,
                    hp=entity_data['hp'],
                    max_hp=entity_data['max_hp'],
                    attack=entity_data['attack'],
                    defense=entity_data['defense'],
                    name=entity_data['name'],
                    inventory=[],
                    gold=entity_data['gold'],
                    xp=entity_data.get('xp', 0),
                    level=entity_data.get('level', 1),
                    xp_value=entity_data.get('xp_value', 0),
                    mana=entity_data.get('mana', 20),
                    max_mana=entity_data.get('max_mana', 20),
                    angle=entity_data.get('angle', 0.0),
                    known_spells=[],
                    active_effects=entity_data.get('active_effects', [])
                )
                
                # Restore inventory
                for item_data in entity_data['inventory']:
                    item_type = None
                    for it in EntityType:
                        if it.value == item_data['type']:
                            item_type = it
                            break
                    
                    spell_type = None
                    if item_data.get('spell_type'):
                        for st in SpellType:
                            if st.value == item_data['spell_type']:
                                spell_type = st
                                break
                    
                    item = Item(
                        name=item_data['name'],
                        type=item_type,
                        value=item_data['value'],
                        attack_bonus=item_data['attack_bonus'],
                        defense_bonus=item_data['defense_bonus'],
                        heal_amount=item_data['heal_amount'],
                        spell_type=spell_type
                    )
                    entity.inventory.append(item)
                
                # Restore known spells
                for spell_data in entity_data.get('known_spells', []):
                    spell_type = None
                    for st in SpellType:
                        if st.value == spell_data['spell_type']:
                            spell_type = st
                            break
                    
                    if spell_type:
                        spell = Spell(
                            spell_type=spell_type,
                            name=spell_data['name'],
                            description=spell_data['description'],
                            mana_cost=spell_data['mana_cost'],
                            damage=spell_data.get('damage', 0),
                            heal_amount=spell_data.get('heal_amount', 0),
                            range=spell_data.get('range', 1),
                            area_effect=spell_data.get('area_effect', False),
                            status_effect=spell_data.get('status_effect'),
                            duration=spell_data.get('duration', 0)
                        )
                        entity.known_spells.append(spell)
                
                # Restore weapon
                if entity_data.get('weapon'):
                    weapon_data = entity_data['weapon']
                    weapon_type = None
                    for it in EntityType:
                        if it.value == weapon_data['type']:
                            weapon_type = it
                            break
                    
                    weapon_spell_type = None
                    if weapon_data.get('spell_type'):
                        for st in SpellType:
                            if st.value == weapon_data['spell_type']:
                                weapon_spell_type = st
                                break
                    
                    entity.weapon = Item(
                        name=weapon_data['name'],
                        type=weapon_type,
                        value=weapon_data['value'],
                        attack_bonus=weapon_data['attack_bonus'],
                        defense_bonus=weapon_data['defense_bonus'],
                        heal_amount=weapon_data['heal_amount'],
                        spell_type=weapon_spell_type
                    )
                
                # Restore shield
                if entity_data.get('shield'):
                    shield_data = entity_data['shield']
                    shield_type = None
                    for it in EntityType:
                        if it.value == shield_data['type']:
                            shield_type = it
                            break
                    
                    shield_spell_type = None
                    if shield_data.get('spell_type'):
                        for st in SpellType:
                            if st.value == shield_data['spell_type']:
                                shield_spell_type = st
                                break
                    
                    entity.shield = Item(
                        name=shield_data['name'],
                        type=shield_type,
                        value=shield_data['value'],
                        attack_bonus=shield_data['attack_bonus'],
                        defense_bonus=shield_data['defense_bonus'],
                        heal_amount=shield_data['heal_amount'],
                        spell_type=shield_spell_type
                    )
                
                # Restore equipment (backwards compatibility)
                if entity_data.get('equipment') and not entity.weapon:
                    eq_data = entity_data['equipment']
                    eq_type = None
                    for it in EntityType:
                        if it.value == eq_data['type']:
                            eq_type = it
                            break
                    
                    entity.weapon = Item(
                        name=eq_data['name'],
                        type=eq_type,
                        value=eq_data['value'],
                        attack_bonus=eq_data['attack_bonus'],
                        defense_bonus=eq_data['defense_bonus'],
                        heal_amount=eq_data['heal_amount']
                    )
                
                game.dungeon.entities.append(entity)
                
                # Set player reference
                if entity.type == EntityType.PLAYER:
                    game.dungeon.player = entity
            
            # Restore items
            for item_data in save_data['dungeon']['items']:
                item_type = None
                for it in EntityType:
                    if it.value == item_data['item']['type']:
                        item_type = it
                        break
                
                item_spell_type = None
                if item_data['item'].get('spell_type'):
                    for st in SpellType:
                        if st.value == item_data['item']['spell_type']:
                            item_spell_type = st
                            break
                
                item = Item(
                    name=item_data['item']['name'],
                    type=item_type,
                    value=item_data['item']['value'],
                    attack_bonus=item_data['item']['attack_bonus'],
                    defense_bonus=item_data['item']['defense_bonus'],
                    heal_amount=item_data['item']['heal_amount'],
                    spell_type=item_spell_type
                )
                
                pos = Position(item_data['pos']['x'], item_data['pos']['y'])
                game.dungeon.items.append((pos, item))
            
            # Restore game state
            game.messages = save_data['messages']
            game.game_over = save_data['game_over']
            
            return True, "Game loaded!"
            
        except Exception as e:
            return False, f"Failed to load game: {str(e)}"