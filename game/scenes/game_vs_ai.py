# game/scenes/game_vs_ai.py
import pygame
from typing import Dict, Any

from .game_local import GameLocalScene
from game.ai_hook import choose_move_for_game


class GameVsAIScene(GameLocalScene):
    """
    Scene chơi Người vs AI.
    - Tái sử dụng gần như toàn bộ logic của GameLocalScene.
    - Thêm lượt đi tự động cho phía AI bằng ai_hook.choose_move_for_game().
    """

    def __init__(
        self,
        app,
        human_white: bool = True,
        agent_spec: Dict[str, Any] | None = None,
    ):
        super().__init__(app, mode="pve")
        self.human_white = human_white
        self.agent_spec: Dict[str, Any] = agent_spec or {
            "type": "minimax",
            "level": "easy",
        }

        # AI state
        self._waiting_for_ai_move: bool = False
        self._ai_think_delay_sec: float = 0.2  # trễ nhẹ cho dễ nhìn
        self._ai_timer: float = 0.0

        # Xem có cần cho AI đi trước không (nếu người chơi là Đen)
        self._schedule_ai_if_needed()

    # ---------- Helpers ----------

    def _schedule_ai_if_needed(self):
        """
        Kiểm tra xem lượt hiện tại là của AI hay không.
        Nếu phải của AI => bật cờ _waiting_for_ai_move.
        """
        if self.game_over or self.promotion_active:
            self._waiting_for_ai_move = False
            return

        is_human_turn = (self.board.turn_white == self.human_white)
        self._waiting_for_ai_move = not is_human_turn

    # Ghi đè hàm áp dụng nước đi để sau mỗi nước
    # sẽ gọi _schedule_ai_if_needed().
    def _apply_move_and_update_state(self, uci: str) -> bool:
        success = super()._apply_move_and_update_state(uci)
        if success:
            self._schedule_ai_if_needed()
        return success

    # ---------- Vòng lặp ----------

    def update(self, dt: float):
        # Cập nhật đồng hồ như GameLocalScene (hết giờ vẫn thua)
        super().update(dt)

        if self.game_over or self.promotion_active:
            return

        if not self._waiting_for_ai_move:
            return

        # Đợi một khoảng nhỏ để nhìn cho kịp
        self._ai_timer += dt
        if self._ai_timer < self._ai_think_delay_sec:
            return
        self._ai_timer = 0.0

        # Gọi AI
        try:
            uci, _info = choose_move_for_game(self.board, self.agent_spec)
        except NotImplementedError:
            # TEAM AI chưa implement => báo trạng thái và dừng gọi AI nữa
            self.status_text = "AI chưa được implement (TEAM AI sẽ viết choose_move_for_game)."
            self._waiting_for_ai_move = False
            return
        except Exception as e:
            self.status_text = f"Lỗi AI: {e}"
            self._waiting_for_ai_move = False
            return

        # Kiểm tra nước đi AI trả về có hợp lệ không
        if uci not in self.legal_moves_uci:
            self.status_text = "AI trả về nước đi không hợp lệ."
            self._waiting_for_ai_move = False
            return

        # Clear highlight của người chơi
        self.selected_square = None
        self.highlight_squares = []

        # Áp dụng nước đi của AI
        self._apply_move_and_update_state(uci)
