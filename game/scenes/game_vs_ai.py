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

    def _is_in_replay_mode(self) -> bool:
        """Kiểm tra xem có đang ở chế độ replay không"""
        return getattr(self, 'replay_mode', False)

    def _schedule_ai_if_needed(self):
        """
        Kiểm tra xem lượt hiện tại là của AI hay không.
        Nếu phải của AI => bật cờ _waiting_for_ai_move.
        """
        if self.game_over or self.promotion_active:
            self._waiting_for_ai_move = False
            return

        # QUAN TRỌNG: Không schedule AI khi đang replay
        if self._is_in_replay_mode():
            self._waiting_for_ai_move = False
            return

        is_human_turn = (self.board.turn_white == self.human_white)
        self._waiting_for_ai_move = not is_human_turn
        
        # Reset timer khi schedule AI mới
        if self._waiting_for_ai_move:
            self._ai_timer = 0.0

    # Ghi đè hàm áp dụng nước đi để sau mỗi nước
    # sẽ gọi _schedule_ai_if_needed().
    def _apply_move_and_update_state(self, uci: str) -> bool:
        success = super()._apply_move_and_update_state(uci)
        if success:
            self._schedule_ai_if_needed()
        return success

    # ---------- Override reset/replay methods ----------
    
    def reset_game(self):
        """Override để reset cả AI state khi reset game"""
        super().reset_game()
        self._waiting_for_ai_move = False
        self._ai_timer = 0.0
        
        # Đảm bảo tắt replay mode
        if hasattr(self, 'replay_mode'):
            self.replay_mode = False
        
        # Sau khi reset, check xem có phải lượt AI không
        self._schedule_ai_if_needed()
    
    def _on_play_again(self):
        """
        QUAN TRỌNG: Override để tạo lại GameVsAIScene thay vì GameLocalScene
        """
        # Tạo lại scene với cùng config
        self.app.change_scene(
            GameVsAIScene, 
            human_white=self.human_white,
            agent_spec=self.agent_spec
        )
    
    def enter_replay_mode(self):
        """Khi vào chế độ replay, tắt AI"""
        if hasattr(super(), 'enter_replay_mode'):
            super().enter_replay_mode()
        
        self.replay_mode = True
        self._waiting_for_ai_move = False
        self._ai_timer = 0.0
    
    def exit_replay_mode(self):
        """Override để đảm bảo AI được kích hoạt lại sau replay"""
        # Gọi parent method nếu có
        if hasattr(super(), 'exit_replay_mode'):
            super().exit_replay_mode()
        
        # Tắt replay mode
        self.replay_mode = False
        
        # Reset AI state
        self._waiting_for_ai_move = False
        self._ai_timer = 0.0
        
        # QUAN TRỌNG: Schedule AI sau khi thoát replay
        self._schedule_ai_if_needed()

    # ---------- Vòng lặp ----------

    def update(self, dt: float):
        # Cập nhật đồng hồ như GameLocalScene (hết giờ vẫn thua)
        super().update(dt)

        # QUAN TRỌNG: Không cho AI chạy khi đang replay
        if self._is_in_replay_mode():
            self._waiting_for_ai_move = False
            return

        if self.game_over or self.promotion_active:
            self._waiting_for_ai_move = False
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
    
    def handle_events(self, events):
        """Override để đảm bảo events được xử lý đúng sau replay"""
        super().handle_events(events)
        
        # QUAN TRỌNG: Không schedule AI khi đang replay
        if self._is_in_replay_mode():
            self._waiting_for_ai_move = False
            return
        
        # Sau khi xử lý events, check lại AI nếu cần
        if not self.game_over and not self.promotion_active:
            # Chỉ schedule lại nếu chưa đang chờ AI
            if not self._waiting_for_ai_move:
                self._schedule_ai_if_needed()