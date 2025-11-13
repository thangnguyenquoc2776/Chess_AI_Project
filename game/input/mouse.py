# game/input/mouse.py
from typing import Tuple
from game.config import BOARD_LEFT, BOARD_TOP, TILE_SIZE, BOARD_SIZE


def pixel_to_board_square(x: int, y: int) -> Tuple[int, int] | None:
    """
    Chuyển tọa độ pixel (x, y) sang ô cờ (file, rank) 0-based:
    - file: 0..7 -> cột a..h
    - rank: 0..7 -> hàng 1..8 (1 ở dưới, 8 ở trên)
    Return None nếu click ngoài bàn.
    """
    bx = x - BOARD_LEFT
    by = y - BOARD_TOP
    if bx < 0 or by < 0:
        return None

    file_index = bx // TILE_SIZE
    rank_from_top = by // TILE_SIZE

    if file_index < 0 or file_index >= BOARD_SIZE:
        return None
    if rank_from_top < 0 or rank_from_top >= BOARD_SIZE:
        return None

    # rank 0 = hàng 1 (dưới), nên phải đảo trục y
    rank_index = BOARD_SIZE - 1 - rank_from_top
    return int(file_index), int(rank_index)
