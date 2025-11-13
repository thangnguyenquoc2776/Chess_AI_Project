# game/scenes/online_menu.py
import pygame
from typing import List

from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT


class OnlineMenuScene(SceneBase):
    """
    Menu Play Online (stub).
    - Host Game (TODO)
    - Join Game (TODO)
    - Back
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 36)
        self.font_info = pygame.font.Font(None, 28)

        self.buttons: List[Button] = []

        btn_width = 260
        btn_height = 50
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2
        gap = 60

        # Host
        rect_host = pygame.Rect(0, 0, btn_width, btn_height)
        rect_host.center = (center_x, start_y - gap)
        self.buttons.append(
            Button(
                rect_host,
                "Host Game (TODO)",
                self.font_button,
                callback=self._on_host,
            )
        )

        # Join
        rect_join = pygame.Rect(0, 0, btn_width, btn_height)
        rect_join.center = (center_x, start_y)
        self.buttons.append(
            Button(
                rect_join,
                "Join Game (TODO)",
                self.font_button,
                callback=self._on_join,
            )
        )

        # Back
        rect_back = pygame.Rect(0, 0, btn_width, btn_height)
        rect_back.center = (center_x, start_y + gap)
        self.buttons.append(
            Button(
                rect_back,
                "Back",
                self.font_button,
                callback=self._on_back,
            )
        )

        self.info_text = "Online mode: placeholder. TEAM NETWORK sẽ implement."

    # ---------- Callbacks ----------

    def _on_host(self):
        self.info_text = "Host: chức năng online chưa được implement."

    def _on_join(self):
        self.info_text = "Join: chức năng online chưa được implement."

    def _on_back(self):
        from .menu_play import PlayMenuScene
        self.app.change_scene(PlayMenuScene)

    # ---------- SceneBase override ----------

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render("Play Online", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        surface.blit(title_surf, title_rect)

        if self.info_text:
            info_surf = self.font_info.render(self.info_text, True, COLOR_TEXT)
            info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
            surface.blit(info_surf, info_rect)

        for btn in self.buttons:
            btn.draw(surface)
