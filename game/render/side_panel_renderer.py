# game/render/side_panel_renderer.py
import pygame

from game.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BOARD_LEFT,
    BOARD_PIXEL_SIZE,
    COLOR_TEXT,
    CHESS_TIME_LIMIT_SEC,
)


def _format_time(sec: float) -> str:
    """
    Đổi số giây còn lại thành chuỗi mm:ss.
    Nếu <= 0 thì trả về 00:00.
    """
    total = max(0, int(sec))
    minutes = total // 60
    seconds = total % 60
    return f"{minutes:02d}:{seconds:02d}"


def _short_status_text(status_text: str) -> str:
    """
    Rút gọn status cho panel bên trái để đỡ bị dài / tràn.
    Ví dụ: "White wins by checkmate" -> "White wins"
           "Draw (Stalemate)"         -> "Draw"
    Các trạng thái ngắn như "Check!", "Normal" giữ nguyên.
    """
    if not status_text:
        return "Normal"

    s = status_text

    # White wins by X / Black wins by X
    if "wins" in s and " by " in s:
        # "White wins by checkmate" -> "White wins"
        return s.split(" by ")[0]

    # Draw (xxx)
    if s.startswith("Draw"):
        return "Draw"

    return s


def draw_side_panels(
    surface: pygame.Surface,
    font: pygame.font.Font,
    white_time_sec: float,
    black_time_sec: float,
    ply_count: int,
    turn_white: bool,
    status_text: str,
):
    """
    Vẽ 2 panel:

    - BÊN TRÁI (Game Info):
        + Turn: White/Black
        + Status: Check! / Normal / White wins / Black wins / Draw
        + Move: số lượt (fullmove)

    - BÊN PHẢI (Chess Clock):
        + Đồng hồ cho White & Black (đếm ngược)
        + Bên đang tới lượt có dấu "<"
    """

    # Kích thước panel trái/phải
    left_width = BOARD_LEFT
    right_x = BOARD_LEFT + BOARD_PIXEL_SIZE
    right_width = SCREEN_WIDTH - right_x

    # Nếu cả 2 bên quá nhỏ thì thôi khỏi vẽ
    if left_width < 100 and right_width < 100:
        return

    line_h = font.get_linesize()
    center_y = SCREEN_HEIGHT // 2

    # fullmove ~ mỗi "lượt đôi": Trắng + Đen
    fullmove = ply_count // 2 + 1 if ply_count > 0 else 1
    base_minutes = CHESS_TIME_LIMIT_SEC // 60

    short_status = _short_status_text(status_text)

    # ---------- PANEL TRÁI: GAME INFO ----------
    if left_width >= 120:
        cx = left_width // 2

        # Title
        title_surf = font.render("Game Info", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(cx, center_y - line_h * 2))
        surface.blit(title_surf, title_rect)

        # Turn
        turn_str = "White" if turn_white else "Black"
        turn_surf = font.render(f"Turn: {turn_str}", True, COLOR_TEXT)
        turn_rect = turn_surf.get_rect(center=(cx, center_y - line_h))
        surface.blit(turn_surf, turn_rect)

        # Status (đã rút gọn)
        status_surf = font.render(f"Status: {short_status}", True, COLOR_TEXT)
        status_rect = status_surf.get_rect(center=(cx, center_y))
        surface.blit(status_surf, status_rect)

        # Move
        move_surf = font.render(f"Move: {fullmove}", True, COLOR_TEXT)
        move_rect = move_surf.get_rect(center=(cx, center_y + line_h))
        surface.blit(move_surf, move_rect)

    # ---------- PANEL PHẢI: CLOCK ----------
    if right_width >= 160:
        cx = right_x + right_width // 2

        # Title clock: ví dụ Clock (5m)
        if base_minutes > 0:
            clock_title = f"Clock ({base_minutes}m)"
        else:
            clock_title = "Clock"

        title_surf = font.render(clock_title, True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(cx, center_y - line_h * 2))
        surface.blit(title_surf, title_rect)

        # White time
        w_tag = "<" if turn_white else ""   # dùng '<' cho chắc font
        w_time = _format_time(white_time_sec)
        white_surf = font.render(f"White: {w_time} {w_tag}", True, COLOR_TEXT)
        white_rect = white_surf.get_rect(center=(cx, center_y - line_h))
        surface.blit(white_surf, white_rect)

        # Black time
        b_tag = "<" if not turn_white else ""
        b_time = _format_time(black_time_sec)
        black_surf = font.render(f"Black: {b_time} {b_tag}", True, COLOR_TEXT)
        black_rect = black_surf.get_rect(center=(cx, center_y))
        surface.blit(black_surf, black_rect)
