"""Abstract map data."""

from __future__ import annotations

from typing import Protocol

from tcod.ecs import Entity, Registry  # noqa: TC002


class MapKey(Protocol):
    """Map generation identifier."""

    def generate(self, world: Registry) -> Entity:
        """Generate this map."""
        ...
