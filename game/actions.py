"""Main actions."""

from __future__ import annotations

from typing import Final, Self

import attrs
import tcod.ecs  # noqa: TCH002

import game.actor_tools
from game.action import ActionResult, Impossible, Success
from game.combat import apply_damage, melee_damage
from game.components import MapShape, Name, Position, Tiles, VisibleTiles
from game.messages import add_message
from game.tags import IsActor, IsIn, IsPlayer
from game.tiles import TILES
from game.travel import path_to


@attrs.define
class Move:
    """Move an entity in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> ActionResult:
        """Check and apply the movement."""
        assert -1 <= self.direction[0] <= 1 and -1 <= self.direction[1] <= 1, self.direction  # noqa: PT018
        if self.direction == (0, 0):
            return wait(entity)
        new_position = entity.components[Position] + self.direction
        map_shape = new_position.map.components[MapShape]
        if not (0 <= new_position.x < map_shape.width and 0 <= new_position.y < map_shape.height):
            return Impossible("Out of bounds.")
        if TILES["walk_cost"][new_position.map.components[Tiles][new_position.ij]] == 0:
            return Impossible("Blocked by wall.")
        if entity.world.Q.all_of(tags=[IsActor, new_position]):
            return Impossible("Something is in the way.")  # Blocked by actor

        if IsPlayer in entity.tags:
            game.actor_tools.update_fov(entity)  # Update ghosts before moving
        entity.components[Position] += self.direction
        return Success()


@attrs.define
class Melee:
    """Attack an entity in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> ActionResult:
        """Check and apply the movement."""
        new_position = entity.components[Position] + self.direction
        try:
            (target,) = entity.world.Q.all_of(tags=[IsActor, new_position])
        except ValueError:
            return Impossible("Nothing there to attack.")  # No actor at position.

        damage = melee_damage(entity, target)
        attack_color = "player_atk" if IsPlayer in entity.tags else "enemy_atk"
        attack_desc = f"""{entity.components[Name]} attacks {target.components[Name]}"""
        if damage > 0:
            add_message(entity.registry, f"{attack_desc} for {damage} hit points.", attack_color)
            apply_damage(target, damage)
        else:
            add_message(entity.registry, f"{attack_desc} but does no damage.", attack_color)

        return Success()


@attrs.define
class Bump:
    """Context sensitive action in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> ActionResult:
        """Check and apply the movement."""
        if self.direction == (0, 0):
            return wait(entity)
        new_position = entity.components[Position] + self.direction
        if entity.world.Q.all_of(tags=[IsActor, new_position]):
            return Melee(self.direction)(entity)
        return Move(self.direction)(entity)


def wait(entity: tcod.ecs.Entity) -> Success:  # noqa: ARG001
    """Do nothing and return successfully."""
    return Success()


@attrs.define
class FollowPath:
    """Follow path action."""

    path: list[Position] = attrs.field(factory=list)

    @classmethod
    def to_dest(cls, actor: tcod.ecs.Entity, dest: Position) -> Self:
        """Path to a destination."""
        return cls(path_to(actor, dest))

    def __bool__(self) -> bool:
        """Return True if a path exists."""
        return bool(self.path)

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Move along the path."""
        if not self.path:
            return Impossible("No path.")
        actor_pos: Final = actor.components[Position]
        dest: Final = self.path.pop(0)
        result = Move((dest.x - actor_pos.x, dest.y - actor_pos.y))(actor)
        if not isinstance(result, Success):
            self.path = []
        return result


@attrs.define
class HostileAI:
    """Generic hostile AI."""

    path: FollowPath = attrs.field(factory=FollowPath)

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Follow and attack player."""
        (target,) = actor.registry.Q.all_of(tags=[IsPlayer])
        actor_pos: Final = actor.components[Position]
        target_pos: Final = target.components[Position]
        map_: Final = actor.relation_tag[IsIn]
        dx: Final = target_pos.x - actor_pos.x
        dy: Final = target_pos.y - actor_pos.y
        distance: Final = max(abs(dx), abs(dy))  # Chebyshev distance.
        if map_.components[VisibleTiles][actor_pos.ij]:
            if distance <= 1:
                return Melee((dx, dy))(actor)
            self.path = FollowPath.to_dest(actor, target_pos)
        if self.path:
            return self.path(actor)
        return wait(actor)
