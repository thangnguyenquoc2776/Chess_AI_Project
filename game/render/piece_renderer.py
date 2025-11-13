# game/render/piece_renderer.py
import pygame
from core.board import Board
from game.config import (
    BOARD_LEFT,
    BOARD_TOP,
    TILE_SIZE,
    BOARD_SIZE,
    COLOR_TEXT,
)


def draw_pieces(surface: pygame.Surface, board: Board, font: pygame.font.Font):
    """
    Vẽ quân cờ bằng text đơn giản (P, N, B, R, Q, K).
    Sau này có thể thay bằng ảnh PNG.
    """
    for rank in range(BOARD_SIZE):
        for file in range(BOARD_SIZE):
            symbol = board.piece_symbol_at(file, rank)
            if not symbol:
                continue

            # rank 0 ở dưới, nên phải tính lại y theo rank_from_top
            rank_from_top = BOARD_SIZE - 1 - rank
            x = BOARD_LEFT + file * TILE_SIZE + TILE_SIZE // 2
            y = BOARD_TOP + rank_from_top * TILE_SIZE + TILE_SIZE // 2

            text = symbol.upper()
            color = COLOR_TEXT

            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(x, y))
            surface.blit(text_surf, text_rect)
