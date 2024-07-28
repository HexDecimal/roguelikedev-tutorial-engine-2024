"""Action functions."""

from __future__ import annotations

import tcod.ecs  # noqa: TCH002

from game.action import Action  # noqa: TCH001
from game.state import State  # noqa: TCH001


def do_player_action(state: State, entity: tcod.ecs.Entity, action: Action) -> State:
    """Perform an action on the player."""
    _result = action(entity)
    return state
