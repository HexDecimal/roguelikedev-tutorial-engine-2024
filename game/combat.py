"""Combat logic."""

from __future__ import annotations

import logging

import tcod.ecs  # noqa: TCH002

from game.components import AI, HP, XP, Defense, Graphic, MaxHP, Name, Power, RewardXP
from game.messages import add_message
from game.tags import IsAlive, IsBlocking, IsPlayer

logger = logging.getLogger(__name__)


def melee_damage(entity: tcod.ecs.Entity, target: tcod.ecs.Entity) -> int:
    """Get melee damage for attacking target."""
    return max(0, entity.components.get(Power, 0) - target.components.get(Defense, 0))


def apply_damage(entity: tcod.ecs.Entity, damage: int, blame: tcod.ecs.Entity) -> None:
    """Deal damage to an entity."""
    entity.components[HP] -= damage
    if entity.components[HP] <= 0:
        die(entity, blame)


def die(entity: tcod.ecs.Entity, blame: tcod.ecs.Entity | None) -> None:
    """Kill an entity."""
    is_player = IsPlayer in entity.tags
    add_message(
        entity.registry,
        text="You died!" if is_player else f"{entity.components[Name]} is dead!",
        fg="player_die" if is_player else "enemy_die",
    )
    if blame:
        blame.components.setdefault(XP, 0)
        blame.components[XP] += entity.components.get(RewardXP, 0)
        add_message(
            entity.registry, f"{blame.components[Name]} gains {entity.components.get(RewardXP, 0)} experience points."
        )

    entity.components[Graphic] = Graphic(ord("%"), (191, 0, 0))
    entity.components[Name] = f"remains of {entity.components[Name]}"
    entity.components.pop(AI, None)
    entity.tags.discard(IsBlocking)
    entity.tags.discard(IsAlive)


def heal(entity: tcod.ecs.Entity, amount: int) -> int:
    """Recover the HP of `entity` by `amount`. Return the actual amount restored."""
    if not (entity.components.keys() >= {HP, MaxHP}):
        logger.info("%r has no HP/MaxHP component", entity)
        return 0
    old_hp = entity.components[HP]
    new_hp = min(old_hp + amount, entity.components[MaxHP])
    entity.components[HP] = min(entity.components[HP] + amount, entity.components[MaxHP])
    return new_hp - old_hp
