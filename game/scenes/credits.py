# game/scenes/credits.py
import pygame
from typing import List

from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT


class CreditsScene(SceneBase):
    """
    Màn hình Credit.
    Team có thể sửa self.lines để ghi tên thành viên, GVHD, v.v.
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_text = pygame.font.Font(None, 28)
        self.font_button = pygame.font.Font(None, 36)

        self.buttons: List[Button] = []

        btn_width = 220
        btn_height = 50
        center_x = SCREEN_WIDTH // 2

        rect_back = pygame.Rect(0, 0, btn_width, btn_height)
        rect_back.center = (center_x, SCREEN_HEIGHT - 80)
        self.buttons.append(
            Button(
                rect_back,
                "Back",
                self.font_button,
                callback=self._on_back,
            )
        )

        # TODO: sửa lại thành tên thật của nhóm
        self.lines = [
            "Chess_AI_Project",
            "",
            "Game Team: (điền tên thành viên)",
            "AI Team: (điền tên thành viên)",
            "Lecturer: (GVHD)",
            "",
            "Built with Python, pygame, python-chess.",
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

        title_surf = self.font_title.render("Credits", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(title_surf, title_rect)

        y = 170
        for line in self.lines:
            text_surf = self.font_text.render(line, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y))
            surface.blit(text_surf, text_rect)
            y += 32

        for btn in self.buttons:
            btn.draw(surface)
