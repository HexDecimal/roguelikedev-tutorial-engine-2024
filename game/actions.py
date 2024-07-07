"""Main actions."""

from __future__ import annotations

import attrs
import tcod.ecs  # noqa: TCH002

from game.components import Position


@attrs.define
class Move:
    """Move an entity in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> None:
        """Check and apply the movement."""
        entity.components[Position] += self.direction
