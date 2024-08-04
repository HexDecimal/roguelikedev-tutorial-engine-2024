"""Effect base types."""

from __future__ import annotations

from typing import Protocol

from tcod.ecs import Entity  # noqa: TCH002


class Effect(Protocol):
    """A common effect protocol.."""

    __slots__ = ()

    def affect(self, entity: Entity) -> None:
        """Apply this effect to `entity`."""
