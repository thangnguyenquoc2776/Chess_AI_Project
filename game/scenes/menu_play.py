# game/scenes/menu_play.py
import pygame
from typing import List

from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT


class PlayMenuScene(SceneBase):
    """
    Menu Play:
    - Play with AI
    - Play Online
    - Two Player (Local)
    - Back
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 36)

        self.buttons: List[Button] = []

        btn_width = 320
        btn_height = 50
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 60
        gap = 60

        # Play with AI
        rect_ai = pygame.Rect(0, 0, btn_width, btn_height)
        rect_ai.center = (center_x, start_y)
        self.buttons.append(
            Button(
                rect_ai,
                "Play with AI",
                self.font_button,
                callback=self._on_play_with_ai,
            )
        )

        # Play Online
        rect_online = pygame.Rect(0, 0, btn_width, btn_height)
        rect_online.center = (center_x, start_y + gap)
        self.buttons.append(
            Button(
                rect_online,
                "Play Online",
                self.font_button,
                callback=self._on_play_online,
            )
        )

        # Two Player (local)
        rect_pvp = pygame.Rect(0, 0, btn_width, btn_height)
        rect_pvp.center = (center_x, start_y + 2 * gap)
        self.buttons.append(
            Button(
                rect_pvp,
                "Two Player (Local)",
                self.font_button,
                callback=self._on_two_player_local,
            )
        )

        # Back
        rect_back = pygame.Rect(0, 0, btn_width, btn_height)
        rect_back.center = (center_x, start_y + 3 * gap)
        self.buttons.append(
            Button(
                rect_back,
                "Back",
                self.font_button,
                callback=self._on_back,
            )
        )

    # ---------- Callbacks ----------

    def _on_play_with_ai(self):
        from .game_vs_ai import GameVsAIScene

        # Mặc định: Người chơi là Trắng, AI Minimax Medium
        agent_spec = {"type": "minimax", "level": "medium"}
        self.app.change_scene(GameVsAIScene, human_white=True, agent_spec=agent_spec)

    def _on_play_online(self):
        from .online_menu import OnlineMenuScene
        self.app.change_scene(OnlineMenuScene)

    def _on_two_player_local(self):
        from .game_local import GameLocalScene
        self.app.change_scene(GameLocalScene, mode="pvp")

    def _on_back(self):
        from .menu_main import MainMenuScene
        self.app.change_scene(MainMenuScene)

    # ---------- SceneBase override ----------

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render("Play", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        surface.blit(title_surf, title_rect)

        for btn in self.buttons:
            btn.draw(surface)
