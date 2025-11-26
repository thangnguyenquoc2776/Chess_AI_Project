# ai/__init__.py
"""
Module AI cho Chess Game.

Cung cấp API thống nhất để Game gọi sang AI:
- choose_move_from_fen(): Hàm chính để lấy nước đi

Các loại AI:
- RandomAgent: Đi ngẫu nhiên
- MinimaxAgent: Dùng Minimax + Alpha-Beta pruning
- MLAgent: Dùng Machine Learning (TODO)

Usage:
    from ai import choose_move_from_fen
    
    result = choose_move_from_fen(
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        agent_spec={"type": "minimax", "level": "medium"}
    )
    
    print(result["uci"])   # "e2e4"
    print(result["info"])  # {"agent": "minimax", "depth": 3, ...}
"""

from .api import choose_move_from_fen

__all__ = ['choose_move_from_fen']
__version__ = '1.0.0'