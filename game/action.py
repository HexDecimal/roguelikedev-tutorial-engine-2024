"""Action base classes."""

from __future__ import annotations

from typing import Protocol, TypeAlias

import attrs
from tcod.ecs import Entity  # noqa: TC002

from game.state import State  # noqa: TC001


@attrs.define
class Success:
    """Action was successful."""

    message: str = ""
    """Message displayed when this result returns."""


@attrs.define
class Poll:
    """Action needs more input from the user."""

    state: State


@attrs.define
class Impossible:
    """Action can not be performed."""

    reason: str


ActionResult: TypeAlias = Success | Poll | Impossible  # noqa: UP040


class Action(Protocol):
    """Action protocol."""

    def __call__(self, actor: Entity, /) -> ActionResult:
        """Perform action."""
        ...
