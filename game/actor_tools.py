"""Actor handling tools."""

from __future__ import annotations

from typing import Final

import numpy as np
import tcod.constants
import tcod.ecs
import tcod.map

from game.components import XP, Graphic, Level, MemoryTiles, Name, Position, Tiles, VisibleTiles
from game.messages import add_message
from game.tags import IsAlive, IsBlocking, IsGhost, IsIn, IsPlayer
from game.tiles import TILES


def get_player_actor(world: tcod.ecs.Registry) -> tcod.ecs.Entity:
    """Return the active player entity."""
    (player,) = world.Q.all_of(tags=[IsPlayer])
    return player


def update_fov(actor: tcod.ecs.Entity, *, clear: bool = False) -> None:
    """Update the FOV of an actor."""
    assert IsPlayer in actor.tags
    map_: Final = actor.relation_tag[IsIn]
    transparency: Final = TILES["transparent"][map_.components[Tiles]]
    old_visible: Final = map_.components[VisibleTiles]
    if clear:  # Unset visibility, for before level transitions.
        map_.components[VisibleTiles][:] = False
        new_visible = map_.components[VisibleTiles]
    else:
        map_.components[VisibleTiles] = new_visible = tcod.map.compute_fov(
            transparency,
            pov=actor.components[Position].ij,
            radius=10,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
        )
    map_.components[MemoryTiles] = np.where(new_visible, map_.components[Tiles], map_.components[MemoryTiles])

    now_invisible: Final = old_visible & ~new_visible  # Tiles which have gone out of view, should leave ghosts
    all_visible: Final = old_visible & new_visible  # Tiles visible in old and new FOV, should clear ghosts

    world: Final = actor.registry
    # Remove visible ghosts
    for entity in world.Q.all_of(components=[Position], tags=[IsGhost], relations=[(IsIn, map_)]):
        if all_visible[entity.components[Position].ij]:
            entity.clear()
    # Add ghosts for entities going out of view
    for entity in world.Q.all_of(components=[Position, Graphic], relations=[(IsIn, map_)]).none_of(tags=[IsGhost]):
        pos = entity.components[Position]
        if not now_invisible[pos.ij]:
            continue
        ghost = world[object()]
        ghost.tags.add(IsGhost)
        ghost.components[Position] = pos
        ghost.components[Graphic] = entity.components[Graphic]
        if Name in entity.components:
            ghost.components[Name] = entity.components[Name]


def spawn_actor(template: tcod.ecs.Entity, position: Position) -> tcod.ecs.Entity:
    """Spawn a new actor at a location and return the new entity."""
    actor = template.instantiate()
    actor.components[Position] = position
    actor.tags.add(IsBlocking)
    actor.tags.add(IsAlive)
    return actor


def required_xp_for_level(actor: tcod.ecs.Entity) -> int:
    """Return XP needed for the next level."""
    return 200 + (actor.components.get(Level, 1) - 1) * 150


def can_level_up(actor: tcod.ecs.Entity) -> bool:
    """Return True if this actor can level up."""
    return actor.components.get(XP, 0) >= required_xp_for_level(actor)


def level_up(actor: tcod.ecs.Entity) -> None:
    """Handle level up."""
    actor.components.setdefault(Level, 1)
    actor.components.setdefault(XP, 0)
    assert actor.components[XP] >= required_xp_for_level(actor)
    actor.components[XP] -= required_xp_for_level(actor)
    actor.components[Level] += 1
    add_message(actor.registry, f"You advance to level {actor.components[Level]}!")
