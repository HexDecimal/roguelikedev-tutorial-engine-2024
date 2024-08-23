"""Abstract item verb-action classes."""

from __future__ import annotations

from typing import Protocol

from tcod.ecs import Entity  # noqa: TCH002

from game.action import ActionResult  # noqa: TCH001


class ApplyAction(Protocol):
    """Action effect on item apply."""

    def on_apply(self, actor: Entity, item: Entity, /) -> ActionResult:
        """On apply behavior."""
        ...


class FullInventoryError(ValueError):
    """Inventory is full."""
