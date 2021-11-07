# from luxai2021.game.actions import *
from luxai2021.game.actions import MoveAction
from luxai2021.game.constants import Constants

from luxai2021.env.agent import Agent


class BasicAgent(Agent):
    def process_turn(self, game, team):
        actions = []
        if team != self.team:
            raise Exception("ERROR: Asking for turn from wrong team")
        units = game.state["teamStates"][team]["units"].values()
        for unit in units:
            if unit.can_act():
                act = MoveAction(team, unit.id, Constants.DIRECTIONS.NORTH)
                actions.append(act)
        return actions


if __name__ == "__main__":
    from match_runner import get_game, get_actions, render
    max_turns = 20

    # Create agent
    agent1 = BasicAgent()
    agent2 = BasicAgent()

    # Create a game
    game = get_game(agent1, agent2, seed=1)

    game_over = False
    i = 0
    while not game_over and i < max_turns:
        if i % 10 == 0:
            render(game)
        i += 1
        actions = get_actions(game)
        game_over = game.run_turn_with_actions(actions)

    render(game)
