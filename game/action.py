"""Action base classes."""

from __future__ import annotations

from typing import Protocol, TypeAlias

import attrs
import tcod.ecs  # noqa: TCH002


@attrs.define
class Success:
    """Action was successful."""


@attrs.define
class Impossible:
    """Action can not be performed."""

    reason: str


ActionResult: TypeAlias = Success | Impossible  # noqa: UP040


class Action(Protocol):
    """Action protocol."""

    def __call__(self, actor: tcod.ecs.Entity, /) -> ActionResult:
        """Perform action."""
