"""Generic entity functions."""

from __future__ import annotations

from tcod.ecs import Entity  # noqa: TCH002

from game.components import Name
from game.tags import EquippedBy


def get_name(entity: Entity) -> str:
    """Return the name of a generic entity."""
    name = [entity.components.get(Name, "???")]
    if EquippedBy in entity.relation_tag:
        name.append("(E)")
    return " ".join(name)
