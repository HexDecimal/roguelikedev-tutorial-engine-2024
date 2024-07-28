"""Action base classes."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import attrs
import tcod.ecs


@attrs.define
class Success:
    """Action was successful."""


@attrs.define
class Impossible:
    """Action can not be performed."""

    reason: str


ActionResult: TypeAlias = Success | Impossible  # noqa: UP040

Action: TypeAlias = Callable[[tcod.ecs.Entity], ActionResult]  # noqa: UP040
