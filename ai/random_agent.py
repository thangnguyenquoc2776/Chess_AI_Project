# ai/random_agent.py
"""
Random Agent - chọn nước đi ngẫu nhiên.
FIX: Dùng random.random() thay vì Random(seed) để tránh lặp lại kết quả
"""

import random
import time
from typing import Tuple, Dict, Any
import chess

from .agent_base import Agent


class RandomAgent(Agent):
    def __init__(self, seed: int | None = None):
        self.name = "random"
        
        if seed is None:
            self._rng = None  
            self._seed = None
        else:
            self._rng = random.Random(seed)
            self._seed = seed

    def choose_move(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves (game must be over)")

        # FIX: Dùng random toàn cục nếu không có seed
        if self._rng is None:
            move = random.choice(legal_moves)
        else:
            move = self._rng.choice(legal_moves)
        
        info: Dict[str, Any] = {
            "agent": self.name,
            "chosen": move.uci(),
            "note": "random move",
        }
        
        if self._seed is not None:
            info["seed"] = self._seed
            
        return move, info