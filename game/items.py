"""Item-based verb behavior."""

from __future__ import annotations

import functools

import attrs
from tcod.ecs import Entity  # noqa: TC002

import game.states
from game.action import ActionResult, Impossible, Poll, Success
from game.action_tools import do_player_action
from game.components import Position, VisibleTiles
from game.effect import Effect
from game.entity_tools import get_name
from game.item_tools import consume_item
from game.messages import add_message
from game.spell import AreaOfEffect, EntitySpell, PositionSpell
from game.tags import IsActor, IsIn


@attrs.define
class Potion:
    """Drinkable potion."""

    def on_apply(self, actor: Entity, item: Entity) -> ActionResult:
        """Consume the item and apply its effect."""
        add_message(actor.registry, f"""You consume the {get_name(item)}!""")
        if Effect in item.components:
            item.components[Effect].affect(actor)
        consume_item(item)
        return Success()


@attrs.define
class RandomTargetScroll:
    """One-use scroll targeting the nearest enemy."""

    maximum_range: int

    def on_apply(self, actor: Entity, item: Entity) -> ActionResult:
        """Cast items spell at nearest target in range."""
        actor_pos = actor.components[Position]
        possible_targets = actor.registry.Q.all_of(
            components=[Position], tags=[IsActor], relations=[(IsIn, actor_pos.map)]
        ).get_entities() - {actor}

        visible_map = actor_pos.map.components[VisibleTiles]
        visible_targets = [entity for entity in possible_targets if visible_map[entity.components[Position].ij]]
        if not visible_targets:
            return Impossible("No target visible.")

        target = min(visible_targets, key=lambda entity: actor_pos.distance_squared(entity.components[Position]))
        if actor_pos.distance_squared(target.components[Position]) > self.maximum_range**2:
            return Impossible("No target in range.")

        result = item.components[EntitySpell].cast_at_entity(actor, item, target)
        if result:
            consume_item(item)
        return result


@attrs.define
class TargetScroll:
    """One-use scroll with a manual target."""

    def on_apply(self, actor: Entity, item: Entity, target: Position | None = None) -> ActionResult:
        """Cast items spell at nearest target in range."""
        spell = item.components[PositionSpell]
        highlighter = (
            functools.partial(spell.get_affected_area, player_pov=True) if isinstance(spell, AreaOfEffect) else None
        )
        if target is None:
            actor.registry["cursor"].components[Position] = actor.components[Position]
            return Poll(
                game.states.PositionSelect(
                    pick_callback=lambda pos: do_player_action(actor, lambda actor: self.on_apply(actor, item, pos)),
                    highlighter=highlighter,
                )
            )

        if not actor.components[Position].map.components[VisibleTiles][target.ij]:
            return Impossible("Target is out of view.")

        result = item.components[PositionSpell].cast_at_position(actor, item, target)
        if result:
            item.clear()
        return result
