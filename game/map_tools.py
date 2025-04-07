"""Functions for working with map entities."""

from __future__ import annotations

import numpy as np
import tcod.ecs  # noqa: TC002

from game.components import MapShape, MemoryTiles, Tiles, VisibleTiles
from game.map import MapKey  # noqa: TC001


def new_map(world: tcod.ecs.World, shape: tuple[int, int]) -> tcod.ecs.Entity:
    """Return a new blank map."""
    map_ = world[object()]
    map_.components[MapShape] = MapShape(*shape)
    map_.components[Tiles] = np.zeros(shape, dtype=np.int8)
    map_.components[VisibleTiles] = np.zeros(shape, dtype=np.bool)
    map_.components[MemoryTiles] = np.zeros(shape, dtype=np.int8)

    return map_


def get_map(world: tcod.ecs.World, key: MapKey) -> tcod.ecs.Entity:
    """Get a map, generating it on demand."""
    query = world.Q.all_of(tags=[key])
    if query:
        (map_,) = query
        return map_
    map_ = key.generate(world)
    map_.tags.add(key)
    return map_
