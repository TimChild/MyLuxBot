from __future__ import annotations
from typing import List, Dict
from collections import deque
import numpy as np

import luxai2021.game.actions as act
from luxai2021.game.game import Game, GameMap
from luxai2021.game.unit import Unit
from luxai2021.game.constants import Constants as C
from luxai2021.env.agent import Agent

import Bots.utility as util


class MyState:
    def __init__(self, game: Game, team):
        self.game = game
        self.team = team

    def update(self, game):
        self.game = game

    @property
    def map(self):
        return self.game.map

    def units(self):
        units = self.game.state["teamStates"][self.team]["units"]
        return units

    def cities(self):
        cities = {}
        for k, city in self.game.cities.items():
            if city.team == self.team:
                cities[k] = city
        return cities

    def lowest_city(self):
        """Returns city with lowest fuel"""
        cities = self.cities()
        return util.lowest_city(cities)

    @property
    def occupied_tiles(self):
        # occupied = self.game.map.resources
        occupied = []
        for x in range(self.game.map.width):
            for y in range(self.game.map.height):
                cell = self.game.map.get_cell(x, y)
                if cell.has_resource() or cell.is_city_tile():
                    occupied.append(cell)
        return occupied


class MyUnit:
    def __init__(self, unit: Unit, game_state: MyState):
        self.unit = unit
        self.id = unit.id
        self.previous_actions = deque([], maxlen=3)
        self.game_state = game_state

        self.current_mission = None  # Stores current intention of unit
        self.logging = False

    def update(self, game_state: MyState):
        """To be called at the beginning of turn"""
        self.game_state = game_state

    def self_action(self):
        """Have unit decide what action to take"""
        build_thresh = 5
        immediate_fuel_thresh = 3
        min_wood_thresh = 30

        low_city = self.game_state.lowest_city()

        if low_city:
            dist = util.distance_between(self.unit.pos, util.get_nearest_city_tile(self.unit.pos, low_city).pos)
            tl = util.time_left(low_city)
        else:
            dist = 0
            tl = np.inf
        action = None
        if self.unit.is_worker() and self.can_act():
            if self.wood == 100 and tl > dist+build_thresh:
                action = self.build_city()
            # elif self.wood > min_wood_thresh and tl < dist+immediate_fuel_thresh and low_city:
            #     self.log("Fuelling_low_city")
            #     self.go_to_city(low_city)
            elif self.unit.get_cargo_space_left() > 0:
                self.log("Getting")
                action = self.get_resources()
            else:
                self.log("Emptying")
                if low_city:
                    action = self.go_to_city(low_city)
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
        else:
            print(f'Asked for invalid move: {direction}')
            action = act.MoveAction(self.unit.team, self.id, C.DIRECTIONS.CENTER)
        return self.do_action(action)

    def go_to_city(self, city):
        return self.move(self.unit.pos.direction_to(util.get_nearest_city_tile(self.unit.pos, city).pos))

    def build_city(self) -> act.Action:
        """Take action towards building a city"""
        self.current_mission = 'build_city'
        if self.unit.can_build(self.game_state.map):
            action = self.do_action(act.SpawnCityAction(self.unit.team, self.id))
            self.current_mission = None
        else:
            target_cell = util.get_nearest_unoccupied_cell(self.unit.pos, self.game_state.game, self.game_state.occupied_tiles)
            if target_cell:
                pos_target = self.unit.pos.translate(self.unit.pos.direction_to(target_cell.pos), 1)
                cell_target = self.game_state.map.get_cell_by_pos(pos_target)
                if cell_target.city_tile:
                    self.log('avoiding-citytile')
                    action = self.move(util.random_direction())  # TODO: Better avoiding
                else:
                    self.log('Moving-to-build')
                    action = self.move(self.unit.pos.direction_to(target_cell.pos))
            else:
                self.log('STUCK')
                action = self.move(C.DIRECTIONS.CENTER)
        return action

    def get_resources(self, resource_type=C.RESOURCE_TYPES.WOOD) -> act.Action:
        closest_resource = util.get_nearest_resource(self.game_state.map, self.unit.pos, resource_type=resource_type)
        if closest_resource:
            action = self.move(self.unit.pos.direction_to(closest_resource.pos))
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


class BasicAgent(Agent):
    """Basic rule based Agent"""

    def __init__(self):
        super().__init__()
        self.units: Dict[str, MyUnit] = dict()
        self.game_state: MyState = None

    def update_game_state(self, game: Game):
        if self.game_state:
            self.game_state.update(game)
        else:
            self.game_state = MyState(game, self.team)

    def update_units(self):
        units = self.game_state.units()
        for unit_id in units:  # Add new units
            if unit_id not in self.units:
                self.units[unit_id] = MyUnit(units[unit_id], self.game_state)

        for unit_id in self.units:  # Remove missing units
            if unit_id not in units:
                print(f'Unit lost?')
                self.units.pop(unit_id)

    def process_turn(self, game, team):
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        self.update_game_state(game)
        self.update_units()

        actions = []
        for unit in self.units.values():
            action = unit.self_action()
            if action:
                actions.append(action)

        # actions = []
        # for unit in self.units.values():
        #     if unit.can_act():
        #         action = unit.move(C.DIRECTIONS.NORTH)
        #         actions.append(action)
        return actions








if __name__ == '__main__':
    from util.match_runner import get_game, get_actions, generate_replay, render

    max_turns = 20

    # Create agent
    agent1 = BasicAgent()
    agent2 = BasicAgent()

    # Create a game
    game_inst = get_game(agent1, agent2, seed=1)

    game_over = False
    i = 0
    while not game_over and i < max_turns:
        if i % 10 == 0:
            render(game_inst)
        i += 1
        actions = get_actions(game_inst)
        game_over = game_inst.run_turn_with_actions(actions)

    render(game_inst)
