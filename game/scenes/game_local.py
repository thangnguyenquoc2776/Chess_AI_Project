# game/scenes/game_local.py
import pygame
from typing import List, Tuple, Optional, Dict

from .base import SceneBase
from core.board import Board
from core.rules import generate_legal_moves, get_game_result
from game.config import (
    COLOR_BG,
    COLOR_TEXT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    FONT_SCALE,
    CHESS_TIME_LIMIT_SEC,
)
from game.input.mouse import pixel_to_board_square
from game.render.board_renderer import draw_board
from game.render.piece_renderer import draw_pieces
from game.render.hud_renderer import draw_hud
from game.render.side_panel_renderer import draw_side_panels
from game.ui.widgets import Button


class GameLocalScene(SceneBase):
    """
    Scene chơi cờ local.
    - mode = "pvp": cả hai bên là người.
    - mode = "pve": 1 bên người, 1 bên AI (sau này).
    """

    def __init__(self, app, mode: str = "pvp"):
        super().__init__(app)
        self.mode = mode

        # ----- Core state -----
        self.board = Board()  # trạng thái ván cờ
        self.font_piece = pygame.font.Font(None, int(40 * FONT_SCALE))
        self.font_hud = pygame.font.Font(None, int(32 * FONT_SCALE))

        # Ô đang chọn + highlight
        self.selected_square: Optional[Tuple[int, int]] = None
        self.highlight_squares: List[Tuple[int, int]] = []   # ô đi bình thường
        self.capture_squares: List[Tuple[int, int]] = []     # ô có thể ăn quân
        self.last_move_squares: List[Tuple[int, int]] = []   # from / to của nước cuối

        # Đếm số ply (mỗi lần một bên đi 1 nước)
        self.ply_count: int = 0

        # Đồng hồ cờ vua: mỗi bên có CHESS_TIME_LIMIT_SEC giây, đếm ngược
        self.white_time_sec: float = float(CHESS_TIME_LIMIT_SEC)
        self.black_time_sec: float = float(CHESS_TIME_LIMIT_SEC)

        # Danh sách nước hợp lệ (dưới dạng UCI)
        self.legal_moves_uci: List[str] = generate_legal_moves(self.board)

        # Trạng thái game
        self.game_over: bool = False
        self.game_result: str = "ongoing"  # 'white_win' | 'black_win' | 'draw' | 'ongoing'
        self.game_over_reason: str = ""
        self.status_text: str = ""         # "Check!", "White wins...", ...

        # ====== PHONG CẤP ======
        self.promotion_active: bool = False
        self.promotion_choices: Dict[str, str] = {}  # 'Q'/'R'/'B'/'N' -> uci
        self.promotion_buttons: List[Button] = []

        # ====== PAUSE MENU ======
        self.paused: bool = False
        self.pause_buttons: List[Button] = []

        # ====== GAME OVER OVERLAY ======
        self.game_over_buttons: List[Button] = []
        self.font_title_big = pygame.font.Font(None, int(72 * FONT_SCALE))
        self.font_title_small = pygame.font.Font(None, int(40 * FONT_SCALE))
        self.font_button = pygame.font.Font(None, int(36 * FONT_SCALE))

    # ---------- Helpers chung ----------

    @staticmethod
    def _uci_to_from_to(uci: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Chuyển UCI 'e2e4' hoặc 'e7e8q' về ((file_from, rank_from), (file_to, rank_to)).
        file: 0..7, rank: 0..7 (1..8).
        """
        file_from = ord(uci[0]) - ord("a")
        rank_from = int(uci[1]) - 1
        file_to = ord(uci[2]) - ord("a")
        rank_to = int(uci[3]) - 1
        return (file_from, rank_from), (file_to, rank_to)

    def _legal_moves_from_square(self, file: int, rank: int) -> List[str]:
        """
        Lọc các nước hợp lệ bắt đầu từ ô (file, rank).
        """
        res: List[str] = []
        for uci in self.legal_moves_uci:
            (ff, rf), _ = self._uci_to_from_to(uci)
            if ff == file and rf == rank:
                res.append(uci)
        return res

    # ---------- Cập nhật kết quả / luật ----------

    def _update_game_status(self):
        """
        Cập nhật self.game_over, self.game_result, self.status_text,...
        sau mỗi nước đi (theo luật cờ, KHÔNG tính hết giờ).
        """
        if self.game_over:
            # Nếu đã hết giờ / resign rồi thì không override nữa
            return

        status = get_game_result(self.board)
        self.game_result = status

        if status != "ongoing":
            self.game_over = True
            self.paused = False  # đã kết thúc thì không pause nữa

            # Phân loại lý do
            if self.board.is_checkmate():
                self.game_over_reason = "Checkmate"
            elif self.board.is_stalemate():
                self.game_over_reason = "Stalemate"
            elif self.board.is_insufficient_material():
                self.game_over_reason = "Insufficient material"
            else:
                self.game_over_reason = "Draw"

            if status == "white_win":
                self.status_text = "White wins by " + self.game_over_reason.lower()
            elif status == "black_win":
                self.status_text = "Black wins by " + self.game_over_reason.lower()
            else:
                self.status_text = "Draw (" + self.game_over_reason + ")"

            self._create_game_over_buttons()
        else:
            self.game_over_reason = ""
            if self.board.is_check():
                self.status_text = "Check!"
            else:
                self.status_text = ""

    def _apply_move_and_update_state(self, uci: str) -> bool:
        """
        Thực hiện nước đi uci cho self.board.
        - Cập nhật nước đi cuối để highlight.
        - Tăng ply_count.
        - Refresh legal moves + trạng thái thắng/thua/hòa.

        Trả về True nếu thành công, False nếu bị lỗi (move không hợp lệ).
        """
        src, dst = self._uci_to_from_to(uci)

        try:
            self.board.apply_uci(uci)
        except ValueError:
            self.selected_square = None
            self.highlight_squares = []
            self.capture_squares = []
            return False

        # Ghi lại nước đi cuối
        self.last_move_squares = [src, dst]

        # Tăng số ply
        self.ply_count += 1

        # Refresh nước hợp lệ + reset highlight
        self.legal_moves_uci = generate_legal_moves(self.board)
        self.selected_square = None
        self.highlight_squares = []
        self.capture_squares = []

        # Cập nhật trạng thái thắng/thua/hòa
        self._update_game_status()

        return True

    def _on_flag_timeout(self, white_flag: bool):
        """
        Một bên hết giờ (flag fall).
        white_flag = True  -> trắng hết giờ, đen thắng.
        white_flag = False -> đen hết giờ, trắng thắng.
        """
        if self.game_over:
            return

        self.game_over = True
        self.paused = False
        self.game_over_reason = "Time out"

        if white_flag:
            self.game_result = "black_win"
            self.status_text = "Black wins on time"
        else:
            self.game_result = "white_win"
            self.status_text = "White wins on time"

        self._create_game_over_buttons()

    # ---------- PAUSE MENU ----------

    def _set_paused(self, value: bool):
        """
        Bật / tắt pause.
        Không cho pause nếu game đã over hoặc đang popup phong cấp.
        """
        if self.game_over or self.promotion_active:
            self.paused = False
            self.pause_buttons.clear()
            return

        self.paused = value
        self.pause_buttons.clear()
        if value:
            self._create_pause_buttons()

    def _create_pause_buttons(self):
        """Tạo nút Resume / Back to Menu cho pause menu."""
        btn_w = int(TILE_SIZE * 3.0)
        btn_h = int(TILE_SIZE * 0.8)
        gap = int(TILE_SIZE * 0.5)

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.6)

        # Resume
        rect_resume = pygame.Rect(0, 0, btn_w, btn_h)
        rect_resume.center = (center_x - (btn_w // 2 + gap // 2), center_y)
        self.pause_buttons.append(
            Button(
                rect_resume,
                "Resume",
                self.font_button,
                callback=lambda: self._set_paused(False),
            )
        )

        # Back to Menu
        rect_menu = pygame.Rect(0, 0, btn_w, btn_h)
        rect_menu.center = (center_x + (btn_w // 2 + gap // 2), center_y)
        self.pause_buttons.append(
            Button(
                rect_menu,
                "Back to Menu",
                self.font_button,
                callback=self._on_back_to_menu,
            )
        )

    # ---------- PHONG CẤP: UI & logic ----------

    def _start_promotion_choice(self, promotion_moves: List[str]):
        """
        Gọi khi người chơi đi tới hàng phong cấp và có nhiều lựa chọn (Q/R/B/N).
        promotion_moves: list UCI dạng 'e7e8q', 'e7e8r',...
        """
        self.promotion_active = True
        self.promotion_choices.clear()
        self.promotion_buttons.clear()

        order = ["Q", "R", "B", "N"]
        for uci in promotion_moves:
            promo_char = uci[4].upper()  # q/r/b/n -> Q/R/B/N
            if promo_char in order:
                self.promotion_choices[promo_char] = uci

        btn_size = int(TILE_SIZE * 0.8)
        gap = int(TILE_SIZE * 0.2)
        total_width = len(order) * btn_size + (len(order) - 1) * gap
        start_x = (SCREEN_WIDTH - total_width) // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.5)

        for i, piece_code in enumerate(order):
            if piece_code not in self.promotion_choices:
                continue
            rect = pygame.Rect(0, 0, btn_size, btn_size)
            rect.topleft = (start_x + i * (btn_size + gap), center_y)

            def make_cb(code=piece_code):
                return lambda: self._on_promotion_choice(code)

            btn = Button(
                rect=rect,
                text=piece_code,
                font=self.font_button,
                callback=make_cb(),
            )
            self.promotion_buttons.append(btn)

    def _on_promotion_choice(self, piece_code: str):
        """
        Người chơi chọn Q/R/B/N (bằng chuột hoặc phím).
        """
        uci = self.promotion_choices.get(piece_code)
        if not uci:
            return

        success = self._apply_move_and_update_state(uci)
        if not success:
            return

        # Reset state phong cấp
        self.promotion_active = False
        self.promotion_choices.clear()
        self.promotion_buttons.clear()

        # Reset chọn ô
        self.selected_square = None
        self.highlight_squares = []
        self.capture_squares = []

    # ---------- GAME OVER OVERLAY ----------

    def _create_game_over_buttons(self):
        """Tạo nút Play Again / Back to Menu khi game over."""
        self.game_over_buttons.clear()

        btn_w = int(TILE_SIZE * 3.0)
        btn_h = int(TILE_SIZE * 0.8)
        gap = int(TILE_SIZE * 0.5)

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.8)

        # Play Again
        rect_again = pygame.Rect(0, 0, btn_w, btn_h)
        rect_again.center = (center_x - (btn_w // 2 + gap // 2), center_y)
        self.game_over_buttons.append(
            Button(rect_again, "Play Again", self.font_button, callback=self._on_play_again)
        )

        # Back to Menu
        rect_menu = pygame.Rect(0, 0, btn_w, btn_h)
        rect_menu.center = (center_x + (btn_w // 2 + gap // 2), center_y)
        self.game_over_buttons.append(
            Button(rect_menu, "Back to Menu", self.font_button, callback=self._on_back_to_menu)
        )

    def _on_play_again(self):
        """Bắt đầu lại ván mới với cùng mode."""
        self.app.change_scene(GameLocalScene, mode=self.mode)

    def _on_back_to_menu(self):
        from .menu_main import MainMenuScene
        self.app.change_scene(MainMenuScene)

    # ---------- Event handling ----------

    def handle_events(self, events: List[pygame.event.Event]):
        # Ưu tiên: nếu đang chọn phong cấp
        if self.promotion_active and not self.game_over:
            self._handle_promotion_events(events)
            return

        # Nếu game over: chỉ xử lý nút + ESC
        if self.game_over:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._on_back_to_menu()
                for btn in self.game_over_buttons:
                    btn.handle_event(event)
            return

        # Nếu đang pause: chỉ xử lý pause menu + ESC
        if self.paused:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # ESC lần nữa để tiếp tục
                    self._set_paused(False)
                for btn in self.pause_buttons:
                    btn.handle_event(event)
            return

        # Bình thường
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Trước đây ESC thoát thẳng, giờ là mở pause
                    self._set_paused(True)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _handle_promotion_events(self, events: List[pygame.event.Event]):
        """Khi đang popup chọn phong cấp: xử lý phím và chuột."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                key_map = {
                    pygame.K_q: "Q",
                    pygame.K_r: "R",
                    pygame.K_b: "B",
                    pygame.K_n: "N",
                }
                if event.key in key_map:
                    self._on_promotion_choice(key_map[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.promotion_buttons:
                    btn.handle_event(event)

    def _handle_left_click(self, pos: Tuple[int, int]):
        sq = pixel_to_board_square(*pos)
        if sq is None:
            self.selected_square = None
            self.highlight_squares = []
            self.capture_squares = []
            return

        file, rank = sq
        piece_symbol = self.board.piece_symbol_at(file, rank)

        if self.selected_square is None:
            # Chưa chọn quân
            if not piece_symbol:
                return

            is_white_piece = piece_symbol.isupper()
            if is_white_piece != self.board.turn_white:
                return

            self.selected_square = (file, rank)
            moves_from = self._legal_moves_from_square(file, rank)

            normal_squares: List[Tuple[int, int]] = []
            capture_squares: List[Tuple[int, int]] = []

            for uci in moves_from:
                _, (tf, tr) = self._uci_to_from_to(uci)
                # Ô đích hiện tại có quân đối phương? -> nước ăn
                dest_piece = self.board.piece_symbol_at(tf, tr)
                if dest_piece and (dest_piece.isupper() != self.board.turn_white):
                    capture_squares.append((tf, tr))
                else:
                    normal_squares.append((tf, tr))

            self.highlight_squares = normal_squares
            self.capture_squares = capture_squares
            return

        else:
            # Đã chọn quân, giờ chọn đích
            src_file, src_rank = self.selected_square

            if (file, rank) == (src_file, src_rank):
                # Bỏ chọn
                self.selected_square = None
                self.highlight_squares = []
                self.capture_squares = []
                return

            candidate_moves = self._legal_moves_from_square(src_file, src_rank)

            promotion_moves: List[str] = []
            normal_move: Optional[str] = None

            for uci in candidate_moves:
                (_, _), (tf, tr) = self._uci_to_from_to(uci)
                if tf == file and tr == rank:
                    if len(uci) == 5:
                        promotion_moves.append(uci)
                    else:
                        normal_move = uci

            if promotion_moves:
                # Bật UI chọn phong cấp
                self._start_promotion_choice(promotion_moves)
                return

            if normal_move is None:
                self.selected_square = None
                self.highlight_squares = []
                self.capture_squares = []
                return

            success = self._apply_move_and_update_state(normal_move)
            if not success:
                self.selected_square = None
                self.highlight_squares = []
                self.capture_squares = []
                return

    # ---------- Update & Render ----------

    def update(self, dt: float):
        """
        dt: số giây trôi qua giữa 2 frame (GameApp truyền vào).
        Dùng để cập nhật đồng hồ cờ vua (đếm ngược).
        """
        if self.game_over or self.promotion_active or self.paused:
            return

        if self.board.turn_white:
            self.white_time_sec -= dt
            if self.white_time_sec <= 0:
                self.white_time_sec = 0
                self._on_flag_timeout(white_flag=True)
        else:
            self.black_time_sec -= dt
            if self.black_time_sec <= 0:
                self.black_time_sec = 0
                self._on_flag_timeout(white_flag=False)

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Bàn + quân
        draw_board(
            surface,
            self.selected_square,
            self.highlight_squares,
            self.last_move_squares,
            self.capture_squares,  # ô ăn quân
        )
        draw_pieces(surface, self.board, self.font_piece)

        # HUD trên cùng (giữ cho kiến trúc thống nhất)
        draw_hud(
            surface,
            self.board,
            self.font_hud,
            self.status_text,
            game_over=self.game_over,
            game_result=self.game_result,
        )

        # Panel 2 bên: info + clock
        draw_side_panels(
            surface,
            self.font_hud,
            self.white_time_sec,
            self.black_time_sec,
            self.ply_count,
            self.board.turn_white,
            self.status_text,
            "",
        )

        # Overlay ưu tiên nằm trên cùng
        if self.game_over:
            self._render_game_over_overlay(surface)
        elif self.promotion_active:
            self._render_promotion_popup(surface)
        elif self.paused:
            self._render_pause_overlay(surface)

    # ---------- Render overlay ----------

    def _render_promotion_popup(self, surface: pygame.Surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        text = "Choose promotion: Q / R / B / N"
        text_surf = self.font_hud.render(text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 0.6))
        )
        surface.blit(text_surf, text_rect)

        for btn in self.promotion_buttons:
            btn.draw(surface)

    def _render_game_over_overlay(self, surface: pygame.Surface):
        # Lớp mờ
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Tiêu đề lớn
        if self.game_result == "white_win":
            title = "WHITE WINS!"
        elif self.game_result == "black_win":
            title = "BLACK WINS!"
        elif self.game_result == "draw":
            title = "DRAW"
        else:
            title = "GAME OVER"

        title_surf = self.font_title_big.render(title, True, COLOR_TEXT)
        title_rect = title_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 1.2))
        )
        surface.blit(title_surf, title_rect)

        # Lý do (checkmate, stalemate, time out,...)
        if self.game_over_reason:
            reason_surf = self.font_title_small.render(self.game_over_reason, True, COLOR_TEXT)
            reason_rect = reason_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 0.4))
            )
            surface.blit(reason_surf, reason_rect)

        # Nút
        for btn in self.game_over_buttons:
            btn.draw(surface)

    def _render_pause_overlay(self, surface: pygame.Surface):
        """Overlay khi pause: tối nền + chữ PAUSED + nút Resume / Back."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Tiêu đề
        title_surf = self.font_title_big.render("PAUSED", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 1.2))
        )
        surface.blit(title_surf, title_rect)

        subtitle_surf = self.font_title_small.render("Local game", True, COLOR_TEXT)
        subtitle_rect = subtitle_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 0.6))
        )
        surface.blit(subtitle_surf, subtitle_rect)

        for btn in self.pause_buttons:
            btn.draw(surface)
