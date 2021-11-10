from __future__ import annotations
from typing import Dict

from luxai2021.game.game import Game
from luxai2021.env.agent import Agent
from luxai2021.game.position import Position

from Bots.component_classes import MyState, MyCity, MyUnit


class BasicAgent(Agent):
    """Basic rule based Agent"""

    def __init__(self):
        super().__init__()
        self.units: Dict[str, MyUnit] = dict()
        self.cities: Dict[str, MyCity] = dict()
        self.game_state: MyState = None

    # @property
    # def units(self) -> Dict[str, MyUnit]:
    #     return {k: unit for k, unit in self.game_state.all_units.items() if unit.team == self.team}

    def update_game_state(self, game: Game):
        self.update_units(game)
        self.update_cities(game)

        if self.game_state:
            # self.game_state.update(game)  # TODO: need to update with the units that Agent has
            self.game_state.update(game, self.units, self.cities)
        else:
            self.game_state = MyState(game, self.units, self.cities, self.team)

    def update_units(self, game: Game):
        """Agent keeps track of all the units on the map (will have more info about own units throughout turn)"""
        all_units = dict(**game.state["teamStates"][0]["units"], **game.state["teamStates"][1]["units"])
        all_units = {k: MyUnit(v, v.team, self.game_state) for k, v in all_units.items()}
        for unit_id in all_units:  # Add new units
            if unit_id not in self.units:
                self.units[unit_id] = all_units[unit_id]

        for unit_id in list(self.units.keys()):  # Remove missing units
            if unit_id not in all_units:
                print(f'Unit lost? {unit_id}')  # Could be on the other team...
                self.units.pop(unit_id)

    def update_cities(self, game: Game):
        """Agent keeps track of all the cities on the map (will have more info about own cities throughout turn)"""
        cities = game.cities
        # cities = self.game_state.cities  # TODO: Should be updating from real Game here, not my game_state
        for city_id, city in cities.items():  # Add new units
            if city_id not in self.cities:
                city = MyCity(city, city.team, self.game_state)
                self.cities[city_id] = city

        for city_id in list(self.cities.keys()):  # Remove missing units
            if city_id not in cities:
                print(f'City lost? {city_id}')  # Could be other team
                self.cities.pop(city_id)

    def process_turn(self, game, team):
        """This is called each turn"""
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        self.update_game_state(game)

        actions = []
        for unit in self.game_state.units.values():
            if unit.can_act():
                unit.update(self.game_state)
                # if unit.id == 'u_1':
                #     action = unit.move_to(Position(2, 11))
                # elif unit.id == 'u_2':
                #     action = unit.move_to(Position(13, 11))
                # else:
                #     action = unit.self_action()
                action = unit.self_action()
                if action:
                    actions.append(action)

        for city in self.game_state.cities.values():
            city.update(self.game_state)
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
    from util.match_runner import get_game, get_actions, render, generate_replay
    assert Position(1, 2) == Position(1, 2)
    max_turns = 400
    #
    # # Create agent
    # agent1 = BasicAgent()
    # agent2 = BasicAgent()
    #
    # # Create a game
    # game_inst = get_game(agent1, agent2, seed=1)
    #
    # game_over = False
    # i = 0
    # while not game_over and i < max_turns:
    #     if i % 10 == 0:
    #         render(game_inst)
    #     i += 1
    #     actions = get_actions(game_inst)
    #     game_over = game_inst.run_turn_with_actions(actions)
    #
    #
    # render(game_inst)
    #
    agent1 = BasicAgent()
    agent2 = BasicAgent()
    generate_replay(agent1, agent2, max_turns=max_turns, replay_dir='../replays', seed=1)
