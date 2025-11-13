# game/scenes/base.py
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.app import GameApp


class SceneBase:
    """
    Base class cho mọi scene: menu, game, setting,...
    """

    def __init__(self, app: "GameApp"):
        self.app = app

    def handle_events(self, events: list[pygame.event.Event]):
        pass

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))
