from __future__ import annotations
from luxai2021.game.game import Game, GameMap
from luxai2021.game.game_map import Cell, RESOURCE_TYPES
from luxai2021.game.constants import Constants as C
from luxai2021.game.unit import Unit
from luxai2021.game.city import City, CityTile
from luxai2021.game.position import Position

import logging
import numpy as np
from itertools import product
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from component_classes import MyUnit, MyCity, MyState

import pathfinding

DIRECTIONS = C.DIRECTIONS
DIRS = [DIRECTIONS.EAST, DIRECTIONS.NORTH, DIRECTIONS.WEST, DIRECTIONS.SOUTH]


def get_nearest_city(unit_pos: Position, cities: Dict[str, City]) -> CityTile:
    nearest_tile = None
    nearest_distance = np.inf
    for k, city in cities.items():
        nearest = get_nearest_city_tile(unit_pos, city)
        dist = unit_pos.distance_to(nearest.pos)
        if dist < nearest_distance:
            nearest_tile = nearest
            nearest_distance = dist
    return nearest_tile


def get_nearest_city_tile(unit_pos: Position, city: MyCity) -> Optional[CityTile]:
    nearest_tile = None
    nearest_distance = np.inf
    for tile in city.tiles:
        dist = tile.pos.distance_to(unit_pos)
        if dist < nearest_distance:
            nearest_tile = tile
            nearest_distance = dist
    if nearest_tile:
        return nearest_tile.city_tile
    else:
        return None


def get_nearest_cell(pos: Position, game_state: Game, occupied_tiles: List[Position], condition) -> Optional[Cell]:
    def empty(cell: Cell) -> bool:
        if cell.pos in occupied_tiles or not condition(cell):
            return False
        return True

    cell = game_state.map.get_cell_by_pos(pos)
    if empty(cell):
        return cell
    else:
        dist = 1
        while dist < 3:
            for pos in nearest_positions(cell.pos, dist):
                if in_map(pos, game_state):
                    near_cell = game_state.map.get_cell_by_pos(pos)
                    if empty(near_cell):
                        return near_cell
            dist += 1
    return None


def get_nearest_unoccupied_cell(pos: Position, game_state: Game, occupied_tiles: List[Position]) -> Optional[Cell]:
    return get_nearest_cell(pos, game_state, occupied_tiles,
                            condition=lambda cell: not cell.city_tile and not cell.has_resource())
#
#
# def get_nearest_non_city(pos: Position, game_state: Game, occupied_tiles: List[Position]) -> Optional[Cell]:
#     return get_nearest_cell(pos, game_state, occupied_tiles, condition=lambda cell: not cell.city_tile)


def in_map(pos: Position, game_state):
    x, y = pos.x, pos.y
    valid = True
    for z, d in zip([x, y], [game_state.map.width, game_state.map.height]):
        if z < 0 or z > d - 1:
            valid = False
            break
    return valid


def nearest_positions(pos: Position, dist=1):
    # TODO: replace with game.map.get_adjacent_cells(unit)
    translates = ((-1, 0), (0, 1), (1, 0), (0, -1))
    if dist == 1:
        pass
    elif dist == 2:
        x = [-dist, 0, dist]
        y = [-dist, 0, dist]
        translates = set(product(x, y)) - {(0, 0)} - set(translates)
    else:
        raise NotImplemented
    return [Position(pos.x + x, pos.y + y) for x, y in translates]


def random_direction():
    v = np.random.randint(low=0, high=4)
    return DIRS[v]


def lowest_city(cities: Dict[str, MyCity]) -> MyCity:
    low_city = None
    lowest_val = np.inf
    for k, city in cities.items():
        v = time_left(city)
        if v < lowest_val:
            lowest_val = v
            low_city = city
    return low_city


def time_left(city: Optional[MyCity]) -> float:
    if city is None:
        return np.inf
    return city.city.fuel / city.city.get_light_upkeep()


def distance_between(pos1: Position, pos2: Position):
    return pos1.distance_to(pos2)


def get_nearest_resource(map: GameMap, pos: Position, resource_type = C.RESOURCE_TYPES.WOOD) -> Cell:
    closest_tile = None
    closest_dist = np.inf
    for tile in map.resources_by_type[resource_type]:
        dist = pos.distance_to(tile.pos)

        if dist < closest_dist:
            closest_dist = dist
            closest_tile = tile
    return closest_tile


def units_at_position(pos: Position, units: List[MyUnit]) -> List[MyUnit]:
    current_units = []
    for unit in units:
        if pos.distance_to(unit.pos) == 0:
            current_units.append(unit)
    return current_units


def get_path(start: Position, end: Position, matrix_map: np.ndarray) -> List[Position]:
    """
    Get path from start to finish avoiding obstacles
    https://pypi.org/project/pathfinding/

    Args:
        start (): Start position
        end (): End position
        matrix_map (): Map in array where <= 0 means impassible, and > 0 is cost to travel

    Returns:
        Path from start to finish (including both) or an empty list if no path can be found
    """
    from pathfinding.core.grid import Grid
    from pathfinding.finder.a_star import AStarFinder

    grid = Grid(matrix=matrix_map)
    start = grid.node(start.x, start.y)
    end = grid.node(end.x, end.y)

    finder = AStarFinder()
    path, runs = finder.find_path(start, end, grid)
    path = [Position(p[0], p[1]) for p in path]
    return path


def get_matrix_map(map: GameMap, all_cities: List[MyCity], all_units: List[MyUnit], team: int, avoid_cities=False,
                   road_cost=1) -> np.ndarray:
    """
    Convert GameMap into a map for pathfinding

    Args:
        map ():
        all_cities (): All cities on the map
        all_units (): All units on the map
        team (): To figure out which city cells are impassable
        avoid_cities ():  Whether to avoid own cities (i.e. if don't want to accidentally drop off resources)
        road_cost (): the cost to travel by road tile, the lower the cost the more it is prioritized

    Returns:

    """
    state_map = np.array(map.to_state_object())  # Includes resources and roads but not cities or units
    matrix_map = np.ones(state_map.shape)*5  # Start with all cells having move weight of 1

    # resources aren't in the way, so for now just leave those cells with 1
    for y, row in enumerate(state_map):
        for x, info in enumerate(row):
            if info:
                if 'road' in info:
                    if info['road'] >= 0:
                        matrix_map[y, x] = road_cost

    for city in all_cities:
        if avoid_cities or city.team != team:
            for tile in city.tiles:
                pos = tile.pos
                matrix_map[pos.y, pos.x] = 0  # Mark impassable

    #
    for unit in all_units:
        unit_pos = unit.next_pos if unit.next_pos else unit.pos
        if map.get_cell_by_pos(unit_pos).is_city_tile() and unit.team == team:
            pass  # Allowed to share city tile on same team
        else:
            matrix_map[unit_pos.y, unit_pos.x] = 1  # Mark impassable

    return matrix_map


if __name__ == '__main__':
    pass
