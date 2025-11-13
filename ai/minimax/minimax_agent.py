# ai/minimax/minimax_agent.py
from __future__ import annotations
from typing import Tuple, Dict, Any
import time
import chess

from ai.agent_base import Agent
from .search import negamax_search
from .eval import evaluate


class MinimaxAgent(Agent):
    def __init__(self, depth: int = 3):
        self.name = f"minimax_d{depth}"
        self.depth = depth

    def choose_move(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        start = time.time()

        best_move, best_score, nodes = negamax_search(
            board,
            depth=self.depth,
            eval_fn=evaluate,
        )

        elapsed_ms = int((time.time() - start) * 1000)

        info: Dict[str, Any] = {
            "agent": "minimax",
            "depth": self.depth,
            "score": best_score,
            "nodes": nodes,
            "time_ms": elapsed_ms,
        }
        return best_move, info
