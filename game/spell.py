"""Abstract spell classes."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np  # noqa: TC002
from numpy.typing import NDArray  # noqa: TC002
from tcod.ecs import Entity  # noqa: TC002

from game.action import ActionResult  # noqa: TC001
from game.components import Position  # noqa: TC001


@runtime_checkable
class EntitySpell(Protocol):
    """Abstract spell."""

    def cast_at_entity(self, castor: Entity, item: Entity | None, target: Entity, /) -> ActionResult:
        """Cast at an entity."""
        ...


@runtime_checkable
class PositionSpell(Protocol):
    """Abstract spell."""

    def cast_at_position(self, castor: Entity, item: Entity | None, target: Position, /) -> ActionResult:
        """Cast at a tile position."""
        ...


@runtime_checkable
class AreaOfEffect(Protocol):
    """Spell with an area of effect."""

    def get_affected_area(self, target: Position, *, player_pov: bool = False) -> NDArray[np.bool]:
        """Return the affect area for this spell."""
        ...
