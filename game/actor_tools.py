"""Actor handling tools."""

from __future__ import annotations

import numpy as np
import tcod.constants
import tcod.ecs
import tcod.map

from game.components import Graphic, MemoryTiles, Name, Position, Tiles, VisibleTiles
from game.tags import IsGhost, IsIn, IsPlayer
from game.tiles import TILES


def update_fov(actor: tcod.ecs.Entity) -> None:
    """Update the FOV of an actor."""
    assert IsPlayer in actor.tags
    map_ = actor.relation_tag[IsIn]
    transparency = TILES["transparent"][map_.components[Tiles]]
    map_.components[VisibleTiles] = visible = tcod.map.compute_fov(
        transparency,
        pov=actor.components[Position].ij,
        radius=10,
        algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
    )
    map_.components[MemoryTiles] = np.where(visible, map_.components[Tiles], map_.components[MemoryTiles])

    world = actor.world
    # Remove visible ghosts
    for entity in world.Q.all_of(components=[Position], tags=[IsGhost], relations=[(IsIn, map_)]):
        if visible[entity.components[Position].ij]:
            entity.clear()
    # Add ghosts for visible entities
    for entity in world.Q.all_of(components=[Position], relations=[(IsIn, map_)]).none_of(tags=[IsGhost]):
        pos = entity.components[Position]
        if not visible[pos.ij]:
            continue
        ghost = world[object()]
        ghost.tags.add(IsGhost)
        ghost.components[Position] = pos
        ghost.components[Graphic] = entity.components[Graphic]
        if Name in entity.components:
            ghost.components[Name] = entity.components[Name]
