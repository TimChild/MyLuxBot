from __future__ import annotations
from typing import List, Dict

from luxai2021.game.game import Game, Position
from luxai2021.env.agent import Agent

from Bots.component_classes import MyState, MyCity, MyUnit


def units_at_position(pos: Position, units: List[MyUnit]) -> List[MyUnit]:
    current_units = []
    for unit in units:
        if pos.distance_to(unit.pos) == 0:
            current_units.append(unit)
    return current_units


class BasicAgent(Agent):
    """Basic rule based Agent"""

    def __init__(self):
        super().__init__()
        self.units: Dict[str, MyUnit] = dict()
        self.cities: Dict[str, MyCity] = dict()
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

        for unit_id in list(self.units.keys()):  # Remove missing units
            if unit_id not in units:
                print(f'Unit lost?')
                self.units.pop(unit_id)

    def update_cities(self):
        cities = self.game_state.cities()
        for city_id in cities:  # Add new units
            if city_id not in self.cities:
                self.cities[city_id] = MyCity(cities[city_id], self.game_state, list(self.units.values()))

        for city_id in list(self.cities.keys()):  # Remove missing units
            if city_id not in cities:
                print(f'City lost?')
                self.cities.pop(city_id)

    def process_turn(self, game, team):
        """This is called each turn"""
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        self.update_game_state(game)
        self.update_units()
        self.update_cities()

        actions = []
        for unit in self.units.values():
            action = unit.self_action()
            if action:
                actions.append(action)

        for city in self.cities.values():
            city_actions = city.self_action()
            if city_actions:
                actions.extend(city_actions)

        # actions = []
        # for unit in self.units.values():
        #     if unit.can_act():
        #         action = unit.move(C.DIRECTIONS.NORTH)
        #         actions.append(action)
        return actions








if __name__ == '__main__':
    from util.match_runner import get_game, get_actions, render

    max_turns = 400

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
