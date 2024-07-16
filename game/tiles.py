"""Tiles database."""

from __future__ import annotations

import numpy as np
import tcod.console

TILES = np.asarray(
    [
        ("wall", (ord("#"), (0x80, 0x80, 0x80), (0x10, 0x10, 0x10)), 0),
        ("floor", (ord("."), (0x40, 0x40, 0x40), (0, 0, 0)), 1),
    ],
    dtype=[
        ("name", object),
        ("graphic", tcod.console.rgb_graphic),
        ("walk_cost", np.int8),
    ],
)
TILES.flags.writeable = False
