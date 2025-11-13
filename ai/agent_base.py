# ai/agent_base.py
from __future__ import annotations
from typing import Protocol, Tuple, Dict, Any
import chess


class Agent(Protocol):
    """
    Interface chung cho mọi agent:
    - RandomAgent
    - MinimaxAgent
    - MLAgent
    """

    name: str

    def choose_move(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        """
        Input:
            board: đối tượng chess.Board (python-chess) ở trạng thái hiện tại.

        Output:
            (move, info)
            - move: chess.Move hợp lệ mà agent chọn.
            - info: dict chứa thông tin thêm (depth, nodes, time_ms, score, ...)
        """
        ...
