"""Tools for handing movement."""

from __future__ import annotations

import tcod.ecs
import tcod.path

from game.components import Position, Tiles
from game.tags import IsBlocking, IsIn
from game.tiles import TILES


def path_to(actor: tcod.ecs.Entity, dest: Position) -> list[Position]:
    """Compute and return a path to from actor to dest.

    If there is no valid path then returns an empty list.
    """
    map_ = actor.relation_tag[IsIn]
    assert dest.map is map_

    # Copy the walkable array.
    cost = TILES["walk_cost"][map_.components[Tiles]]

    for other in actor.registry.Q.all_of(tags=[IsBlocking], relations=[(IsIn, map_)]):
        other_pos = other.components[Position]
        # Check that an entity blocks movement and the cost isn't zero (blocking.)
        if cost[other_pos.ij]:
            # Add to the cost of a blocked position.
            # A lower number means more enemies will crowd behind each other in
            # hallways.  A higher number means enemies will take longer paths in
            # order to surround the player.
            cost[other_pos.ij] += 10

    # Create a graph from the cost array and pass that graph to a new pathfinder.
    graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)

    pathfinder.add_root(actor.components[Position].ij)  # Start position.

    # Compute the path to the destination and remove the starting point.
    path: list[list[int]] = pathfinder.path_to(dest.ij)[1:].tolist()

    # Convert from List[List[int]] to List[Tuple[int, int]].
    return [Position(ij_index[1], ij_index[0], map_) for ij_index in path]
