#!/usr/bin/env python
"""Main module."""

from __future__ import annotations

from random import Random

import tcod.console
import tcod.context
import tcod.ecs
import tcod.event
import tcod.tileset

import g
import game.procgen
import game.states
from game.components import Graphic, Position
from game.tags import IsPlayer

TITLE = "Yet Another Roguelike Tutorial"
CONSOLE_SIZE = 80, 50


def main() -> None:
    """Main entry point."""
    tileset = tcod.tileset.load_bdf("assets/cozette.bdf")
    g.console = tcod.console.Console(*CONSOLE_SIZE)

    g.world = tcod.ecs.Registry()
    g.world[None].components[Random] = Random()

    map_ = game.procgen.generate_dungeon(world=g.world, shape=(45, 80))
    g.world[None].relation_tag["ActiveMap"] = map_

    (start,) = g.world.Q.all_of(tags=["UpStairs"])

    player = g.world[object()]
    player.components[Position] = start.components[Position]
    player.components[Graphic] = Graphic(ord("@"), (255, 255, 255))
    player.tags.add(IsPlayer)

    g.state = game.states.ExampleState()

    with tcod.context.new(console=g.console, tileset=tileset, title=TITLE) as g.context:
        while True:
            g.console.clear()
            g.state.on_draw(g.console)
            g.context.present(g.console)

            for event in tcod.event.wait():
                match event:
                    case tcod.event.Quit():
                        raise SystemExit
                g.state = g.state.on_event(event)


if __name__ == "__main__":
    main()
