# game/scenes/settings.py
import pygame
from typing import List

from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT


class SettingsScene(SceneBase):
    """
    Màn hình Setting (stub).
    Hiện tại chỉ hiển thị vài setting mẫu, chưa lưu/chỉnh thật.
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_item = pygame.font.Font(None, 32)
        self.font_button = pygame.font.Font(None, 36)

        self.buttons: List[Button] = []

        btn_width = 220
        btn_height = 50
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 + 80

        rect_back = pygame.Rect(0, 0, btn_width, btn_height)
        rect_back.center = (center_x, start_y)
        self.buttons.append(
            Button(
                rect_back,
                "Back",
                self.font_button,
                callback=self._on_back,
            )
        )

        # Các dòng setting minh hoạ (sau này map vào config thật)
        self.dummy_items = [
            "- Board theme: Classic",
            "- Sound: On",
            "- Time limit: 5 minutes",
        ]

    def _on_back(self):
        from .menu_main import MainMenuScene
        self.app.change_scene(MainMenuScene)

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render("Settings", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        surface.blit(title_surf, title_rect)

        y = 200
        for item in self.dummy_items:
            item_surf = self.font_item.render(item, True, COLOR_TEXT)
            item_rect = item_surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            surface.blit(item_surf, item_rect)
            y += 40

        for btn in self.buttons:
            btn.draw(surface)
