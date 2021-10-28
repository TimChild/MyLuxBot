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


class MyCity:
    def __init__(self):
        self.city: City = None
        self.player: Player = None
        self.actions: List = None
        self.game_state: Game = None
        self.resource_tiles: List[Cell] = None

        self.previous_actions = deque([], maxlen=3)
        self.mission: Optional[str] = None

    def update(self, city: City, player: Player, actions: List, game_state: Game, resource_tiles: List[Cell]):
        """Updates with the new turn info"""
        self.city = city
        self.player = player
        self.actions = actions
        self.game_state = game_state
        self.resource_tiles = resource_tiles

    def play(self):
        for city_tile in self.city.citytiles:
            if city_tile.can_act() and len(self.player.units) < self.player.city_tile_count:
                self.build_worker(city_tile)
            else:
                pass
                # self.research(city_tile)

    def do_action(self, action):
        """Adds action to actions list, and updates internal store of actions"""
        if action:
            self.actions.append(action)
            self.previous_actions.append(action)

    def build_worker(self, tile: CityTile):
        self.do_action(tile.build_worker())

    def research(self, tile: CityTile):
        self.do_action(tile.research())
