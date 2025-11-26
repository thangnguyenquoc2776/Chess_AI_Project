# game/scenes/menu_main.py
import pygame
from typing import List

from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT


class MainMenuScene(SceneBase):
    """
    Menu chính:
    - Play      -> vào menu chọn chế độ chơi
    - Simulator -> AI vs AI
    - Setting   -> màn hình cài đặt (stub)
    - Credit    -> credit
    - Exit      -> thoát game
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 36)

        self.buttons: List[Button] = []

        btn_width = 260
        btn_height = 50
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 80
        gap = 60

        # Play
        rect_play = pygame.Rect(0, 0, btn_width, btn_height)
        rect_play.center = (center_x, start_y)
        self.buttons.append(
            Button(
                rect_play,
                "Play",
                self.font_button,
                callback=self._on_play,
            )
        )

        # Simulator
        rect_sim = pygame.Rect(0, 0, btn_width, btn_height)
        rect_sim.center = (center_x, start_y + gap)
        self.buttons.append(
            Button(
                rect_sim,
                "Simulator",
                self.font_button,
                callback=self._on_simulator,
            )
        )

        # Setting
        rect_setting = pygame.Rect(0, 0, btn_width, btn_height)
        rect_setting.center = (center_x, start_y + 2 * gap)
        self.buttons.append(
            Button(
                rect_setting,
                "Setting",
                self.font_button,
                callback=self._on_setting,
            )
        )

        # Credit
        rect_credit = pygame.Rect(0, 0, btn_width, btn_height)
        rect_credit.center = (center_x, start_y + 3 * gap)
        self.buttons.append(
            Button(
                rect_credit,
                "Credit",
                self.font_button,
                callback=self._on_credit,
            )
        )

        # Exit
        rect_exit = pygame.Rect(0, 0, btn_width, btn_height)
        rect_exit.center = (center_x, start_y + 4 * gap)
        self.buttons.append(
            Button(
                rect_exit,
                "Exit",
                self.font_button,
                callback=self._on_exit,
            )
        )

    # ---------- Callbacks ----------

    def _on_play(self):
        from .menu_play import PlayMenuScene
        self.app.change_scene(PlayMenuScene)

    def _on_simulator(self):
        from .simulator import SimulatorScene
        
        white_agent = {"type": "minimax", "level": "hard", "side": "white"}
        black_agent = {"type": "random", "level": "easy", "side": "black"}

        self.app.change_scene(
            SimulatorScene,
            white_agent_spec=white_agent,
            black_agent_spec=black_agent,
        )

    def _on_setting(self):
        from .settings import SettingsScene
        self.app.change_scene(SettingsScene)

    def _on_credit(self):
        from .credits import CreditsScene
        self.app.change_scene(CreditsScene)

    def _on_exit(self):
        self.app.quit()

    # ---------- SceneBase override ----------

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render("Chess_AI_Project", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        surface.blit(title_surf, title_rect)

        for btn in self.buttons:
            btn.draw(surface)