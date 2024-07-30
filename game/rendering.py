"""Rendering functions."""

from __future__ import annotations

import tcod.console  # noqa: TCH002

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
