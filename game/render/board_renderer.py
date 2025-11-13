# game/render/board_renderer.py
import pygame
from game.config import (
    BOARD_LEFT,
    BOARD_TOP,
    TILE_SIZE,
    BOARD_SIZE,
    COLOR_LIGHT_SQUARE,
    COLOR_DARK_SQUARE,
    COLOR_SELECTED,
    COLOR_HIGHLIGHT,
    COLOR_LAST_MOVE,
)


def draw_board(
    surface: pygame.Surface,
    selected_square: tuple[int, int] | None = None,
    highlight_squares: list[tuple[int, int]] | None = None,
    last_move_squares: list[tuple[int, int]] | None = None,
):
    """
    Vẽ bàn 8x8.
    - selected_square: ô đang chọn
    - highlight_squares: ô có thể đi tới
    - last_move_squares: 2 ô from/to của nước đi cuối
    """
    if highlight_squares is None:
        highlight_squares = []
    if last_move_squares is None:
        last_move_squares = []

    for rank in range(BOARD_SIZE):
        for file in range(BOARD_SIZE):
            rank_from_top = BOARD_SIZE - 1 - rank
            x = BOARD_LEFT + file * TILE_SIZE
            y = BOARD_TOP + rank_from_top * TILE_SIZE

            base_color = COLOR_LIGHT_SQUARE if (file + rank) % 2 == 0 else COLOR_DARK_SQUARE
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            if selected_square is not None and (file, rank) == selected_square:
                color = COLOR_SELECTED
            elif (file, rank) in highlight_squares:
                color = COLOR_HIGHLIGHT
            elif (file, rank) in last_move_squares:
                color = COLOR_LAST_MOVE
            else:
                color = base_color

            pygame.draw.rect(surface, color, rect)
