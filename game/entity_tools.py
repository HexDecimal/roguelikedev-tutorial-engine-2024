"""Generic entity functions."""

from __future__ import annotations

from tcod.ecs import Entity  # noqa: TC002

from game.components import Count, Name
from game.tags import EquippedBy


def get_name(entity: Entity) -> str:
    """Return the name of a generic entity."""
    return entity.components.get(Name, "???")


def get_desc(entity: Entity) -> str:
    """Return a description of an entity."""
    name = get_name(entity)
    if entity.components.get(Count, 1) != 1:
        name = f"{entity.components[Count]}x{name}"
    if EquippedBy in entity.relation_tag:
        name += " (E)"
    return name
