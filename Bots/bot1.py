from __future__ import annotations
from typing import List, Dict

import luxai2021.game.actions as act
from luxai2021.game.game import Game, GameMap
from luxai2021.game.constants import Constants as C
from luxai2021.env.agent import Agent


class BasicAgent(Agent):
    """Basic rule based Agent"""
    def process_turn(self, game, team):
        actions = []
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        units = game.state["teamStates"][team]["units"].values()
        for unit in units:
            if unit.can_act():
                action = act.MoveAction(team, unit.id, C.DIRECTIONS.NORTH)
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
