from __future__ import annotations
from typing import Tuple, Dict, Any
import time
import chess

from ai.agent_base import Agent
from .search import negamax_search
from .eval import evaluate, evaluate_advanced

class MinimaxAgent(Agent):
    def __init__(
        self,
        depth: int = 3,
        use_advanced_eval: bool = True,
        use_quiescence: bool = True,
        use_move_ordering: bool = True,
    ):
        self.name = f"minimax_d{depth}"
        self.depth = depth
        self.use_advanced_eval = use_advanced_eval
        self.use_quiescence = use_quiescence
        self.use_move_ordering = use_move_ordering

    def choose_move(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        start = time.time()

        # Sử dụng hàm evaluate_advanced chứa script mở màn
        eval_fn = evaluate_advanced if self.use_advanced_eval else evaluate

        # Debug: Báo hiện tại đang ở nước thứ mấy (Fullmove)
        print(f"--- Turn: {board.turn} (White=True/Black=False) | Move Number: {board.fullmove_number} | Ply: {board.ply()} ---")

        best_move, best_score, nodes = negamax_search(
            board=board,
            depth=self.depth,
            eval_fn=eval_fn,
            use_quiescence=self.use_quiescence,
            use_move_ordering=self.use_move_ordering
        )

        # Tự động phong hậu nếu tốt đi đến cuối
        if best_move and best_move != chess.Move.null():
            if board.is_capture(best_move) or board.piece_at(best_move.from_square).piece_type == chess.PAWN:
                # Logic check phong cap co ban
                pass
            
            # Gán promotion=Queen nếu chưa có (đề phòng engine quên)
            move_uci = best_move.uci()
            piece = board.piece_at(best_move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                rank = chess.square_rank(best_move.to_square)
                if (board.turn == chess.WHITE and rank == 7) or \
                   (board.turn == chess.BLACK and rank == 0):
                     if best_move.promotion is None:
                        best_move.promotion = chess.QUEEN

        elapsed_ms = int((time.time() - start) * 1000)
        
        # Debug output
        print(f"[AGENT] Picked Move: {best_move} | Score: {best_score} | Nodes: {nodes} | Time: {elapsed_ms}ms")

        info: Dict[str, Any] = {
            "agent": "minimax_scripted",
            "depth": self.depth,
            "score": best_score,
            "nodes": nodes,
            "time_ms": elapsed_ms
        }
        return best_move, info

# Factory functions giữ nguyên hoặc tối giản để test
def create_hard_agent() -> MinimaxAgent:
    return MinimaxAgent(depth=2, use_advanced_eval=True)

def create_easy_agent() -> MinimaxAgent:
    return MinimaxAgent(depth=2, use_advanced_eval=True)

def create_medium_agent() -> MinimaxAgent:
    return MinimaxAgent(depth=2, use_advanced_eval=True)

def create_expert_agent() -> MinimaxAgent:
    return MinimaxAgent(depth=4, use_advanced_eval=True)

def create_master_agent() -> MinimaxAgent:
    return MinimaxAgent(depth=4, use_advanced_eval=True)