# game/render/hud_renderer.py
import pygame
from core.board import Board
from game.config import COLOR_TEXT, SCREEN_WIDTH


def draw_hud(
    surface: pygame.Surface,
    board: Board,
    font: pygame.font.Font,
    status_text: str,
    game_over: bool = False,
    game_result: str = "ongoing",
):
    """
    HUD phía trên.

    Hiện tại: không vẽ gì, vì toàn bộ thông tin (Turn, Status, Clock)
    đã được chuyển sang side panels và overlay Game Over.

    Hàm này vẫn giữ lại để:
    - Không làm vỡ kiến trúc (Scene vẫn gọi draw_hud).
    - Sau này nếu muốn thêm header chung (logo, menu nhỏ) thì dùng lại.
    """
    return
