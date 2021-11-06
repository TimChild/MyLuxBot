from __future__ import annotations
from typing import List
import lux.game as game
from lux import annotate
from random import randint


class Agent():
    def __init__(self, game_state: game.Game, player: game.Player):
        self.game_state = game_state
        self.player = player

    def get_actions(self) -> List[str]:
        actions = list()
        actions.append(annotate.circle(randint(0, self.game_state.map_width), randint(0, self.game_state.map_height)))
        return actions

    def update(self, game_state: game.Game):
        self.game_state = game_state

