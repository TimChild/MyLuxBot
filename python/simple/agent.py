import math, sys
import xdrlib

import winsound

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
logging.basicConfig(filename='logs/agent_v1.log', encoding='utf-8', level=logging.DEBUG, filemode='w')

DIRECTIONS = Constants.DIRECTIONS
DIRS = [DIRECTIONS.EAST, DIRECTIONS.NORTH, DIRECTIONS.WEST, DIRECTIONS.SOUTH]
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
        if unit.is_worker() and unit.can_act():
            logging.info(f'Wood = {unit.cargo.wood}')
            low_city = lowest_city(player.cities)
            if not low_city:
                low_city = object()
                low_city.cityid = 'NONE'
                low_city.fuel = 100
                low_city.light_upkeep = 1
            logging.info(f'{low_city.cityid}:{low_city.fuel/low_city.light_upkeep}')
            actions.append(annotate.sidetext(f'{low_city.cityid},{low_city.fuel}'))
            if low_city.fuel > 1.5*low_city.light_upkeep and unit.cargo.wood >= 100:
                actions.append(annotate.text(unit.pos.x, unit.pos.y, "Building"))
                actions.append(build_city(unit, game_state))
            elif unit.get_cargo_space_left() > 0:
                actions.append(annotate.text(unit.pos.x, unit.pos.y, "Getting"))
                # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                get_resources(unit, player, actions, resource_tiles)
            elif low_city.fuel/low_city.light_upkeep < 1.5:
                actions.append(annotate.text(unit.pos.x, unit.pos.y, "LOW"))
                actions.append(go_to_city(unit, low_city))
            else:
                actions.append(go_to_city(unit, low_city))
                # actions.append(annotate.text(unit.pos.x, unit.pos.y, "Returning"))
                # # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
                # return_to_city(unit, player, actions)



    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    return actions


# # unitState = UnitState(unit, player, actions, resource_tiles)
# @dataclass
# class UnitState:
#     unit: Unit
#     player: Player
#     actions: List
#     resources: List[Cell]
#

def go_to_city(unit: Unit, city: City):
    return unit.move(unit.pos.direction_to(get_nearest_city_tile(unit.pos, city).pos))


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


def lowest_city(cities: Dict[str, City]) -> City:
    low_city = []
    lowest_val = np.inf
    for k, city in cities.items():
        v = city.fuel/city.light_upkeep
        if v < lowest_val:
            lowest_val = v
            low_city = city
    return low_city



if __name__ == '__main__':
    positions = nearest_positions(Position(5,5))
    for pos in positions:
        print(pos.x, pos.y)