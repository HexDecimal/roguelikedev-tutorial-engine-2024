"""Global constants."""

from __future__ import annotations

from typing import Final

from tcod.event import KeySym

DIRECTION_KEYS: Final = {
    # Arrow keys
    KeySym.LEFT: (-1, 0),
    KeySym.RIGHT: (1, 0),
    KeySym.UP: (0, -1),
    KeySym.DOWN: (0, 1),
    # Arrow key diagonals
    KeySym.HOME: (-1, -1),
    KeySym.END: (-1, 1),
    KeySym.PAGEUP: (1, -1),
    KeySym.PAGEDOWN: (1, 1),
    # Keypad
    KeySym.KP_4: (-1, 0),
    KeySym.KP_6: (1, 0),
    KeySym.KP_8: (0, -1),
    KeySym.KP_2: (0, 1),
    KeySym.KP_7: (-1, -1),
    KeySym.KP_1: (-1, 1),
    KeySym.KP_9: (1, -1),
    KeySym.KP_3: (1, 1),
    KeySym.KP_5: (0, 0),
    # VI keys
    KeySym.H: (-1, 0),
    KeySym.L: (1, 0),
    KeySym.K: (0, -1),
    KeySym.J: (0, 1),
    KeySym.Y: (-1, -1),
    KeySym.B: (-1, 1),
    KeySym.U: (1, -1),
    KeySym.N: (1, 1),
    KeySym.PERIOD: (0, 0),
}

INVENTORY_KEYS = "abcdefghijklmnopqrstuvwxyz"
