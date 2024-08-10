"""World handling functions."""

from __future__ import annotations

import logging
import lzma
import pickle
from pathlib import Path

import tcod.ecs

logger = logging.getLogger(__name__)


def save_world(world: tcod.ecs.Registry, path: Path) -> None:
    """Save the world to a file."""
    data = pickle.dumps(world)
    data = lzma.compress(data)
    path.write_bytes(data)


def load_world(path: Path) -> tcod.ecs.Registry:
    """Return a world loaded from a file."""
    data = path.read_bytes()
    data = lzma.decompress(data)
    world = pickle.loads(data)  # noqa: S301
    assert isinstance(world, tcod.ecs.Registry)
    return world
