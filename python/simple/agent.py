import math, sys
import xdrlib

import winsound

from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from lux.game_objects import Player, Unit, City, Position, CityTile

from Player import MyPlayer
from Blob import Blob

import logging
import numpy as np
from itertools import product
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
logging.basicConfig(filename='logs/agent_v1.log', level=logging.DEBUG, filemode='w')

game_state = None

logging.info(f'RANDOM: {random.random()}\n')


def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []


    ### AI Code goes down here! ###
    logging.info(f'Player: {observation.player}, Turn: {game_state.turn}')
    player = game_state.players[observation.player]
    # player = MyPlayer(player)
    opponent = game_state.players[(observation.player + 1) % 2]
    # opponent = MyPlayer(opponent)
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)

    # we iterate over all our units and do something with them
    for unit in player.units:
        blob = Blob(unit, player, actions, game_state, resource_tiles)
        if unit.is_worker() and unit.can_act():
            if unit.get_cargo_space_left() > 0:
                actions.append(annotate.text(unit.pos.x, unit.pos.y, "Getting"))
                # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                blob.get_resources()
            else:
                # # if self is a worker and there is no cargo space left, and we have cities, lets return to them
                blob.return_to_city()


    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    return actions



if __name__ == '__main__':
    pass
