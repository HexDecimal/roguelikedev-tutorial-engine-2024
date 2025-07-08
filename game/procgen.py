"""Procedural generation tools."""

from __future__ import annotations

import bisect
import itertools
from collections.abc import Iterable, Iterator, Sequence
from random import Random
from typing import Final, Self, TypedDict

import attrs
import numpy as np
import tcod.ecs
import tcod.los
from numpy.typing import NDArray  # noqa: TC002

import game.map_tools
from game.actions import HostileAI
from game.actor_tools import spawn_actor
from game.components import AI, Floor, Graphic, Position, SpawnWeight, Tiles
from game.item_tools import spawn_item
from game.map import MapKey
from game.tags import IsActor, IsItem
from game.tiles import TILE_NAMES

max_items_by_floor = (
    (1, 1),
    (4, 2),
)
"""(floor, max_items)"""

max_monsters_by_floor = (
    (1, 2),
    (4, 3),
    (6, 5),
)
"""(floor, max_monsters)"""


def get_value_for_floor(floor_table: Sequence[tuple[int, int]], floor: int) -> int:
    """Return the value from a table of ((min_floor, value), ...) items."""
    i = bisect.bisect_right(floor_table, floor, key=lambda item: item[0])
    if i:
        return floor_table[i - 1][1]
    return 0


class RandomChoices(TypedDict):
    """Parameters for random.choices."""

    population: Sequence[tcod.ecs.Entity]
    weights: Sequence[float]


def get_template_weights(
    templates: Iterable[tcod.ecs.Entity],
    floor: int,
) -> RandomChoices:
    """Return a select of entities at random based on their weights."""
    population = []
    choice_weights = []
    for template in templates:
        weight = get_value_for_floor(template.components.get(SpawnWeight, ()), floor)
        if not weight:
            continue
        population.append(template)
        choice_weights.append(weight)

    assert population
    return RandomChoices(population=population, weights=choice_weights)


