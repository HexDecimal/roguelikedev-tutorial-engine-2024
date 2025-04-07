"""Main actions."""

from __future__ import annotations

from typing import Final, Literal, Self

import attrs
import tcod.ecs  # noqa: TC002

from game.action import ActionResult, Impossible, Success
from game.actor_tools import update_fov
from game.combat import apply_damage, melee_damage
from game.components import EquipSlot, MapShape, Name, Position, Tiles, VisibleTiles
from game.entity_tools import get_name
from game.item import ApplyAction
from game.item_tools import add_to_inventory, equip_item, unequip_item
from game.map import MapKey
from game.map_tools import get_map
from game.messages import add_message
from game.tags import EquippedBy, IsAlive, IsBlocking, IsIn, IsItem, IsPlayer
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
        tile_index = new_position.map.components[Tiles][new_position.ij]
        if TILES["walk_cost"][tile_index] == 0:
            return Impossible(f"""Blocked by {TILES["name"][tile_index]}.""")
        if entity.registry.Q.all_of(tags=[IsBlocking, new_position]):
            return Impossible("Something is in the way.")  # Blocked by entity

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
            (target,) = entity.registry.Q.all_of(tags=[IsAlive, new_position])
        except ValueError:
            return Impossible("Nothing there to attack.")  # No actor at position.

        damage = melee_damage(entity, target)
        attack_color = "player_atk" if IsPlayer in entity.tags else "enemy_atk"
        attack_desc = f"""{entity.components[Name]} attacks {target.components[Name]}"""
        if damage > 0:
            add_message(entity.registry, f"{attack_desc} for {damage} hit points.", attack_color)
            apply_damage(target, damage, blame=entity)
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
        if entity.registry.Q.all_of(tags=[IsAlive, new_position]):
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


@attrs.define
class PickupItem:
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Check for and pickup item."""
        items_here = actor.registry.Q.all_of(tags=[IsItem, actor.components[Position]]).get_entities()
        if not items_here:
            return Impossible("There is nothing here to pick up.")
        item = next(iter(items_here))

        return add_to_inventory(actor, item)


@attrs.define
class ApplyItem:
    """Use an item directly."""

    item: tcod.ecs.Entity

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Defer to items apply behavior."""
        if EquipSlot in self.item.components:
            if EquippedBy in self.item.relation_tag:
                unequip_item(self.item)
                add_message(actor.registry, f"You unequip the {get_name(self.item)}.")
            else:
                equip_item(actor, self.item)
                add_message(actor.registry, f"You equip the {get_name(self.item)}.")
            return Success()
        if ApplyAction in self.item.components:
            return self.item.components[ApplyAction].on_apply(actor, self.item)
        return Impossible(f"""Can not use the {get_name(self.item)}""")


@attrs.define
class DropItem:
    """Place an item on the floor."""

    item: tcod.ecs.Entity

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Drop item from inventory."""
        item = self.item
        assert item.relation_tag[IsIn] is actor
        add_message(actor.registry, f"""You drop the {item.components.get(Name, "?")}!""")
        unequip_item(item)
        del item.relation_tag[IsIn]
        item.components[Position] = actor.components[Position]
        return Success()


@attrs.define
class TakeStairs:
    """Traverse stairs action."""

    dir: Literal["down", "up"]

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Find and traverse stairs for this actor."""
        dir_tag = "DownStairs" if self.dir == "down" else "UpStairs"
        dir_tag_reverse = "DownStairs" if self.dir == "up" else "UpStairs"
        stairs_found = actor.registry.Q.all_of(tags=[actor.components[Position], dir_tag]).get_entities()
        if not stairs_found:
            return Impossible(f"There are no {self.dir}ward stairs here!")

        (stairs,) = stairs_found
        if MapKey not in stairs.components:
            return Impossible("You can not leave yet.")  # Generic description for non-exits for now.

        dir_desc = "descend" if self.dir == "down" else "ascend"
        return MoveLevel(
            dest_map=stairs.components[MapKey],
            exit_tag=(dir_tag_reverse,),
            message=f"""You {dir_desc} the stairs.""",
        )(actor)


@attrs.define
class MoveLevel:
    """Handle level transition."""

    dest_map: MapKey
    exit_tag: tuple[object, ...] = ()
    message: str = ""

    def __call__(self, actor: tcod.ecs.Entity) -> ActionResult:
        """Move actor to the exit passage of the destination map."""
        update_fov(actor, clear=True)

        dest_map = get_map(actor.registry, self.dest_map)
        (dest_stairs,) = actor.registry.Q.all_of(tags=self.exit_tag, relations=[(IsIn, dest_map)]).get_entities()
        add_message(actor.registry, self.message)
        actor.components[Position] = dest_stairs.components[Position]
        return Success()
