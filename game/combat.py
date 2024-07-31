"""Combat logic."""

from __future__ import annotations

import tcod.ecs

from game.components import AI, HP, Defense, Graphic, Name, Power
from game.messages import add_message
from game.tags import IsPlayer


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
    entity.components.pop(AI)
    del entity.relation_tag[tcod.ecs.IsA]
