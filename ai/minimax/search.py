from __future__ import annotations
from typing import Callable, Tuple, List
import chess
import random

EvalFn = Callable[[chess.Board], int]
INFINITY = 10**9

def negamax_search(
    board: chess.Board,
    depth: int,
    eval_fn: EvalFn,
    use_quiescence: bool = True,
    use_move_ordering: bool = True,
) -> Tuple[chess.Move, int, int]:
    """
    Root search function.
    """
    alpha = -INFINITY
    beta = INFINITY
    best_move = chess.Move.null()
    best_val = -INFINITY
    nodes_searched = 0
    
    # Lấy tất cả các nước đi hợp lệ
    moves = list(board.legal_moves)
    if not moves:
        return chess.Move.null(), eval_fn(board), 1

    # Move ordering (đơn giản để không làm rối script)
    if use_move_ordering:
        # Prioritize captures, promotion, checks
        moves.sort(key=lambda m: _move_score_guess(board, m), reverse=True)

    for move in moves:
        board.push(move)
        
        # Đệ quy
        score, sub_nodes = _negamax_worker(
            board, depth - 1, -beta, -alpha, -1 if board.turn == chess.BLACK else 1, eval_fn
        )
        
        # Đảo dấu score vì Negamax
        score = -score
        nodes_searched += sub_nodes
        board.pop()

        if score > best_val:
            best_val = score
            best_move = move
        
        alpha = max(alpha, score)
        if alpha >= beta:
            break
            
    return best_move, best_val, nodes_searched

def _negamax_worker(
    board: chess.Board, depth: int, alpha: int, beta: int, color: int, eval_fn: EvalFn
) -> Tuple[int, int]:
    
    # Node đếm
    nodes = 1

    # Kiểm tra hết ván cờ
    if board.is_game_over():
        # Dùng eval thông thường cho game over
        return eval_fn(board) * color, nodes

    # Hết depth
    if depth == 0:
        # Trả về điểm số (scripted bonus nằm trong eval_fn)
        return eval_fn(board) * color, nodes

    best_score = -INFINITY
    moves = list(board.legal_moves)
    
    # Simple sorting
    moves.sort(key=lambda m: _move_score_guess(board, m), reverse=True)

    found_pv = False
    for move in moves:
        board.push(move)
        
        score, sub_nodes = _negamax_worker(board, depth - 1, -beta, -alpha, -color, eval_fn)
        score = -score
        nodes += sub_nodes
        
        board.pop()

        best_score = max(best_score, score)
        alpha = max(alpha, score)
        
        if alpha >= beta:
            break
            
    return best_score, nodes

def _move_score_guess(board: chess.Board, move: chess.Move) -> int:
    """Heuristic đơn giản để sắp xếp nước đi"""
    if board.is_capture(move):
        return 10000 \
            + (100 if board.piece_at(move.to_square) else 0) \
            - (board.piece_at(move.from_square).piece_type if board.piece_at(move.from_square) else 0)
    if board.gives_check(move):
        return 9000
    if move.promotion:
        return 8000
    return 0