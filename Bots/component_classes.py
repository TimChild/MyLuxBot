from __future__ import annotations
from collections import deque
from typing import Dict, List, Optional, Deque

import numpy as np
from luxai2021.game import actions as act
from luxai2021.game.cell import Cell
from luxai2021.game.city import City
from luxai2021.game.constants import Constants as C
from luxai2021.game.game import Game
from luxai2021.game.position import Position
from luxai2021.game.unit import Unit

from Bots import utility as util


class MyState:
    def __init__(self, game: Game, team):
        self.game = game
        self.team = team
        self.turn = 0
        self.night = 0
        self.logging = True

        self._occupied = []
        self._cities = {}
        self._all_units = {}

    def update(self, game):
        self.game = game
        self.turn = game.state['turn']
        self.night = game.is_night()
        self._cities = {}
        self._all_units = {}

    @property
    def map(self):
        return self.game.map

    @property
    def worker_cap_reached(self):
        return self.game.worker_unit_cap_reached(self.team)

    @property
    def units(self) -> Dict[str, MyUnit]:
        return {k: v for k, v in self.all_units.items() if v.team == self.team}

    @property
    def all_units(self) -> Dict[str, MyUnit]:
        if not self._all_units:
            self._all_units = dict(**self.game.state["teamStates"][0]["units"], **self.game.state["teamStates"][1]["units"])
            self._all_units = {k: MyUnit(v, v.team, self) for k, v in self._all_units.items()}
        return self._all_units

    @property
    def cities(self) -> Dict[str, MyCity]:
        return {k: v for k, v in self.all_cities.items() if v.team == self.team}

    @property
    def all_cities(self) -> Dict[str, MyCity]:
        if not self._cities:
            for k, city in self.game.cities.items():
                city = MyCity(city, city.team, self)
                self._cities[k] = city
        return self._cities

    def lowest_city(self):
        """Returns city with lowest fuel"""
        cities = self.cities
        return util.lowest_city(cities)

    @property
    def occupied_tiles(self) -> List[Position]:
        if not self._occupied:
            cities = self.all_cities
            units = self.all_units
            resources = self.game.map.resources
            occupied = []
            for city in cities.values():
                for tile in city.tiles:
                    occupied.append(tile.pos)
            for unit in units.values():
                pos = unit.next_pos if unit.next_pos else unit.pos
                occupied.append(pos)
            for resource in resources:
                occupied.append(resource.pos)
            self._occupied = occupied
        return self._occupied

    def add_to_occupied(self, pos: Position):
        if pos not in self._occupied:
            self._occupied.append(pos)
        else:
            self.log(f'Trying to add {pos} to occupied, but already there')

    def remove_from_occupied(self, pos: Position):
        if pos in self._occupied:
            self._occupied.remove(pos)
        else:
            self.log(f'Tried to remove {pos} from occupied which wasn\'t in occupied')

    def log(self, message):
        if self.logging:
            print(message)


class MyCity:
    def __init__(self, city: City, team: int, game_state: MyState):
        self.city = city
        self.id = self.city.id
        self.tiles: List[Cell] = self.city.city_cells
        self.game_state = game_state
        self.team = team

        self.previous_actions = deque(maxlen=3)
        self.logging = True

    def update(self, game_state: MyState):
        if self.team != game_state.team:
            raise ValueError
        self.game_state = game_state
        self.tiles = self.city.city_cells

    def self_action(self) -> List[act.Action]:
        """Have city decide what action to take"""
        fuel_buffer = 10  # How many days of fuel should be reserved

        actions = []
        action = None
        for tile in self.tiles:
            tile = tile.city_tile
            if tile.can_act():
                if util.time_left(self) > fuel_buffer and not self.game_state.night and not self.game_state.worker_cap_reached:
                    self.log('Spawning worker')
                    action = self.do_action(act.SpawnWorkerAction(self.game_state.team, tile.city_id, tile.pos.x, tile.pos.y))
                elif tile.can_research():
                    self.log('Doing research')
                    action = self.do_action(act.ResearchAction(self.game_state.team, tile.pos.x, tile.pos.y, tile.city_id))
                else:
                    self.log('Nothing to do')
                if action:
                    actions.append(action)
        #         units = units_at_position(tile.pos, self.units)
        #         if self.game_state.night and units:
        #             for unit in units:
        return actions

    def do_action(self, action: act.Action) -> act.Action:
        if action:
            self.previous_actions.append(action)
        else:
            self.log('tried to do no action')
        return action

    def log(self, message: str):
        if self.logging:
            print(f'City {self.id}: {message}')


