from Blob import Blob

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


class MyPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.units = Blob(self.units)


