# core/rules.py
from .board import Board


def generate_legal_moves(board: Board) -> list[str]:
    """
    Trả về list nước hợp lệ dạng UCI.
    Ở game, ta sẽ filter theo ô 'from' để highlight.
    """
    return board.legal_moves_uci()


def get_game_result(board: Board) -> str:
    """
    Wrapper cho Board.result_status().
    """
    return board.result_status()
