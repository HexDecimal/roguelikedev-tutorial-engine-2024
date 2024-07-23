"""Main game states."""

from __future__ import annotations

import attrs
import numpy as np
import tcod.camera
import tcod.console
import tcod.event

import g
from game.actions import Bump
from game.components import Graphic, MapShape, MemoryTiles, Position, Tiles, VisibleTiles
from game.constants import DIRECTION_KEYS
from game.tags import IsGhost, IsIn, IsPlayer
from game.tiles import TILES

from .state import State


@attrs.define
class ExampleState(State):
    """Example game state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                Bump(DIRECTION_KEYS[sym])(player)
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the current map and entities."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        map_ = player.relation_tag[IsIn]
        console_slices, map_slices = tcod.camera.get_slices(
            (console.height, console.width), map_.components[MapShape], (0, 0)
        )

        visible = map_.components[VisibleTiles][map_slices]
        not_visible = ~visible

        light_tiles = map_.components[Tiles][map_slices]
        dark_tiles = map_.components[MemoryTiles][map_slices]

        console.rgb[console_slices] = TILES["graphic"][np.where(visible, light_tiles, dark_tiles)]

        for entity in g.world.Q.all_of(components=[Position, Graphic], relations=[(IsIn, map_)]):
            pos = entity.components[Position]
            if not (0 <= pos.x < console.width and 0 <= pos.y < console.height):
                continue
            if visible[pos.ij] == (IsGhost in entity.tags):
                continue
            graphic = entity.components[Graphic]
            console.rgb[["ch", "fg"]][pos.ij] = graphic.ch, graphic.fg

        console.rgb["fg"][console_slices][not_visible] //= 2
        console.rgb["bg"][console_slices][not_visible] //= 2
