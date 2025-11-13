# scripts/run_game.py
import pygame
from game.app import GameApp
from game.scenes.menu_main import MainMenuScene
from game.config import WINDOW_TITLE


def main():
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    app = GameApp(initial_scene_cls=MainMenuScene)
    app.run()

    pygame.quit()


if __name__ == "__main__":
    main()
