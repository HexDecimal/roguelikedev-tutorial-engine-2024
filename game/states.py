"""Main game states."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self

import attrs
import tcod.console
import tcod.constants
import tcod.event
from tcod.ecs import Entity  # noqa: TCH002
from tcod.event import KeySym

import g
from game.action import Action  # noqa: TCH001
from game.action_tools import do_player_action
from game.actions import ApplyItem, Bump, DropItem, PickupItem
from game.components import Name
from game.constants import DIRECTION_KEYS, INVENTORY_KEYS
from game.rendering import main_render
from game.state import State
from game.tags import IsIn, IsItem, IsPlayer


@attrs.define
class ExampleState(State):
    """Example game state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                return do_player_action(self, player, Bump(DIRECTION_KEYS[sym]))
            case tcod.event.KeyDown(sym=KeySym.g):
                return do_player_action(self, player, PickupItem())
            case tcod.event.KeyDown(sym=KeySym.i):
                return ItemSelect.player_verb(self, player, "use", ApplyItem)
            case tcod.event.KeyDown(sym=KeySym.d):
                return ItemSelect.player_verb(self, player, "drop", DropItem)
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the current map and entities."""
        main_render(g.world, console)


@attrs.define
class GameOver(State):
    """Game over state."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Disables most actions."""
        match event:
            case tcod.event.KeyDown(sym=KeySym.ESCAPE):
                raise SystemExit
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the current map and entities."""
        main_render(g.world, console)


@attrs.define(kw_only=True)
class ItemSelect(State):
    """Item selection interface."""

    items: list[Entity]
    title: str = "Select an item"

    pick_callback: Callable[[Entity], State]
    cancel_callback: Callable[[], State] | None = None

    @classmethod
    def player_verb(cls, state: State, player: Entity, verb: str, action: Callable[[Entity], Action]) -> Self:
        """Initialize a common player verb on item menu."""
        return cls(
            title=f"Select an item to {verb}",
            items=list(g.world.Q.all_of(tags=[IsItem], relations=[(IsIn, player)])),
            pick_callback=lambda item: do_player_action(state, player, action(item)),
            cancel_callback=lambda: state,
        )

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle item selection."""
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in {ord(c) for c in INVENTORY_KEYS}:
                index = INVENTORY_KEYS.index(chr(sym))
                if index < len(self.items):
                    return self.pick_callback(self.items[index])
            case tcod.event.KeyDown(sym=KeySym.ESCAPE) if self.cancel_callback is not None:
                return self.cancel_callback()
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the item menu."""
        main_render(g.world, console)

        x = 5
        y = 5
        width = 30
        height = 2 + len(self.items)

        console.draw_frame(x=x, y=y, width=width, height=height, fg=(255, 255, 255), bg=(0, 0, 0))
        if self.title:
            console.print_box(
                x=x,
                y=y,
                width=width,
                height=1,
                string=f" {self.title} ",
                fg=(0, 0, 0),
                bg=(255, 255, 255),
                alignment=tcod.constants.CENTER,
            )
        for i, (item, key_char) in enumerate(zip(self.items, INVENTORY_KEYS, strict=False), start=1):
            console.print(
                x=x + 1, y=y + i, string=f"""{key_char}) {item.components.get(Name, "???")}""", fg=(255, 255, 255)
            )
        footer_rect: dict[str, Any] = {"x": x + 1, "y": y + height - 1, "width": width - 2, "height": 1}
        console.print_box(**footer_rect, string="[a-z] select", fg=(255, 255, 255))
        if self.cancel_callback is not None:
            console.print_box(**footer_rect, string="[esc] cancel", fg=(255, 255, 255), alignment=tcod.constants.RIGHT)
