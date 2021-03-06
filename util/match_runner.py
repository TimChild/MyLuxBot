from __future__ import annotations
from typing import List
import os

from luxai2021.game.game import Game
# from luxai2021.game.actions import *
from luxai2021.game.actions import Action, MoveAction
from luxai2021.game.constants import LuxMatchConfigs_Default, Constants
from luxai2021.game.replay import Replay
import json

from luxai2021.env.agent import Agent
from luxai2021.env.lux_env import LuxEnvironment


def get_game(agent1, agent2, seed=1):
    configs = LuxMatchConfigs_Default
    configs["stateful_replay"] = True
    configs["seed"] = seed
    game = Game(configs)
    agent1.set_team(Constants.TEAM.A)
    agent2.set_team(Constants.TEAM.B)
    game.agents = [agent1, agent2]
    return game


def render(game):
    print(f"Turn {game.state['turn']}")
    print(game.map.get_map_string())


def get_actions(game) -> List[Action]:
    """Get next actions from both agents in Game"""
    actions = []
    actions.extend(game.agents[0].process_turn(game, Constants.TEAM.A))
    actions.extend(game.agents[1].process_turn(game, Constants.TEAM.B))
    return actions


def print_actions(game, actions):
    print(f"Turn: {game.state['turn']}")
    for action in actions:
        if action:
            print(action.to_message(game))
        else:
            print('"None" action detected')


def generate_replay(agent1, agent2, max_turns=400, replay_name='default_replay', seed=1, replay_dir='./replays'):
    configs = LuxMatchConfigs_Default
    configs["stateful_replay"] = True
    configs["seed"] = seed
    game = Game(configs)
    game.agents = [agent1, agent2]
    # game = env.game
    filepath = os.path.join(replay_dir, replay_name)
    filepath = f'{filepath}.json'
    # game.start_replay_logging(stateful=True, replay_folder=env.replay_folder, replay_filename_prefix=env.replay_prefix)  # Adds a random number to filename
    game.replay = Replay(game, filepath)  # Same effect as above but with determined name
    game.replay_folder = replay_dir
    game.replay_filename_prefix = replay_name

    # Init agents
    agent1.game_start(game)
    agent1.set_team(Constants.TEAM.A)
    agent2.game_start(game)
    agent2.set_team(Constants.TEAM.B)

    game_over = False
    while not game_over and game.state['turn'] < max_turns:
        # Array of actions for both teams. Eg: MoveAction(team, unit_id, direction)
        actions = []
        actions = get_actions(game)
        game_over = game.run_turn_with_actions(actions)

    print("Game done, final map:")
    print(game.map.get_map_string())
    if not game_over:
        game.replay.write(game)
    with open(filepath, 'r') as f:
        replay_json = json.load(f)
    return replay_json


if __name__ == "__main__":
    from Bots.bot1 import BasicAgent

    # Create agent
    agent1 = BasicAgent()
    agent2 = BasicAgent()

    replay = generate_replay(agent1, agent2,  max_turns=400, seed=1, replay_dir='../replays')

