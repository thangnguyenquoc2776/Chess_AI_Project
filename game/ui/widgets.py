# game/ui/widgets.py
import pygame
from typing import Callable


class Button:
    """
    Nút bấm cơ bản: vẽ hình chữ nhật + text, click chuột trái để gọi callback.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None],
        bg_color=(70, 70, 70),
        hover_color=(100, 100, 100),
        text_color=(255, 255, 255),
    ):
        self.rect = rect
        self.text = text
        self.font = font
        self.callback = callback
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.bg_color

        pygame.draw.rect(surface, color, self.rect)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
