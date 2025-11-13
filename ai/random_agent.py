# ai/random_agent.py
import random
from typing import Tuple, Dict, Any
import chess

from .agent_base import Agent


class RandomAgent(Agent):
    def __init__(self, seed: int | None = None):
        self.name = "random"
        self._rng = random.Random(seed)

    def choose_move(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves (game must be over)")

        move = self._rng.choice(legal_moves)
        info: Dict[str, Any] = {
            "agent": self.name,
            "chosen": move.uci(),
            "note": "random move",
        }
        return move, info
