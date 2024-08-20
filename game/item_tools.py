"""Functions for handling items."""

from __future__ import annotations

from tcod.ecs import Entity, IsA

from game.components import Name, Position


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
