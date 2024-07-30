"""Main game states."""

from __future__ import annotations

import attrs
import numpy as np
import tcod.camera
import tcod.console
import tcod.event

import g
from game.action_tools import do_player_action
from game.actions import Bump
from game.components import HP, Graphic, MapShape, MaxHP, MemoryTiles, Position, Tiles, VisibleTiles
from game.constants import DIRECTION_KEYS
from game.rendering import render_bar, render_messages, render_names_at_position
from game.state import State
from game.tags import IsActor, IsGhost, IsIn, IsPlayer
from game.tiles import TILES

from . import color


@attrs.define
class ExampleState(State):
    """Example game state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                return do_player_action(self, player, Bump(DIRECTION_KEYS[sym]))
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

        actor_drawn = set()
        for entity in g.world.Q.all_of(components=[Position, Graphic], relations=[(IsIn, map_)]):
            pos = entity.components[Position]
            if not (0 <= pos.x < console.width and 0 <= pos.y < console.height):
                continue  # Out of bounds
            if pos in actor_drawn:
                continue  # Do not render over an actor
            if visible[pos.ij] == (IsGhost in entity.tags):
                continue
            if IsActor in entity.tags:
                actor_drawn.add(pos)
            graphic = entity.components[Graphic]
            console.rgb[["ch", "fg"]][pos.ij] = graphic.ch, graphic.fg

        console.rgb["fg"][console_slices][not_visible] //= 2
        console.rgb["bg"][console_slices][not_visible] //= 2

        render_bar(
            console,
            x=0,
            y=45,
            width=20,
            value=player.components[HP] / player.components[MaxHP],
            text=f" HP: {player.components[HP]}/{player.components[MaxHP]}",
            empty_color=color.bar_empty,
            full_color=color.bar_filled,
        )
        render_messages(g.world, width=40, height=5).blit(dest=console, dest_x=21, dest_y=45)
        if g.cursor_location:
            render_names_at_position(console, x=21, y=44, pos=Position(*g.cursor_location, map_))