class MyUnit:
    def __init__(self, unit: Unit, team: int, game_state: MyState):
        self.unit = unit
        self.id = unit.id
        self.pos = unit.pos
        self.previous_actions = deque([], maxlen=3)
        self.game_state = game_state
        self.team = team

        self.current_mission = None  # Stores current intention of unit
        self.next_pos: Optional[Position] = None  # For storing destination if moving
        self.logging = True

        self._move_queue: Deque = None

    def update(self, game_state: MyState):
        """To be called at the beginning of turn"""
        if self.team != game_state.team:
            raise ValueError
        self.game_state = game_state
        self.pos = self.unit.pos
        self.next_pos = None

    def continue_mission(self):
        # TODO: This
        if self.current_mission == 'moving':
            # self._move_queue.popleft
            self.move_to()
        elif self.current_mission == 'building':
            self.build_city()
        else:
            pass

    def self_action(self):
        """Have unit decide what action to take"""
        build_thresh = 15
        immediate_fuel_thresh = 3
        min_wood_thresh = 30
        night_buffer = 20  # Consider cargo full if > Max - night_loss

        low_city = self.game_state.lowest_city()

        if low_city:
            dist = util.distance_between(self.unit.pos, util.get_nearest_city_tile(self.unit.pos, low_city).pos)
            tl = util.time_left(low_city)
        else:
            dist = 0
            tl = np.inf
        action = None
        if self.unit.is_worker() and self.can_act():
            # if self.current_mission:  # TODO: Finish this
            #     self.continue_mission()

            if self.wood == 100 and not self.game_state.night and tl > dist+build_thresh:
                action = self.build_city()
            # elif self.wood > min_wood_thresh and tl < dist+immediate_fuel_thresh and low_city:
            #     self.log("Fuelling_low_city")
            #     self.go_to_city(low_city)
            elif self.unit.get_cargo_space_left() > 0 + self.game_state.night*night_buffer:
                self.log("Getting")
                action = self.get_resources()
            else:
                if low_city:
                    action = self.go_to_city(low_city)
                    # action = self.transfer_to_city(low_city, C.RESOURCE_TYPES.WOOD, keep=night_buffer*self.game_state.night)
                else:
                    self.log("NothingToDo")
                    action = self.move(C.DIRECTIONS.CENTER)
        return action

    # Actions
    def do_action(self, action: act.Action) -> act.Action:
        """All actions should be returned through this"""
        self.previous_actions.append(action)
        return action

    def move(self, direction) -> act.Action:
        """Basic move in direction"""
        if direction in {C.DIRECTIONS.NORTH, C.DIRECTIONS.SOUTH, C.DIRECTIONS.EAST, C.DIRECTIONS.WEST, C.DIRECTIONS.CENTER}:
            action = act.MoveAction(self.unit.team, self.id, direction)
            new_pos = self.unit.pos.translate(direction, 1)
            self.next_pos = new_pos
            self.game_state.add_to_occupied(self.next_pos)
            self.game_state.remove_from_occupied(self.pos)
        else:
            print(f'Asked for invalid move: {direction}')
            action = act.MoveAction(self.unit.team, self.id, C.DIRECTIONS.CENTER)
        return self.do_action(action)

    def move_to(self, position: Position, avoid_cities = False) -> act.Action:
        """Move to a new location"""
        self.current_mission = 'moving'
        action = None
        matrix_map = util.get_matrix_map(
            self.game_state.map,
            list(self.game_state.all_cities.values()),
            list(self.game_state.all_units.values()),
            self.team,
            avoid_cities=avoid_cities, road_cost=1)
        new_path = util.get_path(self.pos, position, matrix_map)
        self.log(f'Path from {self.pos} to {position}: {new_path}')

        if len(new_path) == 0:
            self.log(f'No path from {self.pos} to {position}')
            action = self.move(C.DIRECTIONS.CENTER)
        elif len(new_path) == 1:
            self.current_mission = ''
            self.log('Already at desired position')
            action = self.move(C.DIRECTIONS.CENTER)
        else:
            self._move_queue = deque(new_path[1:])
            self.log(f'Progressing towards {position}')
            x, y = new_path[1]
            action = self.move(self.pos.direction_to(Position(x, y)))
        return action

    def go_to_city(self, city):
        return self.move_to(util.get_nearest_city_tile(self.pos, city).pos, avoid_cities=False)  # TODO: Probably do want to avoid other cities on the way there.
        # return self.move(self.unit.pos.direction_to(util.get_nearest_city_tile(self.unit.pos, city).pos))

    # def transfer_to_city(self, city: City, resource_type, keep=0):
    #     """Try to transfer resources to a city (or move towards the city)
    #     If keep != 0 the transferring until will keep some resources
    #     """
    #     nearest_tile = util.get_nearest_city_tile(self.pos, city)
    #     if nearest_tile and self.unit.pos.distance_to(nearest_tile.pos) == 1:
    #         self.log(f'transferring to {nearest_tile.city_id}')
    #         action = act.TransferAction(self.unit.team, self.id, nearest_tile.city_id, resource_type=resource_type,
    #                                     amount=self.unit.cargo[resource_type] - keep)
    #     else:
    #         self.log(f'moving towards {nearest_tile.city_id}')
    #         action = self.move(self.pos.direction_to(nearest_tile.pos))
    #     return action

    def build_city(self) -> act.Action:
        """Take action towards building a city"""
        self.current_mission = 'build_city'
        if self.wood < 100:
            self.current_mission = ''
            self.log('Trying to build city but not enough fuel, getting fuel instead')
            action = self.get_resources(C.RESOURCE_TYPES.WOOD)
        elif self.unit.can_build(self.game_state.map):
            action = self.do_action(act.SpawnCityAction(self.unit.team, self.id))
            self.current_mission = None
        else:
            target_cell = util.get_nearest_unoccupied_cell(self.unit.pos, self.game_state.game, self.game_state.occupied_tiles)
            if target_cell:
                self.log(f'Moving to empty cell {target_cell.pos}')
                action = self.move_to(target_cell.pos, avoid_cities=True)  # Avoid dropping off resources in a city on the way
                # pos_target = self.unit.pos.translate(self.unit.pos.direction_to(target_cell.pos), 1)
                # cell_target = self.game_state.map.get_cell_by_pos(pos_target)
                # if cell_target.city_tile:
                #     self.log('avoiding-citytile')
                #     action = self.move(util.random_direction())  # TODO: Better avoiding
                # else:
                #     self.log('Moving-to-build')
                #     action = self.move(self.unit.pos.direction_to(target_cell.pos))
            else:
                self.log('STUCK')
                action = self.move(C.DIRECTIONS.CENTER)
        return action

    def get_resources(self, resource_type=C.RESOURCE_TYPES.WOOD) -> act.Action:
        closest_resource = util.get_nearest_resource(self.game_state.map, self.unit.pos, resource_type=resource_type)
        if closest_resource:
            action = self.move_to(closest_resource.pos, avoid_cities=False)
            # action = self.move(self.unit.pos.direction_to(closest_resource.pos))
        else:
            self.log('No resource to get')
            action = self.move(C.DIRECTIONS.CENTER)
        return action

    # Quick access to info
    @property
    def wood(self):
        return self.unit.cargo["wood"]

    def can_act(self):
        return self.unit.can_act()

    def log(self, message):
        if self.logging:
            print(f'Unit {self.id}: {message}')