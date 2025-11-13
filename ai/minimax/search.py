# ai/minimax/search.py
from __future__ import annotations
from typing import Callable, Tuple
import chess

EvalFn = Callable[[chess.Board], int]


def negamax_search(
    board: chess.Board,
    depth: int,
    eval_fn: EvalFn,
) -> Tuple[chess.Move, int, int]:
    """
    Negamax + alpha-beta đơn giản.
    Trả về: (best_move, best_score, nodes)

    - best_move: nước đi tốt nhất từ trạng thái hiện tại
    - best_score: điểm đánh giá
    - nodes: số node đã duyệt (để debug)
    """

    alpha = -10**9
    beta = 10**9
    best_move = None
    nodes = 0

    for move in board.legal_moves:
        board.push(move)
        score, sub_nodes = _negamax(board, depth - 1, -beta, -alpha, -1, eval_fn)
        board.pop()
        score = -score
        nodes += sub_nodes + 1

        if best_move is None or score > alpha:
            alpha = score
            best_move = move

    if best_move is None:
        # không có legal move (game over) -> score theo eval
        return chess.Move.null(), eval_fn(board), nodes

    return best_move, alpha, nodes


def _negamax(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    color: int,
    eval_fn: EvalFn,
) -> Tuple[int, int]:
    """
    Hàm đệ quy của negamax.
    color = 1 nếu đang perspective của bên hiện tại,
          = -1 nếu đảo bên.
    """
    nodes = 0

    if depth == 0 or board.is_game_over():
        return color * eval_fn(board), 1

    best = -10**9

    for move in board.legal_moves:
        board.push(move)
        score, sub_nodes = _negamax(board, depth - 1, -beta, -alpha, -color, eval_fn)
        board.pop()

        score = -score
        nodes += sub_nodes + 1

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break  # cắt tỉa

    return best, nodes
