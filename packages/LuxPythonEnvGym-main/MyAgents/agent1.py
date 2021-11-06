from luxai2021.game.game import Game
# from luxai2021.game.actions import *
from luxai2021.game.actions import Action, MoveAction
from luxai2021.game.constants import LuxMatchConfigs_Default, Constants

from MyAgents.RL_agent1 import AgentPolicy

from luxai2021.env.agent import Agent
from luxai2021.env.lux_env import LuxEnvironment


class BasicAgent(Agent):
    def process_turn(self, game, team):
        actions = []
        if team != self.team:
            print("Asking for turn from wrong team?")
        units = game.state["teamStates"][team]["units"].values()
        for unit in units:
            if unit.can_act():
                act = MoveAction(team, unit.id, Constants.DIRECTIONS.NORTH)
                actions.append(act)
        return actions


if __name__ == "__main__":
    # Create agent
    agent1 = BasicAgent()
    agent2 = BasicAgent()

    # Create a game
    configs = LuxMatchConfigs_Default
    configs["stateful_replay"] = True
    configs["seed"] = 101
    env = LuxEnvironment(configs, agent1, agent2)
    game = env.game

    # Initialize agent
    env.set_replay_path('./replays/', 'replay')
    game.start_replay_logging(stateful=True, replay_folder=env.replay_folder, replay_filename_prefix=env.replay_prefix)
    # try:
    #     env.reset()
    # except StopIteration:
    #     pass

    print("Done resetting")

    agent1.game_start(game)
    agent1.set_team(Constants.TEAM.A)
    agent2.game_start(game)
    agent2.set_team(Constants.TEAM.B)

    game_over = False
    first_turn = True
    while not game_over and game.state['turn'] < 10:
        print("Turn %i" % game.state["turn"])

        # Array of actions for both teams. Eg: MoveAction(team, unit_id, direction)

        actions = []
        actions.extend(agent1.process_turn(game, Constants.TEAM.A))
        actions.extend(agent2.process_turn(game, Constants.TEAM.B))
        print(actions)
        game_over = game.run_turn_with_actions(actions)

        first_turn = False
        print(game.map.get_map_string())

    print("Game done, final map:")
    print(game.map.get_map_string())


