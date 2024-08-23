"""Functions for handling items."""

from __future__ import annotations

import logging

from tcod.ecs import Entity, IsA

from game.action import ActionResult, Impossible, Success
from game.components import AssignedKey, Count, EquipSlot, Name, Position
from game.constants import INVENTORY_KEYS
from game.entity_tools import get_name
from game.item import FullInventoryError
from game.tags import Affecting, EquippedBy, IsActor, IsIn, IsItem

logger = logging.getLogger(__name__)


def spawn_item(template: Entity, position: Position) -> Entity:
    """Spawn an item based on `template` at `position`. Return the spawned entity."""
    item = template.instantiate()
    item.components[Position] = position
    return item


def can_stack(entity: Entity, onto: Entity, /) -> bool:
    """Return True if two entities can be stacked."""
    return bool(
        entity.components.get(Name) == onto.components.get(Name)
        and entity.relation_tag.get(IsA) is onto.relation_tag.get(IsA)
    )


def equip_item(actor: Entity, item: Entity, /) -> ActionResult:
    """Equip an item on an actor."""
    unequip_slot(actor, item.components[EquipSlot])
    if not (result := add_to_inventory(actor, item)):
        return result
    item.relation_tag[EquippedBy] = actor
    item.relation_tag[Affecting] = actor
    item.components.pop(Position, None)
    return Success()


def unequip_slot(actor: Entity, slot: object, /) -> None:
    """Free an equipment slot on an actor."""
    for e in actor.registry.Q.all_of(relations=[(EquippedBy, actor)]):
        if e.components[EquipSlot] == slot:
            unequip_item(e)
            return


def unequip_item(item: Entity, /) -> None:
    """Unequip an item from its actor."""
    if IsActor not in item.relation_tag[IsIn].tags:
        logger.warning("%s not equipped by an actor!", item)
        return

    item.relation_tag.pop(EquippedBy, None)
    item.relation_tag.pop(Affecting, None)


def consume_item(item: Entity) -> None:
    """Consume an item, delete the item if its stack ie depleted."""
    item.components.setdefault(Count, 1)
    item.components[Count] -= 1
    if item.components[Count] <= 0:
        item.clear()


def add_to_inventory(actor: Entity, item: Entity) -> ActionResult:
    """Add an item to actors inventory."""
    if item.relation_tag.get(IsIn) is actor:
        return Success()  # Already in inventory.
    for held_item in actor.registry.Q.all_of(tags=[IsItem], relations=[(IsIn, actor)]):
        if not can_stack(item, held_item):
            continue
        held_item.components.setdefault(Count, 1)
        held_item.components[Count] += item.components.get(Count, 1)
        msg = f"You picked up the {get_name(item)}!"
        item.clear()
        return Success(msg)
    try:
        assign_item_key(actor, item)
    except FullInventoryError:
        return Impossible("Inventory is full.")

    item.components.pop(Position, None)
    item.relation_tag[IsIn] = actor

    return Success(f"You picked up the {get_name(item)}!")


def get_inventory_keys(actor: Entity) -> dict[str, Entity]:
    """Return a {key: item} dict of an actors inventory."""
    return {e.components[AssignedKey]: e for e in actor.registry.Q.all_of(tags=[IsItem], relations=[(IsIn, actor)])}


def assign_item_key(actor: Entity, item: Entity) -> None:
    """Assign a free key to an item. Raise FullInventoryError if no key is available.

    Should be called before adding the item to the inventory.
    """
    inventory = get_inventory_keys(actor)
    for key in INVENTORY_KEYS:
        if key in inventory:
            continue
        item.components[AssignedKey] = key
        return
    raise FullInventoryError
