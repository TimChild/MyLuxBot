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

blobs = dict()

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
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)

    # we iterate over all our units and do something with them
    for unit in player.units:
        if unit.id not in blobs:
            logging.info(f'New unit {unit.id}')
            blobs[unit.id] = Blob()
        blob = blobs[unit.id]

        blob.update(unit, player, actions, game_state, resource_tiles)
        blob.play()
    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    return actions



if __name__ == '__main__':
    pass
