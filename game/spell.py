"""Abstract spell classes."""

from __future__ import annotations

from typing import Protocol

from tcod.ecs import Entity  # noqa: TCH002

from game.action import ActionResult  # noqa: TCH001


class Spell(Protocol):
    """Abstract spell."""

    def cast_at_entity(self, castor: Entity, item: Entity | None, target: Entity, /) -> ActionResult:
        """Cast at an entity."""
