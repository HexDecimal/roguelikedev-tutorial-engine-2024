"""Action functions."""

from __future__ import annotations

import logging

import tcod.ecs  # noqa: TCH002

from game.action import Action, Impossible, Success
from game.state import State  # noqa: TCH001
from game.tags import IsActor, IsIn, IsPlayer

logger = logging.getLogger(__name__)


def do_player_action(state: State, player: tcod.ecs.Entity, action: Action) -> State:
    """Perform an action on the player."""
    assert IsPlayer in player.tags
    result = action(player)
    match result:
        case Success():
            handle_enemy_turns(player.registry, player.relation_tag[IsIn])
            return state
        case Impossible():
            logger.debug("%r", result)
            return state


def handle_enemy_turns(world: tcod.ecs.Registry, map_: tcod.ecs.Entity) -> None:
    """Perform enemy turns."""
    for enemy in world.Q.all_of(tags=[IsActor], relations=[(IsIn, map_)]).none_of(tags=[IsPlayer]):
        logger.debug("%s", f"The {enemy} wonders when it will get to take a real turn.")
