"""A collection of effects."""

from __future__ import annotations

import attrs


@attrs.define
class Healing:
    """Healing effect."""

    amount: int
