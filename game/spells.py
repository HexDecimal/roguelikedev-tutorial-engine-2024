"""Collection of spell effects."""

from __future__ import annotations

import attrs
from tcod.ecs import Entity  # noqa: TCH002

from game.action import ActionResult, Success
from game.combat import apply_damage
from game.components import Name
from game.messages import add_message


@attrs.define
class LightningBolt:
    """Basic damage spell."""

    damage: int

    def cast_at_entity(self, castor: Entity, _item: Entity | None, target: Entity) -> ActionResult:
        """Damage target."""
        add_message(
            castor.registry,
            f"A lighting bolt strikes the {target.components.get(Name)} with a loud thunder, for {self.damage} damage!",
        )
        apply_damage(target, self.damage)
        return Success()
