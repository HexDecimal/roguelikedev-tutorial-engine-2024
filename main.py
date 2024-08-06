#!/usr/bin/env python
"""Main module."""

from __future__ import annotations

import logging

import tcod.console
import tcod.context
import tcod.ecs
import tcod.event
import tcod.tileset

import g
import game.actor_tools
import game.procgen
import game.states
import game.world_init

TITLE = "Yet Another Roguelike Tutorial"
CONSOLE_SIZE = 80, 50


def main() -> None:
    """Main entry point."""
    logging.basicConfig(level="DEBUG")
    tileset = tcod.tileset.load_tilesheet("assets/Alloy_curses_12x12.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    g.console = tcod.console.Console(*CONSOLE_SIZE)

    g.world = game.world_init.new_world()

    g.state = game.states.InGame()

    with tcod.context.new(console=g.console, tileset=tileset, title=TITLE) as g.context:
        while True:
            g.console.clear()
            g.state.on_draw(g.console)
            g.context.present(g.console)

            for event in tcod.event.wait():
                event = g.context.convert_event(event)  # noqa: PLW2901
                match event:
                    case tcod.event.Quit():
                        raise SystemExit
                    case tcod.event.MouseMotion(position=position):
                        g.cursor_location = position
                    case tcod.event.WindowEvent(type="WindowLeave"):
                        g.cursor_location = None
                g.state = g.state.on_event(event)


if __name__ == "__main__":
    main()
