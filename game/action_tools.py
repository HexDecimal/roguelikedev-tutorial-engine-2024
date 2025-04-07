"""Action functions."""

from __future__ import annotations

import logging

import tcod.ecs  # noqa: TC002

import game.states
from game.action import Action, Impossible, Poll, Success
from game.actor_tools import can_level_up, update_fov
from game.components import AI, HP
from game.messages import add_message
from game.state import State  # noqa: TC001
from game.tags import IsIn, IsPlayer

logger = logging.getLogger(__name__)


def do_player_action(player: tcod.ecs.Entity, action: Action) -> State:
    """Perform an action on the player."""
    assert IsPlayer in player.tags
    if player.components[HP] <= 0:
        return game.states.InGame()
    result = action(player)
    update_fov(player)
    match result:
        case Success(message=message):
            if message:
                add_message(player.registry, message)
            handle_enemy_turns(player.registry, player.relation_tag[IsIn])
        case Poll(state=state):
            return state
        case Impossible(reason=reason):
            add_message(player.registry, reason, fg="impossible")

    if can_level_up(player):
        return game.states.LevelUp()

    return game.states.InGame()


def handle_enemy_turns(world: tcod.ecs.Registry, map_: tcod.ecs.Entity) -> None:
    """Perform enemy turns."""
    for enemy in world.Q.all_of(components=[AI], relations=[(IsIn, map_)]):
        enemy.components[AI](enemy)
