"""Mutable global variables."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tcod.console
    import tcod.context
    import tcod.ecs

    import game.state

context: tcod.context.Context
"""The active context."""

console: tcod.console.Console
"""The active console."""

state: game.state.State
"""The active state."""

world: tcod.ecs.Registry
"""The active world."""

cursor_location: tuple[int, int] | None = None
"""Mouse or cursor screen position."""
