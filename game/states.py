"""Main game states."""

from __future__ import annotations

import attrs
import tcod.camera
import tcod.console
import tcod.event
from tcod.event import KeySym

import g
from game.actions import Move
from game.components import Graphic, MapShape, Position, Tiles
from game.tags import IsPlayer
from game.tiles import TILES

from .state import State


@attrs.define
class ExampleState(State):
    """Example game state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=KeySym.UP):
                Move((0, -1))(player)
            case tcod.event.KeyDown(sym=KeySym.DOWN):
                Move((0, 1))(player)
            case tcod.event.KeyDown(sym=KeySym.LEFT):
                Move((-1, 0))(player)
            case tcod.event.KeyDown(sym=KeySym.RIGHT):
                Move((1, 0))(player)
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Draw the player position."""
        map_ = g.world[None].relation_tag["ActiveMap"]
        console_slices, map_slices = tcod.camera.get_slices(
            (console.height, console.width), map_.components[MapShape], (0, 0)
        )
        console.rgb[console_slices] = TILES["graphic"][map_.components[Tiles][map_slices]]

        for entity in g.world.Q.all_of(components=[Position, Graphic]):
            pos = entity.components[Position]
            if not (0 <= pos.x < console.width and 0 <= pos.y < console.height):
                continue
            graphic = entity.components[Graphic]
            console.rgb[["ch", "fg"]][pos.ij] = graphic.ch, graphic.fg
