"""Message handling."""

from __future__ import annotations

from typing import Final

import attrs
import tcod.ecs  # noqa: TC002

from . import color


@attrs.define
class Message:
    """A single message."""

    text: str
    fg_color: str
    count: int = 1

    @property
    def fg(self) -> tuple[int, int, int]:
        """Return the  text color."""
        fg: tuple[int, int, int] = getattr(color, self.fg_color)
        return fg

    @property
    def full_text(self) -> str:
        """The full text of this message, including the count if necessary."""
        if self.count > 1:
            return f"{self.text} (x{self.count})"
        return self.text


MessageLog: Final = list[Message]
"""Message log component."""


def add_message(world: tcod.ecs.Registry, text: str, fg: str = "white") -> None:
    """Append a message to the log, stacking is necessary."""
    assert hasattr(color, fg), fg
    log = world[None].components[MessageLog]
    if log and log[-1].text == text:
        log[-1].count += 1
        return
    log.append(Message(text, fg))
