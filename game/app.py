# game/app.py
import pygame
from typing import Type

from .config import SCREEN_WIDTH, SCREEN_HEIGHT


class GameApp:
    """
    Điều khiển vòng lặp chính Pygame, quản lý scene hiện tại.
    """

    def __init__(self, initial_scene_cls: Type["SceneBase"]):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Scene hiện tại
        self.current_scene = initial_scene_cls(self)

    def change_scene(self, new_scene_cls: Type["SceneBase"], *args, **kwargs):
        """Chuyển sang scene khác."""
        self.current_scene = new_scene_cls(self, *args, **kwargs)

    def quit(self):
        self.running = False

    def run(self):
        """Vòng lặp game chính."""
        while self.running:
            dt_ms = self.clock.tick(60)  # fps = 60
            dt = dt_ms / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.current_scene.handle_events(events)
            self.current_scene.update(dt)
            self.current_scene.render(self.screen)

            pygame.display.flip()
