from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from lux.game_objects import Player, Unit, City, Position, CityTile


import logging
import numpy as np
from itertools import product
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from Player import MyPlayer
logging.basicConfig(filename='logs/agent_v1.log', level=logging.DEBUG, filemode='w')

DIRECTIONS = Constants.DIRECTIONS
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


def get_nearest_city_tile(unit_pos: Position, city: City) -> CityTile:
    nearest_tile = None
    nearest_distance = np.inf
    for tile in city.citytiles:
        dist = tile.pos.distance_to(unit_pos)
        if dist < nearest_distance:
            nearest_tile = tile
            nearest_distance = dist
    return nearest_tile


def get_nearest_cell(pos: Position, game_state: Game, condition) -> Optional[Cell]:
    def empty(cell: Cell) -> bool:
        return condition(cell)

    cell = game_state.map.get_cell_by_pos(pos)
    if empty(cell):
        return cell
    else:
        dist = 1
        while dist < 50:
            for pos in nearest_positions(cell.pos, dist):
                if in_map(pos):
                    near_cell = game_state.map.get_cell_by_pos(pos)
                    if empty(near_cell):
                        return near_cell
            dist += 1
    return None


def get_nearest_unoccupied(pos: Position, game_state: Game) -> Optional[Cell]:
    return get_nearest_cell(pos, game_state, condition = lambda cell: not cell.citytile and not cell.has_resource())


def get_nearest_non_city(pos: Position, game_state: Game) -> Optional[Cell]:
    return get_nearest_cell(pos, game_state, condition = lambda cell: not cell.citytile)


def in_map(pos: Position):
    global game_state
    x, y = pos.x, pos.y
    valid = True
    for z, d in zip([x, y], [game_state.map.width, game_state.map.height]):
        if z < 0 or z > d-1:
            valid = False
            break
    return valid


def nearest_positions(pos: Position, dist=1):
    x = [-dist, 0, dist]
    y = [-dist, 0, dist]
    tranlates = set(product(x, y))-{(0, 0)}
    return [Position(pos.x+x, pos.y+y) for x, y in tranlates]


def random_direction():
    v = np.random.randint(low=0, high=4)
    return DIRS[v]


def lowest_city(cities: Dict[str, City]) -> City:
    low_city = []
    lowest_val = np.inf
    for k, city in cities.items():
        v = city.fuel/city.light_upkeep
        if v < lowest_val:
            lowest_val = v
            low_city = city
    return low_city
