"""Main actions."""

from __future__ import annotations

import attrs
import tcod.ecs  # noqa: TCH002

import game.actor_tools
from game.action import ActionResult, Impossible, Success
from game.components import MapShape, Name, Position, Tiles
from game.tags import IsActor
from game.tiles import TILES


@attrs.define
class Move:
    """Move an entity in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> ActionResult:
        """Check and apply the movement."""
        new_position = entity.components[Position] + self.direction
        map_shape = new_position.map.components[MapShape]
        if not (0 <= new_position.x < map_shape.width and 0 <= new_position.y < map_shape.height):
            return Impossible("Out of bounds.")
        if TILES["walk_cost"][new_position.map.components[Tiles][new_position.ij]] == 0:
            return Impossible("Blocked by wall.")
        if entity.world.Q.all_of(tags=[IsActor, new_position]):
            return Impossible("Something is in the way.")  # Blocked by actor

        entity.components[Position] += self.direction
        game.actor_tools.update_fov(entity)
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

        print(f"""You kick the {target.components.get(Name, "?")}, much to its annoyance!""")
        return Success()


@attrs.define
class Bump:
    """Context sensitive action in a direction."""

    direction: tuple[int, int]

    def __call__(self, entity: tcod.ecs.Entity) -> ActionResult:
        """Check and apply the movement."""
        new_position = entity.components[Position] + self.direction
        if entity.world.Q.all_of(tags=[IsActor, new_position]):
            return Melee(self.direction)(entity)
        return Move(self.direction)(entity)
