"""Rendering functions."""

from __future__ import annotations

from collections.abc import Reversible  # noqa: TCH003

import tcod.console
import tcod.ecs

from game.components import MapShape, Name, Position, VisibleTiles
from game.messages import Message, MessageLog
from game.tags import IsGhost

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
    if not (0 <= x < map_width and 0 <= y < map_height):
        return
    is_visible = pos.map.components[VisibleTiles].item(pos.ij)
    known_entities = [
        entity
        for entity in pos.map.registry.Q.all_of(components=[Name], tags=[pos])
        if is_visible or (IsGhost in entity.tags)
    ]
    names = ", ".join(entity.components[Name] for entity in known_entities)
    console.print(x=x, y=y, string=names, fg=color.white)
