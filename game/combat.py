"""Combat logic."""

from __future__ import annotations

import logging

import tcod.ecs  # noqa: TCH002

from game.components import AI, HP, Defense, Graphic, MaxHP, Name, Power
from game.messages import add_message
from game.tags import IsActor, IsPlayer

logger = logging.getLogger(__name__)


def melee_damage(entity: tcod.ecs.Entity, target: tcod.ecs.Entity) -> int:
    """Get melee damage for attacking target."""
    return max(0, entity.components.get(Power, 0) - target.components.get(Defense, 0))


def apply_damage(entity: tcod.ecs.Entity, damage: int) -> None:
    """Deal damage to an entity."""
    entity.components[HP] -= damage
    if entity.components[HP] <= 0:
        die(entity)


def die(entity: tcod.ecs.Entity) -> None:
    """Kill an entity."""
    is_player = IsPlayer in entity.tags
    add_message(
        entity.registry,
        text="You died!" if is_player else f"{entity.components[Name]} is dead!",
        fg="player_die" if is_player else "enemy_die",
    )
    entity.components[Graphic] = Graphic(ord("%"), (191, 0, 0))
    entity.components[Name] = f"remains of {entity.components[Name]}"
    entity.components.pop(AI, None)
    entity.tags.remove(IsActor)


def heal(entity: tcod.ecs.Entity, amount: int) -> int:
    """Recover the HP of `entity` by `amount`. Return the actual amount restored."""
    if not (entity.components.keys() >= {HP, MaxHP}):
        logger.info("%r has no HP/MaxHP component", entity)
        return 0
    old_hp = entity.components[HP]
    new_hp = min(old_hp + amount, entity.components[MaxHP])
    entity.components[HP] = min(entity.components[HP] + amount, entity.components[MaxHP])
    return new_hp - old_hp
