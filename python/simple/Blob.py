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
from typing import List, Dict, Optional
logging.basicConfig(filename='logs/agent_v1.log', level=logging.DEBUG, filemode='w')


DIRECTIONS = Constants.DIRECTIONS
DIRS = [DIRECTIONS.EAST, DIRECTIONS.NORTH, DIRECTIONS.WEST, DIRECTIONS.SOUTH]


class Blob(Unit):
    def __init__(self, actions: List, game_state: Game, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = actions
        self.game_state = game_state

    def play(self):
        if self.is_worker() and self.can_act():
            logging.info(f'Wood = {self.cargo.wood}')
            low_city = lowest_city(player.cities)
            if not low_city:
                low_city = object()
                low_city.cityid = 'NONE'
                low_city.fuel = 100
                low_city.light_upkeep = 1
            logging.info(f'{low_city.cityid}:{low_city.fuel/low_city.light_upkeep}')
            self.actions.append(annotate.sidetext(f'{low_city.cityid},{low_city.fuel}'))
            if low_city.fuel > 1.5*low_city.light_upkeep and self.cargo.wood >= 100:
                self.actions.append(annotate.text(self.pos.x, self.pos.y, "Building"))
                self.actions.append(self.build_city(self, game_state))
            elif self.get_cargo_space_left() > 0:
                self.actions.append(annotate.text(self.pos.x, self.pos.y, "Getting"))
                # if the self is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                get_resources(self, player, self.actions, resource_tiles)
            elif low_city.fuel/low_city.light_upkeep < 1.5:
                self.actions.append(annotate.text(self.pos.x, self.pos.y, "LOW"))
                self.actions.append(go_to_city(self, low_city))
            else:
                self.actions.append(go_to_city(self, low_city))
                # self.actions.append(annotate.text(self.pos.x, self.pos.y, "Returning"))
                # # if self is a worker and there is no cargo space left, and we have cities, lets return to them
                # return_to_city(self, player, actions)
