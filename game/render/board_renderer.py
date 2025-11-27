# game/render/board_renderer.py
import pygame

from game.config import (
    BOARD_LEFT,
    BOARD_TOP,
    TILE_SIZE,
    BOARD_SIZE,
    BOARD_PIXEL_SIZE,
    COLOR_LIGHT_SQUARE,
    COLOR_DARK_SQUARE,
    COLOR_SELECTED,
    COLOR_MOVE_HINT,
    COLOR_LAST_MOVE,
)


def _square_rect(file: int, rank: int) -> pygame.Rect:
    """
    Trả về rect của ô (file, rank) trên màn hình.

    file: 0..7 (a..h, trái -> phải)
    rank: 0..7 (1..8, dưới -> trên)
    """
    x = BOARD_LEFT + file * TILE_SIZE
    y = BOARD_TOP + (BOARD_SIZE - 1 - rank) * TILE_SIZE
    return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)


def draw_board(
    surface: pygame.Surface,
    selected_square,
    move_squares,
    capture_squares,
    last_move_squares,
):
    """
    Vẽ bàn cờ + hiệu ứng:

    - Panel nền phía sau bàn
    - Ô sáng / tối
    - Ô của nước đi cuối (last_move_squares)
    - Ô có thể đi tới (move_squares + capture_squares)
    - Ô ăn quân (capture_squares) có viền đặc biệt
    - Ô đang chọn (selected_square)
    """

    move_squares = move_squares or []
    capture_squares = capture_squares or []
    last_move_squares = last_move_squares or []

    move_set = set(move_squares)
    capture_set = set(capture_squares)
    all_move_set = move_set | capture_set

    # -----------------------
    #  PANEL NỀN + KHUNG
    # -----------------------
    panel_margin = int(TILE_SIZE * 0.35)
    panel_rect = pygame.Rect(
        BOARD_LEFT - panel_margin,
        BOARD_TOP - panel_margin,
        BOARD_PIXEL_SIZE + panel_margin * 2,
        BOARD_PIXEL_SIZE + panel_margin * 2,
    )

    panel_color = (10, 10, 10)
    panel_border = (60, 60, 60)
    border_radius = int(TILE_SIZE * 0.25)

    pygame.draw.rect(surface, panel_color, panel_rect, border_radius=border_radius)
    pygame.draw.rect(surface, panel_border, panel_rect, width=2, border_radius=border_radius)

    # -----------------------
    #  NỀN Ô SÁNG / TỐI
    # -----------------------
    for rank in range(BOARD_SIZE):
        for file in range(BOARD_SIZE):
            rect = _square_rect(file, rank)
            color = COLOR_LIGHT_SQUARE if (file + rank) % 2 == 0 else COLOR_DARK_SQUARE
            pygame.draw.rect(surface, color, rect)

    tile_overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    # -----------------------
    #  NƯỚC ĐI CUỐI
    # -----------------------
    for file, rank in last_move_squares:
        rect = _square_rect(file, rank)

        tile_overlay.fill((0, 0, 0, 0))
        r, g, b = COLOR_LAST_MOVE
        tile_overlay.fill((r, g, b, 80))
        surface.blit(tile_overlay, rect.topleft)

        border_width = max(2, TILE_SIZE // 26)
        pygame.draw.rect(surface, COLOR_LAST_MOVE, rect, width=border_width)

    # -----------------------
    #  TẤT CẢ Ô ĐI ĐƯỢC (MOVE + CAPTURE)
    # -----------------------
    if all_move_set:
        for file, rank in all_move_set:
            rect = _square_rect(file, rank)

            tile_overlay.fill((0, 0, 0, 0))
            r, g, b = COLOR_MOVE_HINT
            # phủ chung cho mọi ô có thể đi
            tile_overlay.fill((r, g, b, 110))
            surface.blit(tile_overlay, rect.topleft)

    # -----------------------
    #  Ô ĂN QUÂN (CAPTURE) – VIỀN ĐẶC BIỆT
    # -----------------------
    if capture_set:
        capture_border_color = (220, 120, 80)  # cam nhẹ
        for file, rank in capture_set:
            rect = _square_rect(file, rank)
            inner = rect.inflate(-TILE_SIZE * 0.12, -TILE_SIZE * 0.12)
            pygame.draw.rect(
                surface,
                capture_border_color,
                inner,
                width=max(2, TILE_SIZE // 22),
            )

    # -----------------------
    #  Ô ĐANG CHỌN
    # -----------------------
    if selected_square is not None:
        file, rank = selected_square
        rect = _square_rect(file, rank)

        tile_overlay.fill((0, 0, 0, 0))
        r, g, b = COLOR_SELECTED
        tile_overlay.fill((r, g, b, 140))
        surface.blit(tile_overlay, rect.topleft)

        inner_rect = rect.inflate(-TILE_SIZE * 0.10, -TILE_SIZE * 0.10)
        pygame.draw.rect(
            surface,
            COLOR_SELECTED,
            inner_rect,
            width=max(2, TILE_SIZE // 18),
        )
