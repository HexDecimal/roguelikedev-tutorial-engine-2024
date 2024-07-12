"""Common entity components."""

from __future__ import annotations

from typing import Final, NamedTuple

import attrs
import numpy as np
import tcod.ecs  # noqa: TCH002
from numpy.typing import NDArray


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
