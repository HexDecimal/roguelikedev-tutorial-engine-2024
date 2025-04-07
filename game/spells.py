"""Collection of spell effects."""

from __future__ import annotations

import attrs
import numpy as np
import tcod.constants
import tcod.map
from numpy.typing import NDArray  # noqa: TC002
from tcod.ecs import Entity  # noqa: TC002

from game.action import ActionResult, Success
from game.combat import apply_damage
from game.components import HP, MapShape, MemoryTiles, Name, Position, Tiles, VisibleTiles
from game.messages import add_message
from game.tags import IsActor, IsIn
from game.tiles import TILES


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
        apply_damage(target, self.damage, blame=castor)
        return Success()


def get_sphere(shape: tuple[int, int], pos_ij: tuple[int, int], distance_squared: float) -> NDArray[np.bool]:
    """Return a boolean mask in shape of a sphere."""
    height, width = shape
    ii, jj = np.mgrid[:height, :width]
    ii -= pos_ij[0]
    jj -= pos_ij[1]
    ii *= ii
    jj *= jj

    ii += jj
    mask: NDArray[np.bool] = ii <= distance_squared
    return mask


@attrs.define
class SphereAOE:
    """Spell with a circular area of effect."""

    radius: int

    def get_affected_area(self, target: Position, *, player_pov: bool = False) -> NDArray[np.bool]:
        """Return the affected area as a boolean array."""
        if not target.map.components[VisibleTiles][target.ij]:
            return np.zeros(target.map.components[MapShape], dtype=bool)
        return tcod.map.compute_fov(
            TILES["transparent"][target.map.components[Tiles if not player_pov else MemoryTiles]],
            pov=target.ij,
            radius=self.radius,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
        ) & get_sphere(target.map.components[MapShape], target.ij, distance_squared=(self.radius - 0.5) ** 2)


@attrs.define
class Fireball(SphereAOE):
    """Fireball attack."""

    damage: int

    def cast_at_position(self, castor: Entity, _item: Entity | None, target: Position) -> ActionResult:
        """Apply fireball to affected area."""
        affected_area = self.get_affected_area(target)

        targets_hit = False
        for entity in castor.registry.Q.all_of(
            components=[Position, HP], tags=[IsActor], relations=[(IsIn, target.map)]
        ):
            if not affected_area[entity.components[Position].ij]:
                continue
            add_message(
                castor.registry,
                f"""The {entity.components.get(Name, "?")} is engulfed in a fiery explosion, taking {self.damage} damage!""",
            )
            apply_damage(entity, self.damage, blame=castor)
            targets_hit = True

        if not targets_hit:
            add_message(castor.registry, "The fireball misses!")

        return Success()
