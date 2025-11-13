# game/scenes/simulator.py
import pygame
from typing import Dict, Any

from .game_local import GameLocalScene
from game.ai_hook import choose_move_for_game


class SimulatorScene(GameLocalScene):
    """
    Scene Simulator: AI vs AI.
    Dùng để team AI test các agent hoặc làm demo tự chạy.
    """

    def __init__(
        self,
        app,
        white_agent_spec: Dict[str, Any] | None = None,
        black_agent_spec: Dict[str, Any] | None = None,
        move_delay_sec: float = 0.2,
    ):
        super().__init__(app, mode="sim")

        self.white_agent_spec = white_agent_spec or {
            "type": "minimax",
            "level": "easy",
            "side": "white",
        }
        self.black_agent_spec = black_agent_spec or {
            "type": "minimax",
            "level": "easy",
            "side": "black",
        }

        self._ai_delay_sec = move_delay_sec
        self._ai_timer = 0.0

        self.status_text = "Simulator: AI vs AI"

    # ---------- Events ----------

    def handle_events(self, events):
        # Simulator chỉ cần ESC để quay lại menu
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                from .menu_main import MainMenuScene
                self.app.change_scene(MainMenuScene)

    # ---------- Update ----------

    def update(self, dt: float):
        if self.game_over or self.promotion_active:
            return

        # Không gọi super().update(dt) để tránh hết giờ
        self._ai_timer += dt
        if self._ai_timer < self._ai_delay_sec:
            return
        self._ai_timer = 0.0

        # Chọn agent theo bên đang đi
        if self.board.turn_white:
            spec = self.white_agent_spec
        else:
            spec = self.black_agent_spec

        # Gọi AI
        try:
            uci, _info = choose_move_for_game(self.board, spec)
        except NotImplementedError:
            self.status_text = "AI chưa được implement (TEAM AI). Simulator dừng lại."
            self.game_over = True
            self.game_over_reason = "AI Not Implemented"
            return
        except Exception as e:
            self.status_text = f"Lỗi AI: {e}"
            self.game_over = True
            self.game_over_reason = "AI Error"
            return

        if uci not in self.legal_moves_uci:
            self.status_text = "AI trả về nước đi không hợp lệ. Simulator dừng."
            self.game_over = True
            self.game_over_reason = "Illegal move"
            return

        self.selected_square = None
        self.highlight_squares = []

        self._apply_move_and_update_state(uci)

    # ---------- Render ----------

    def render(self, surface: pygame.Surface):
        # Dùng lại render của GameLocalScene (bàn + panel + overlay)
        super().render(surface)
