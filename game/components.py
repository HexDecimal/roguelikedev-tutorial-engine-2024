"""Common entity components."""

from __future__ import annotations

from typing import Final, NamedTuple

import attrs
import numpy as np
import tcod.ecs
import tcod.ecs.callbacks
from numpy.typing import NDArray

from game.action import Action
from game.tags import IsIn


@attrs.define(frozen=True)
class Position:
    """Entity position."""

    x: int
    y: int
    map: tcod.ecs.Entity

    def __add__(self, other: tuple[int, int]) -> Position:
        """Return a Position offset by `other`."""
        return self.__class__(self.x + other[0], self.y + other[1], self.map)

    @property
    def ij(self) -> tuple[int, int]:
        """Return coordinates for Numpy indexing."""
        return self.y, self.x


@attrs.define(frozen=True)
class Graphic:
    """Entity glyph."""

    ch: int
    fg: tuple[int, int, int]


class MapShape(NamedTuple):
    """The shape of a map entity."""

    height: int
    width: int


Tiles: Final = ("Tiles", NDArray[np.int8])
"""The tile indexes of a map entity."""

VisibleTiles: Final = ("VisibleTiles", NDArray[np.bool])
"""Player visible tiles for a map."""

MemoryTiles: Final = ("MemoryTiles", NDArray[np.int8])
"""Last seen tiles for a map."""

Name: Final = ("Name", str)
"""Name of an entity."""

HP: Final = ("HP", int)
"""Current hit points."""

MaxHP: Final = ("MaxHP", int)
"""Maximum hit points."""

Power: Final = ("Power", int)
"""Attack power."""

Defense: Final = ("Defense", int)
"""Defense power."""

AI: Final = ("AI", Action)
"""Action for AI actor."""


@tcod.ecs.callbacks.register_component_changed(component=Position)
def on_position_changed(entity: tcod.ecs.Entity, old: Position | None, new: Position | None) -> None:
    """Called when an entities position is changed."""
    if old == new:
        return
    if old is not None:
        entity.tags.remove(old)
    if new is not None:
        entity.tags.add(new)
        entity.relation_tag[IsIn] = new.map
    else:
        del entity.relation_tags_many[IsIn]
