# game/scenes/ai_selection.py
import pygame
from .base import SceneBase
from game.ui.widgets import Button
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_TEXT
from ai.api import get_available_agents


class AISelectionScene(SceneBase):
    def __init__(self, app, human_white=True):
        super().__init__(app)
        self.human_white = human_white

        self.font_title = pygame.font.Font(None, 64)
        self.font_btn = pygame.font.Font(None, 42)
        self.buttons = []

        center_x = SCREEN_WIDTH // 2
        start_y = 180
        gap = 75

        agents = get_available_agents()

        for key, info in agents.items():
            config = info["config"]
            name = info.get("name", key.replace("_", " ").title())
            if info.get("badge"):
                name += f" [{info['badge']}]"

            btn = Button(
                pygame.Rect(0, 0, 460, 65),
                name,
                self.font_btn,
                callback=lambda c=config: self.start_game(c)
            )
            btn.rect.centerx = center_x
            btn.rect.y = start_y + len(self.buttons) * gap
            self.buttons.append(btn)

        # Back button
        back = Button(
            pygame.Rect(0, 0, 200, 50),
            "Back",
            self.font_btn,
            callback=self.go_back
        )
        back.rect.centerx = center_x
        back.rect.y = start_y + len(self.buttons) * gap + 20
        self.buttons.append(back)

    def start_game(self, agent_spec):
        from .game_vs_ai import GameVsAIScene
        self.app.change_scene(GameVsAIScene, human_white=self.human_white, agent_spec=agent_spec)

    def go_back(self):
        from .menu_play import PlayMenuScene
        self.app.change_scene(PlayMenuScene)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in self.buttons:
                    btn.handle_event(event)

    def render(self, surface):
        surface.fill(COLOR_BG)

        title = self.font_title.render("Choose AI Opponent", True, COLOR_TEXT)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(title, title_rect)

        side = "White" if self.human_white else "Black"
        subtitle = self.font_btn.render(f"You play as {side}", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150))
        surface.blit(subtitle, subtitle_rect)

        for btn in self.buttons:
            btn.draw(surface)