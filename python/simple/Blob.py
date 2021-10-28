from __future__ import annotations
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from lux.game_objects import Player, Unit, City, Position, CityTile


from utility import lowest_city, get_nearest_non_city, get_nearest_city_tile, get_nearest_unoccupied, get_nearest_city, \
    get_nearest_cell, random_direction

import logging
import math
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


class Blob:
    def __init__(self, unit: Unit, player: MyPlayer, actions: List, game_state: Game, resource_tiles: List[Cell]):
        self.unit = unit
        self.player = player
        self.actions = actions
        self.game_state = game_state
        self.resource_tiles = resource_tiles

    def get_resources(self):
        get_resources(self.unit, self.player, self.actions, self.resource_tiles)

    def return_to_city(self):
        return_to_city(self.unit, self.player, self.actions)


def go_to_city(unit: Unit, city: City):
    return unit.move(unit.pos.direction_to(get_nearest_city_tile(unit.pos, city).pos))


def build_city(unit: Unit, game_state: Game) -> str:
    action = None
    if unit.cargo.wood >= 100:
        target_cell = get_nearest_unoccupied(unit.pos, game_state)
        if target_cell.pos.equals(unit.pos):
            logging.info(f'BUILDING!!')
            action = unit.build_city()
        else:
            logging.info(f'Moving {unit.pos.direction_to(target_cell.pos)}')
            pos_target = unit.pos.translate(unit.pos.direction_to(target_cell.pos), 1)
            cell_target = game_state.map.get_cell_by_pos(pos_target)
            if cell_target.citytile or cell_target.has_resource():
                pos_target = get_nearest_non_city(unit.pos, game_state)
                if not pos_target:
                    action = unit.move(random_direction())
                else:
                    action = unit.move(unit.pos.direction_to(target_cell.pos))
            else:
                action = unit.move(unit.pos.direction_to(target_cell.pos))

    else:
        logging.warning('Attempting to build city with not enough resources')
    return action


def get_resources(unit, player, actions, resource_tiles):
    closest_dist = math.inf
    closest_resource_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue

        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile

    if closest_resource_tile is not None:
        actions.append(unit.move(unit.pos.direction_to(closest_resource_tile.pos)))


def return_to_city(unit, player, actions):
    if len(player.cities) > 0:
        closest_dist = math.inf
        closest_city_tile = None
        for k, city in player.cities.items():
            for city_tile in city.citytiles:
                dist = city_tile.pos.distance_to(unit.pos)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_city_tile = city_tile
        if closest_city_tile is not None:
            move_dir = unit.pos.direction_to(closest_city_tile.pos)
            actions.append(unit.move(move_dir))
