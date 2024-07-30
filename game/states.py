"""Main game states."""

from __future__ import annotations

import attrs
import tcod.console
import tcod.event
from tcod.event import KeySym

import g
from game.action_tools import do_player_action
from game.actions import Bump
from game.constants import DIRECTION_KEYS
from game.rendering import main_render
from game.state import State
from game.tags import IsPlayer


@attrs.define
class ExampleState(State):
    """Example game state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                return do_player_action(self, player, Bump(DIRECTION_KEYS[sym]))
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the current map and entities."""
        main_render(g.world, console)


@attrs.define
class GameOver(State):
    """Game over state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Disables most actions."""
        match event:
            case tcod.event.KeyDown(sym=KeySym.ESCAPE):
                raise SystemExit
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the current map and entities."""
        main_render(g.world, console)
