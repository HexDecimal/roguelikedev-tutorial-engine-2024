"""Action functions."""

from __future__ import annotations

import logging

import tcod.ecs  # noqa: TCH002

import game.states
from game.action import Action, Impossible, Success
from game.actor_tools import update_fov
from game.components import AI, HP
from game.state import State  # noqa: TCH001
from game.tags import IsActor, IsIn, IsPlayer

logger = logging.getLogger(__name__)


def do_player_action(state: State, player: tcod.ecs.Entity, action: Action) -> State:
    """Perform an action on the player."""
    assert IsPlayer in player.tags
    result = action(player)
    update_fov(player)
    match result:
        case Success():
            handle_enemy_turns(player.registry, player.relation_tag[IsIn])
        case Impossible():
            logger.debug("%r", result)

    if player.components[HP] <= 0:
        return game.states.GameOver()
    return state


def handle_enemy_turns(world: tcod.ecs.Registry, map_: tcod.ecs.Entity) -> None:
    """Perform enemy turns."""
    for enemy in world.Q.all_of(components=[AI], tags=[IsActor], relations=[(IsIn, map_)]):
        enemy.components[AI](enemy)
