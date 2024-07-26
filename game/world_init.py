"""World initialization."""

from __future__ import annotations

from random import Random

import tcod.ecs

import game.actor_tools
import game.procgen
from game.components import Graphic, Name, Position
from game.tags import IsActor, IsPlayer


def new_world() -> tcod.ecs.Registry:
    """Return a new world."""
    world = tcod.ecs.Registry()
    world[None].components[Random] = Random()

    init_creatures(world)

    map_ = game.procgen.generate_dungeon(world=world, shape=(45, 80))
    world[None].relation_tag["ActiveMap"] = map_

    (start,) = world.Q.all_of(tags=["UpStairs"])

    player = world["player"].instantiate()
    player.components[Position] = start.components[Position]
    player.tags.add(IsPlayer)
    game.actor_tools.update_fov(player)
    return world


def init_creatures(world: tcod.ecs.Registry) -> None:
    """Initialize monster database."""
    world["player"].components[Name] = "Player"
    world["player"].components[Graphic] = Graphic(ord("@"), (255, 255, 255))
    world["player"].tags.add(IsActor)

    world["orc"].components[Name] = "Orc"
    world["orc"].components[Graphic] = Graphic(ord("o"), (63, 127, 63))
    world["orc"].tags.add(IsActor)

    world["troll"].components[Name] = "Troll"
    world["troll"].components[Graphic] = Graphic(ord("T"), (0, 127, 0))
    world["troll"].tags.add(IsActor)
