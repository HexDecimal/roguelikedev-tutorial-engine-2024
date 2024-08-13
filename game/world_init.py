"""World initialization."""

from __future__ import annotations

from random import Random

import tcod.ecs

import game.actor_tools
import game.procgen
from game.components import HP, Defense, Graphic, MaxHP, Name, Position, Power, RewardXP
from game.effect import Effect
from game.effects import Healing
from game.item import ApplyAction
from game.items import Potion, RandomTargetScroll, TargetScroll
from game.map_tools import get_map
from game.messages import MessageLog, add_message
from game.spell import EntitySpell, PositionSpell
from game.spells import Fireball, LightningBolt
from game.tags import IsIn, IsPlayer


def new_world() -> tcod.ecs.Registry:
    """Return a new world."""
    world = tcod.ecs.Registry()
    world[None].components[Random] = Random()
    world[None].components[MessageLog] = MessageLog()

    init_creatures(world)
    init_items(world)

    map_ = get_map(world, game.procgen.Tombs(1))

    (start,) = world.Q.all_of(tags=["UpStairs"], relations=[(IsIn, map_)])

    player = game.actor_tools.spawn_actor(world["player"], start.components[Position])
    player.tags.add(IsPlayer)
    game.actor_tools.update_fov(player)

    add_message(world, "Hello and welcome, adventurer, to yet another dungeon!", "welcome_text")
    return world


def init_new_creature(
    world: tcod.ecs.Registry,
    name: str,
    ch: int,
    fg: tuple[int, int, int],
    hp: int,
    power: int,
    defense: int,
    xp: int,
) -> None:
    """Setup a new creature type."""
    race = world[name]
    race.components[Name] = name
    race.components[Graphic] = Graphic(ch, fg)
    race.components[HP] = race.components[MaxHP] = hp
    race.components[Power] = power
    race.components[Defense] = defense
    race.components[RewardXP] = xp


def init_creatures(world: tcod.ecs.Registry) -> None:
    """Initialize monster database."""
    init_new_creature(world, name="player", ch=ord("@"), fg=(255, 255, 255), hp=30, power=5, defense=2, xp=0)
    init_new_creature(world, name="orc", ch=ord("o"), fg=(63, 127, 63), hp=10, power=3, defense=0, xp=35)
    init_new_creature(world, name="troll", ch=ord("T"), fg=(0, 127, 0), hp=16, power=4, defense=1, xp=100)


def init_items(world: tcod.ecs.Registry) -> None:
    """Initialize item database."""
    health_potion = world["health_potion"]
    health_potion.components[Name] = "Health Potion"
    health_potion.components[Graphic] = Graphic(ord("!"), (127, 0, 255))
    health_potion.components[Effect] = Healing(4)
    health_potion.components[ApplyAction] = Potion()

    lightning_scroll = world["lightning_scroll"]
    lightning_scroll.components[Name] = "Lightning Scroll"
    lightning_scroll.components[Graphic] = Graphic(ord("~"), (255, 255, 0))
    lightning_scroll.components[ApplyAction] = RandomTargetScroll(maximum_range=5)
    lightning_scroll.components[EntitySpell] = LightningBolt(damage=20)

    fireball_scroll = world["fireball_scroll"]
    fireball_scroll.components[Name] = "Fireball Scroll"
    fireball_scroll.components[Graphic] = Graphic(ord("~"), (255, 0, 0))
    fireball_scroll.components[ApplyAction] = TargetScroll()
    fireball_scroll.components[PositionSpell] = Fireball(damage=12, radius=3)
