"""Functions for handling items."""

from __future__ import annotations

import logging

from tcod.ecs import Entity, IsA

from game.components import EquipSlot, Name, Position
from game.tags import Affecting, EquippedBy, IsActor, IsIn

logger = logging.getLogger(__name__)


def spawn_item(template: Entity, position: Position) -> Entity:
    """Spawn an item based on `template` at `position`. Return the spawned entity."""
    item = template.instantiate()
    item.components[Position] = position
    return item


def can_stack(entity: Entity, target: Entity, /) -> bool:
    """Return True if two entities can be stacked."""
    return bool(
        entity.components.get(Name) == target.components.get(Name)
        and entity.relation_tag[IsA] is target.relation_tag[IsA]
    )


def equip_item(actor: Entity, item: Entity, /) -> None:
    """Equip an item on an actor."""
    unequip_slot(actor, item.components[EquipSlot])
    item.relation_tag[IsIn] = actor
    item.relation_tag[EquippedBy] = actor
    item.relation_tag[Affecting] = actor
    item.components.pop(Position, None)


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
