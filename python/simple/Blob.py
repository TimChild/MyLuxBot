from __future__ import annotations
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from lux.game_objects import Player, Unit, City, Position, CityTile


from utility import lowest_city, get_nearest_non_city, get_nearest_city_tile, get_nearest_unoccupied_cell, get_nearest_city, \
    get_nearest_cell, random_direction, time_left, distance_between

from collections import deque
import logging
import math
import numpy as np
from itertools import product
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from Player import MyPlayer
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DIRECTIONS = Constants.DIRECTIONS
DIRS = [DIRECTIONS.EAST, DIRECTIONS.NORTH, DIRECTIONS.WEST, DIRECTIONS.SOUTH]


class Blob:
    def __init__(self):
        self.unit: Unit = None
        self.player: Player = None
        self.actions: List = None
        self.game_state: Game = None
        self.resource_tiles: List[Cell] = None
        self.occupied_tiles: List[Position] = None

        self.previous_actions = deque([], maxlen=3)
        self.mission: Optional[str] = None

    @property
    def wood(self):
        return self.unit.cargo.wood

    def update(self, unit: Unit, player: Player, actions: List, game_state: Game, resource_tiles: List[Cell], occupied_tiles: List[Position]):
        """Updates with the new turn info"""
        self.unit = unit
        self.player = player
        self.actions = actions
        self.game_state = game_state
        self.resource_tiles = resource_tiles
        self.occupied_tiles = occupied_tiles

    def do_action(self, action):
        """Adds action to actions list, and updates internal store of actions"""
        if action:
            self.actions.append(action)
            self.previous_actions.append(action)

    def log(self, message:str):
        logger.info(f'Blob-{self.unit.id}-{message}')
        self.actions.append(annotate.text(self.unit.pos.x, self.unit.pos.y, message, 26))

    def play(self):
        """Decides best action based on current state and adds it to actions"""
        build_thresh = 5
        immediate_fuel_thresh = 3
        min_wood_thresh = 30

        low_city = lowest_city(self.player.cities)
        if low_city:
            self.actions.append(annotate.sidetext(f'Low-city:{low_city.cityid}:{time_left(low_city):.2f}'))
            dist = distance_between(self.unit.pos, get_nearest_city_tile(self.unit.pos, low_city).pos)
            tl = time_left(low_city)
        else:
            dist = 0
            tl = np.inf
        if self.unit.is_worker() and self.unit.can_act():
            if self.wood == 100 and tl > dist+build_thresh:
                self.build_city()
            elif self.wood > min_wood_thresh and tl < dist+immediate_fuel_thresh and low_city:
                self.log("Fuelling_low_city")
                self.go_to_city(low_city)
            elif self.unit.get_cargo_space_left() > 0:
                self.log("Getting")
                self.get_resources()
            else:
                self.log("Emptying")
                if low_city:
                    self.go_to_city(low_city)
                else:
                    self.log("NothingToDo")

    def get_resources(self):
        action = get_resources(self.unit, self.player, self.resource_tiles)
        if action:
            self.do_action(action)

    def return_to_city(self):
        action = return_to_city(self.unit, self.player)
        return self.do_action(action)

    def build_city(self):
        if self.unit.can_build(self.game_state.map):
            self.log('BUILDING')
            self.do_action(self.unit.build_city())
        else:
            unit = self.unit
            game_state = self.game_state
            target_cell = get_nearest_unoccupied_cell(unit.pos, game_state, self.occupied_tiles)
            if target_cell:
                pos_target = unit.pos.translate(unit.pos.direction_to(target_cell.pos), 1)
                cell_target = game_state.map.get_cell_by_pos(pos_target)
                if cell_target.citytile:
                    self.log('AVOIDING')
                    self.move(random_direction())
                else:
                    self.log('Moving-to-build')
                    self.move(unit.pos.direction_to(target_cell.pos))
            else:
                self.log('STUCK')

    def move(self, direction):
        new_pos = self.unit.pos.translate(direction, 1)
        logging.info(f'{self.unit.id} moving to {new_pos}')
        self.occupied_tiles.append(new_pos)
        return self.do_action(self.unit.move(direction))

    def go_to_city(self, city: City):
        return self.move(self.unit.pos.direction_to(get_nearest_city_tile(self.unit.pos, city).pos))



def get_resources(unit, player, resource_tiles) -> str:
    action = ''
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
        action = unit.move(unit.pos.direction_to(closest_resource_tile.pos))
    return action


def return_to_city(unit, player):
    action = ''
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
            action = unit.move(move_dir)
    return action
