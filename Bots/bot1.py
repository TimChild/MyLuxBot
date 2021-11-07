from __future__ import annotations
from typing import List, Dict
from collections import deque

import luxai2021.game.actions as act
from luxai2021.game.game import Game, GameMap
from luxai2021.game.unit import Unit
from luxai2021.game.constants import Constants as C
from luxai2021.env.agent import Agent


class MyState:
    def __init__(self, game: Game):
        self.game = game

    def update(self, game):
        self.game = game

    def units(self, team):
        units = self.game.state["teamStates"][team]["units"]
        return units


class MyUnit:
    def __init__(self, unit: Unit, game_state: MyState):
        self.unit = unit
        self.id = unit.id
        self.previous_actions = deque([], maxlen=3)
        self.game_state = game_state

    def update(self, game_state: MyState):
        self.game_state = game_state

    def do_action(self, action: act.Action):
        """All actions should be returned through this"""
        self.previous_actions.append(action)
        return action

    def move(self, direction):
        if direction in {C.DIRECTIONS.NORTH, C.DIRECTIONS.SOUTH, C.DIRECTIONS.EAST, C.DIRECTIONS.WEST, C.DIRECTIONS.CENTER}:
            action = act.MoveAction(self.unit.team, self.id, direction)
        else:
            print(f'Asked for invalid move: {direction}')
            action = act.MoveAction(self.unit.team, self.id, C.DIRECTIONS.CENTER)
        return self.do_action(action)

    @property
    def wood(self):
        return self.unit.cargo.wood

    def can_act(self):
        return self.unit.can_act()


class BasicAgent(Agent):
    """Basic rule based Agent"""

    def __init__(self):
        super().__init__()
        self.units = dict()
        self.game_state = None

    def update_game_state(self, game: Game):
        if self.game_state:
            self.game_state.update(game)
        else:
            self.game_state = MyState(game)

    def update_units(self):
        units = self.game_state.units(self.team)
        for unit_id in units:  # Add new units
            if unit_id not in self.units:
                self.units[unit_id] = MyUnit(units[unit_id], self.game_state)

        for unit in self.units:  # Remove missing units
            if unit not in units:
                print(f'Unit lost?')
                self.units.pop(unit.id)

    def process_turn(self, game, team):
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        self.update_game_state(game)
        self.update_units()

        actions = []
        for unit in self.units.values():
            if unit.can_act():
                action = unit.move(C.DIRECTIONS.NORTH)
                actions.append(action)
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
