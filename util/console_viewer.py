from Bots.bot1 import BasicAgent

from match_runner import get_game, get_actions, render

if __name__ == '__main__':
    agent1, agent2 = BasicAgent(), BasicAgent()
    game = get_game(agent1, agent2)

    actions = get_actions(game)
    print(f"Turn: {game.state['turn']}")
    for action in actions:
        print(type(action))
        print(action.to_message(game))

    actions = get_actions(game)
    game.run_turn_with_actions(actions)
    render(game)