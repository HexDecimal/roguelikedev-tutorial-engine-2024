"""Common entity components."""

from __future__ import annotations

import attrs


@attrs.define(frozen=True)
class Position:
    """Entity position."""

    x: int
    y: int

    def __add__(self, other: Position | tuple[int, int]) -> Position:
        """Return a Position offset by `other`."""
        if isinstance(other, tuple):
            return self.__class__(self.x + other[0], self.y + other[1])
        return self.__class__(self.x + other.x, self.y + other.y)

    @property
    def ij(self) -> tuple[int, int]:
        """Return coordinates for Numpy indexing."""
        return self.y, self.x


@attrs.define(frozen=True)
class Graphic:
    """Entity glyph."""

    ch: int
    fg: tuple[int, int, int]
