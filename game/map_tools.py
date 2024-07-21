"""Functions for working with map entities."""

from __future__ import annotations

import numpy as np
import tcod.ecs  # noqa: TCH002

from game.components import MapShape, MemoryTiles, Tiles, VisibleTiles


def new_map(world: tcod.ecs.World, shape: tuple[int, int]) -> tcod.ecs.Entity:
    """Return a new blank map."""
    map_ = world[object()]
    map_.components[MapShape] = MapShape(*shape)
    map_.components[Tiles] = np.zeros(shape, dtype=np.int8)
    map_.components[VisibleTiles] = np.zeros(shape, dtype=np.bool)
    map_.components[MemoryTiles] = np.zeros(shape, dtype=np.int8)

    return map_
