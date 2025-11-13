# game/render/piece_renderer.py
import pygame

from game.config import (
    BOARD_LEFT,
    BOARD_TOP,
    TILE_SIZE,
    BOARD_SIZE,
    COLOR_WHITE_PIECE,
    COLOR_BLACK_PIECE,
)


def draw_pieces(surface: pygame.Surface, board, font: pygame.font.Font):
    """
    Vẽ các quân cờ lên bàn.

    - `board.piece_symbol_at(file, rank)` trả về:
        + 'P','N','B','R','Q','K'  cho quân TRẮNG
        + 'p','n','b','r','q','k'  cho quân ĐEN
        + None / '' nếu ô trống.

    - Ta luôn vẽ bằng chữ HOA (P,N,B,R,Q,K) để sau này
      đổi qua asset hình quân cờ cũng dễ map.
    - Màu chữ:
        + COLOR_WHITE_PIECE cho quân trắng
        + COLOR_BLACK_PIECE cho quân đen
    """

    for rank in range(BOARD_SIZE):
        for file in range(BOARD_SIZE):
            symbol = board.piece_symbol_at(file, rank)
            if not symbol:
                continue

            # Trắng = chữ hoa, Đen = chữ thường
            is_white = symbol.isupper()

            # Chọn màu vẽ quân
            text_color = COLOR_WHITE_PIECE if is_white else COLOR_BLACK_PIECE

            # Chỉ lấy chữ hoa để hiển thị
            char = symbol.upper()

            # Tính toạ độ ô trên màn hình
            # file: 0..7 (a..h) -> x tăng sang phải
            # rank: 0..7 (1..8) -> ta vẽ rank 0 ở hàng dưới cùng
            x = BOARD_LEFT + file * TILE_SIZE
            y = BOARD_TOP + (BOARD_SIZE - 1 - rank) * TILE_SIZE

            cx = x + TILE_SIZE // 2
            cy = y + TILE_SIZE // 2

            text_surf = font.render(char, True, text_color)
            text_rect = text_surf.get_rect(center=(cx, cy))
            surface.blit(text_surf, text_rect)
