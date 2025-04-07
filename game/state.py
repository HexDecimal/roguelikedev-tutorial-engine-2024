"""Abstract state classes."""

from __future__ import annotations

from typing import Protocol

import tcod.console
import tcod.event  # noqa: TC002


class State(Protocol):
    """State protocol."""

    __slots__ = ()

    def on_event(self, event: tcod.event.Event, /) -> State:
        """Handle events."""
        ...

    def on_draw(self, console: tcod.console.Console, /) -> None:
        """Handle drawing."""
        ...