@attrs.define
class RectangularRoom:
    """A simple rectangular room."""

    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_rect(cls, x: int, y: int, width: int, height: int) -> Self:
        """Return a new room from a simple rect."""
        return cls(x, y, x + width, y + height)

    @classmethod
    def from_center(cls, x: int, y: int, width: int, height: int) -> Self:
        """Return a new room centered on a position."""
        x -= width // 2
        y -= height // 2
        return cls.from_rect(x, y, width, height)

    @property
    def center(self) -> tuple[int, int]:
        """Return the center coordinate of the room."""
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    @property
    def center_ij(self) -> tuple[int, int]:
        """Return the center coordinate of the room."""
        return (self.y1 + self.y2) // 2, (self.x1 + self.x2) // 2

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.y1 + 1, self.y2), slice(self.x1 + 1, self.x2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1

    def distance_to(self, other: RectangularRoom) -> int:
        """Return a distance between this room and other."""
        x, y = self.center
        x2, y2 = other.center
        return abs(x - x2) + abs(y - y2)

    def iter_random_spaces(self, rng: Random, map_: tcod.ecs.Entity) -> Iterator[Position]:
        """Iterate over floor spaces which do not already have an entity."""
        spaces = list(itertools.product(range(self.x1 + 1, self.x2 - 1), range(self.y1 + 1, self.y2 - 1)))
        world = map_.registry
        rng.shuffle(spaces)
        for x, y in spaces:
            pos = Position(x, y, map_)
            if world.Q.all_of(tags=[pos]):
                continue  # Space already taken.
            yield pos


def random_walk_iter(rng: Random, start: tuple[int, int], space: tuple[int, int]) -> Iterator[tuple[int, int]]:
    """Iterate over the coordinates of a random walk."""
    dirs: Final = ((1, 0), (-1, 0), (0, 1), (0, -1))
    x, y = start
    x = max(0, min(x, space[0] - 1))
    y = max(0, min(y, space[1] - 1))
    while True:
        dx, dy = rng.choice(dirs)
        next_x = x + dx
        next_y = y + dy
        if 0 <= next_x < space[0] and 0 <= next_y < space[1]:
            x = next_x
            y = next_y
            yield x, y


def tunnel_between_indices(
    rng: Random, start: tuple[int, int], end: tuple[int, int]
) -> tuple[NDArray[np.intc], NDArray[np.intc]]:
    """Return the indexes of a tunnel between two points."""
    x1, y1 = start
    x2, y2 = end
    if rng.random() < 0.5:  # noqa: PLR2004
        corner_x, corner_y = x2, y1
    else:
        corner_x, corner_y = x1, y2
    tunnel: NDArray[np.intc] = np.vstack(
        (tcod.los.bresenham((x1, y1), (corner_x, corner_y)), tcod.los.bresenham((corner_x, corner_y), (x2, y2))[1:])
    )
    return tuple(tunnel.T)  # type: ignore[return-value]


def generate_dungeon(  # noqa: C901
    *,
    world: tcod.ecs.Registry,
    shape: tuple[int, int],
    max_rooms: int = 20,
    room_min_size: int = 6,
    room_max_size: int = 10,
    max_iterations: int = 100_000,
    floor: int,
) -> tcod.ecs.Entity:
    """Return a new generated map."""
    max_monsters_per_room: Final = get_value_for_floor(max_monsters_by_floor, floor)
    max_items_per_room: Final = get_value_for_floor(max_items_by_floor, floor)
    monster_weights: Final = get_template_weights(
        world.Q.all_of(components=[SpawnWeight], tags=[IsActor], depth=0), floor
    )
    item_weights: Final = get_template_weights(world.Q.all_of(components=[SpawnWeight], tags=[IsItem], depth=0), floor)
    map_height, map_width = shape
    map_ = game.map_tools.new_map(world, shape)
    map_.components[Floor] = floor
    map_tiles = map_.components[Tiles]
    map_tiles[:] = TILE_NAMES["wall"]
    rng = world[None].components[Random]

    room_width = rng.randint(room_min_size, room_max_size)
    room_height = rng.randint(room_min_size, room_max_size)
    rooms: list[RectangularRoom] = []
    rooms.append(
        RectangularRoom.from_rect(
            rng.randint(0, map_width - room_width), rng.randint(0, map_height - room_height), room_width, room_height
        )
    )
    map_tiles[rooms[-1].inner] = TILE_NAMES["floor"]

    for _ in range(max_rooms):
        from_room = rng.choice(rooms)
        room_width = rng.randint(room_min_size, room_max_size)
        room_height = rng.randint(room_min_size, room_max_size)
        for x, y in random_walk_iter(
            rng, (from_room.x1, from_room.y1), (map_width - room_width, map_height - room_height)
        ):
            if max_iterations <= 0:
                break
            max_iterations -= 1
            if __debug__ and max_iterations % 100 == 0:
                print(f"\r{max_iterations=} ", end="")

            new_room = RectangularRoom.from_rect(x, y, room_width, room_height)
            if any(new_room.intersects(room) for room in rooms):
                continue

            nearest_room = min(rooms, key=new_room.distance_to)
            map_tiles[new_room.inner] = TILE_NAMES["floor"]
            map_tiles[tunnel_between_indices(rng, nearest_room.center_ij, new_room.center_ij)] = TILE_NAMES["floor"]

            rooms.append(new_room)
            break

    # Join random rooms
    for _ in range(2):
        room_a, room_b = rng.sample(rooms, 2)
        map_tiles[tunnel_between_indices(rng, room_a.center_ij, room_b.center_ij)] = TILE_NAMES["floor"]

    up_stairs = world[object()]
    up_stairs.components[Position] = next(rooms[0].iter_random_spaces(rng, map_))
    up_stairs.components[Graphic] = Graphic(ord("<"), (255, 255, 255))
    up_stairs.tags.add("UpStairs")
    if floor > 1:
        up_stairs.components[MapKey] = Tombs(level=floor - 1)

    down_stairs = world[object()]
    down_stairs.components[Position] = next(rooms[-1].iter_random_spaces(rng, map_))
    down_stairs.components[Graphic] = Graphic(ord(">"), (255, 255, 255))
    down_stairs.tags.add("DownStairs")
    down_stairs.components[MapKey] = Tombs(level=floor + 1)

    for room in rooms[1:-1]:
        for monster_kind, pos in zip(
            rng.choices(**monster_weights, k=rng.randint(0, max_monsters_per_room)),
            room.iter_random_spaces(rng, map_),
            strict=False,
        ):
            new_monster = spawn_actor(monster_kind, pos)
            new_monster.components[AI] = HostileAI()

        for item_kind, pos in zip(
            rng.choices(**item_weights, k=rng.randint(0, max_items_per_room)),
            room.iter_random_spaces(rng, map_),
            strict=False,
        ):
            spawn_item(item_kind, pos)

    return map_


@attrs.define(frozen=True)
class Tombs:
    """The tombs."""

    level: int

    def generate(self, world: tcod.ecs.Registry) -> tcod.ecs.Entity:
        """Generate the tombs."""
        return generate_dungeon(world=world, shape=(45, 80), floor=self.level)
