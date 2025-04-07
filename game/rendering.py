"""Rendering functions."""

from __future__ import annotations

from collections.abc import Reversible

import numpy as np
import tcod.camera
import tcod.console
import tcod.ecs
from numpy.typing import NDArray  # noqa: TC002

import g
from game.actor_tools import get_player_actor, required_xp_for_level
from game.components import HP, XP, Floor, Graphic, MapShape, MaxHP, MemoryTiles, Name, Position, Tiles, VisibleTiles
from game.messages import Message, MessageLog
from game.tags import IsAlive, IsGhost, IsIn, IsItem, IsPlayer
from game.tiles import TILES

from . import color


def render_bar(
    console: tcod.console.Console,
    *,
    x: int,
    y: int,
    width: int,
    text: str,
    value: float,
    empty_color: tuple[int, int, int],
    full_color: tuple[int, int, int],
    text_color: tuple[int, int, int] = color.bar_text,
) -> None:
    """Render a progress bar with text."""
    bar_width = int(value * width)

    console.draw_rect(x=x, y=y, width=width, height=1, ch=ord(" "), bg=empty_color)

    if bar_width > 0:
        console.draw_rect(x=x, y=y, width=bar_width, height=1, ch=ord(" "), bg=full_color)

    console.print_box(x=x, y=y, height=1, width=width, string=text, fg=text_color)


def render_messages(world: tcod.ecs.Registry, width: int, height: int) -> tcod.console.Console:
    """Return a console with the messages from `world` rendered to it.

    The `messages` are rendered starting at the last message and working backwards.
    """
    messages: Reversible[Message] = world[None].components[MessageLog]
    console = tcod.console.Console(width, height)
    y = height

    for message in reversed(messages):
        y -= tcod.console.get_height_rect(width, message.full_text)
        console.print_box(x=0, y=y, width=width, height=0, string=message.full_text, fg=message.fg)
        if y <= 0:
            break  # No more space to print messages.
    return console


def render_names_at_position(console: tcod.console.Console, x: int, y: int, pos: Position) -> None:
    """Render names of entities at `pos` to `console`."""
    map_height, map_width = pos.map.components[MapShape]
    if not (0 <= pos.x < map_width and 0 <= pos.y < map_height):
        return
    is_visible = pos.map.components[VisibleTiles].item(pos.ij)
    known_entities = [
        entity
        for entity in pos.map.registry.Q.all_of(components=[Name], tags=[pos])
        if is_visible or (IsGhost in entity.tags)
    ]
    names = ", ".join(entity.components[Name] for entity in known_entities)
    console.print(x=x, y=y, string=names, fg=color.white)


def main_render(  # noqa: C901
    world: tcod.ecs.Registry, console: tcod.console.Console, *, highlight: NDArray[np.bool] | None = None
) -> None:
    """Main rendering code."""
    player = get_player_actor(world)
    map_ = player.relation_tag[IsIn]
    console_slices, map_slices = tcod.camera.get_slices(
        (console.height, console.width), map_.components[MapShape], (0, 0)
    )

    visible = map_.components[VisibleTiles][map_slices]
    not_visible = ~visible

    light_tiles = map_.components[Tiles][map_slices]
    dark_tiles = map_.components[MemoryTiles][map_slices]

    console.rgb[console_slices] = TILES["graphic"][np.where(visible, light_tiles, dark_tiles)]

    rendered_priority: dict[Position, int] = {}
    for entity in world.Q.all_of(components=[Position, Graphic], relations=[(IsIn, map_)]):
        pos = entity.components[Position]
        if not (0 <= pos.x < console.width and 0 <= pos.y < console.height):
            continue  # Out of bounds
        if visible[pos.ij] == (IsGhost in entity.tags):
            continue
        render_order = 1
        if IsItem in entity.tags:
            render_order = 2
        if IsAlive in entity.tags:
            render_order = 3
        if IsPlayer in entity.tags:
            render_order = 4
        if rendered_priority.get(pos, 0) >= render_order:
            continue  # Do not render over a more important entity
        rendered_priority[pos] = render_order
        graphic = entity.components[Graphic]
        console.rgb[["ch", "fg"]][pos.ij] = graphic.ch, graphic.fg

    console.rgb["fg"][console_slices][not_visible] //= 2
    console.rgb["bg"][console_slices][not_visible] //= 2

    cursor_pos = world["cursor"].components.get(Position)
    if highlight is not None:
        console.rgb[["fg", "bg"]][console_slices][highlight[map_slices]] = ((0, 0, 0), (0xC0, 0xC0, 0xC0))
    if (
        cursor_pos is not None
        and 0 <= cursor_pos.x < console_slices[1].stop
        and 0 <= cursor_pos.y < console_slices[0].stop
    ):
        console.rgb[["fg", "bg"]][console_slices][cursor_pos.ij] = ((0, 0, 0), (255, 255, 255))

    render_bar(
        console,
        x=0,
        y=45,
        width=20,
        value=player.components[HP] / player.components.get(MaxHP, 1),
        text=f" HP: {player.components[HP]}/{player.components.get(MaxHP, 0)}",
        empty_color=color.bar_empty,
        full_color=color.bar_filled,
    )
    player.components.setdefault(XP, 0)
    render_bar(
        console,
        x=0,
        y=46,
        width=20,
        value=player.components[XP] / required_xp_for_level(player),
        text=f" XP: {player.components[XP]}/{required_xp_for_level(player)}",
        empty_color=color.bar_xp_empty,
        full_color=color.bar_xp_filled,
    )
    console.print(x=0, y=47, string=f""" Dungeon level: {map_.components.get(Floor, "?")}""", fg=(255, 255, 255))
    render_messages(world, width=40, height=5).blit(dest=console, dest_x=21, dest_y=45)
    if g.cursor_location:
        render_names_at_position(console, x=21, y=44, pos=Position(*g.cursor_location, map_))
