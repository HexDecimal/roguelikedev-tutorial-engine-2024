"""Main game states."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self

import attrs
import numpy as np  # noqa: TCH002
import tcod.console
import tcod.constants
import tcod.event
from numpy.typing import NDArray  # noqa: TCH002
from tcod import libtcodpy
from tcod.ecs import Entity  # noqa: TCH002
from tcod.event import KeySym, Modifier, Scancode

import g
import game.color
import game.world_init
from game.action import Action  # noqa: TCH001
from game.action_tools import do_player_action
from game.actions import ApplyItem, Bump, DropItem, PickupItem, TakeStairs
from game.components import Name, Position
from game.constants import DIRECTION_KEYS, INVENTORY_KEYS
from game.rendering import main_render
from game.state import State
from game.tags import IsIn, IsItem, IsPlayer


@attrs.define
class InGame(State):
    """In-game main player control state."""

    def on_event(self, event: tcod.event.Event) -> State:  # noqa: C901, PLR0911
        """Handle basic events and movement."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        match event:
            case tcod.event.KeyDown(sym=KeySym.ESCAPE):
                return MainMenu()
            case tcod.event.KeyDown(sym=KeySym.g):
                return do_player_action(player, PickupItem())
            case tcod.event.KeyDown(sym=KeySym.i):
                return ItemSelect.player_verb(player, "use", ApplyItem)
            case tcod.event.KeyDown(sym=KeySym.d):
                return ItemSelect.player_verb(player, "drop", DropItem)
            case tcod.event.KeyDown(sym=KeySym.SLASH):
                return PositionSelect.init_look()
            case tcod.event.KeyDown(sym=KeySym.PERIOD, mod=mod) if mod & Modifier.SHIFT:
                return do_player_action(player, TakeStairs("down"))
            case tcod.event.KeyDown(sym=KeySym.COMMA, mod=mod) if mod & Modifier.SHIFT:
                return do_player_action(player, TakeStairs("up"))
            case tcod.event.KeyDown(scancode=Scancode.NONUSBACKSLASH, mod=mod) if mod & Modifier.SHIFT:
                return do_player_action(player, TakeStairs("down"))
            case tcod.event.KeyDown(scancode=Scancode.NONUSBACKSLASH, mod=mod) if not mod & Modifier.SHIFT:
                return do_player_action(player, TakeStairs("up"))
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                return do_player_action(player, Bump(DIRECTION_KEYS[sym]))
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
    def player_verb(cls, player: Entity, verb: str, action: Callable[[Entity], Action]) -> Self:
        """Initialize a common player verb on item menu."""
        return cls(
            title=f"Select an item to {verb}",
            items=list(g.world.Q.all_of(tags=[IsItem], relations=[(IsIn, player)])),
            pick_callback=lambda item: do_player_action(player, action(item)),
            cancel_callback=InGame,
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


@attrs.define(kw_only=True)
class PositionSelect:
    """Look handler and position pick tool."""

    pick_callback: Callable[[Position], State]
    cancel_callback: Callable[[], State] | None = InGame
    highlighter: Callable[[Position], NDArray[np.bool]] | None = None

    @classmethod
    def init_look(cls) -> Self:
        """Initialize a basic look state."""
        (player,) = g.world.Q.all_of(tags=[IsPlayer])
        g.world["cursor"].components[Position] = player.components[Position]
        return cls(pick_callback=lambda _: InGame(), cancel_callback=InGame)

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle cursor movement and selection."""
        match event:
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                g.world["cursor"].components[Position] += DIRECTION_KEYS[sym]
            case (
                tcod.event.KeyDown(sym=KeySym.RETURN)
                | tcod.event.KeyDown(sym=KeySym.KP_ENTER)
                | tcod.event.MouseButtonDown(button=tcod.event.MouseButton.LEFT)
            ):
                try:
                    return self.pick_callback(g.world["cursor"].components[Position])
                finally:
                    g.world["cursor"].clear()
            case tcod.event.MouseMotion(position=position):
                g.world["cursor"].components[Position] = g.world["cursor"].components[Position].replace(*position)
            case (
                tcod.event.KeyDown(sym=KeySym.ESCAPE)
                | tcod.event.MouseButtonDown(button=tcod.event.MouseButton.RIGHT)
            ) if self.cancel_callback is not None:
                g.world["cursor"].clear()
                return self.cancel_callback()
        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the main screen."""
        highlight = self.highlighter(g.world["cursor"].components[Position]) if self.highlighter is not None else None
        main_render(g.world, console, highlight=highlight)


@attrs.define
class MainMenu:
    """Handle the main menu rendering and input."""

    def on_event(self, event: tcod.event.Event) -> State:
        """Handle menu keys."""
        match event:
            case tcod.event.KeyDown(sym=KeySym.q):
                raise SystemExit
            case tcod.event.KeyDown(sym=KeySym.c | KeySym.ESCAPE):
                if hasattr(g, "world"):
                    return InGame()
            case tcod.event.KeyDown(sym=KeySym.n):
                g.world = game.world_init.new_world()
                return InGame()

        return self

    def on_draw(self, console: tcod.console.Console) -> None:
        """Render the main menu."""
        if hasattr(g, "world"):
            main_render(g.world, console)
            console.rgb["fg"] //= 8
            console.rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg=game.color.menu_title,
            alignment=tcod.constants.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            'By Kyle "HexDecimal" Benesch',
            fg=game.color.menu_title,
            alignment=tcod.constants.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=game.color.menu_text,
                bg=game.color.black,
                alignment=tcod.constants.CENTER,
                bg_blend=libtcodpy.BKGND_ALPHA(64),
            )
