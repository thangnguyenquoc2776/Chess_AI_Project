# game/scenes/game_online.py
import pygame
from typing import List, Tuple, Optional, Dict, Any

from .base import SceneBase
from core.board import Board
from core.rules import generate_legal_moves
from game.config import (
    COLOR_BG,
    COLOR_TEXT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    FONT_SCALE,
)
from game.input.mouse import pixel_to_board_square
from game.render.board_renderer import draw_board
from game.render.piece_renderer import draw_pieces
from game.render.hud_renderer import draw_hud
from game.render.side_panel_renderer import draw_side_panels
from game.ui.widgets import Button
from game.network_client import NetworkClient


class GameOnlineScene(SceneBase):
    """
    Scene chơi cờ online 1v1, sync với server.
    - Không tự apply move local, mọi thứ theo state từ server.
    """

    def __init__(
        self,
        app,
        network_client: NetworkClient,
        room_id: str,
        player_color: str,  # "white" hoặc "black"
    ):
        super().__init__(app)

        self.client = network_client
        self.room_id = room_id
        self.player_color = player_color  # "white" / "black"

        # ----- Core board state -----
        self.board = Board()
        self.font_piece = pygame.font.Font(None, int(40 * FONT_SCALE))
        self.font_hud = pygame.font.Font(None, int(32 * FONT_SCALE))

        self.selected_square: Optional[Tuple[int, int]] = None
        self.highlight_squares: List[Tuple[int, int]] = []
        self.last_move_squares: List[Tuple[int, int]] = []

        self.ply_count: int = 0  # có thể suy ra từ FEN fullmove nếu muốn

        # Thời gian: giá trị hiển thị (nội suy từ server)
        self.white_time_sec: float = 0.0
        self.black_time_sec: float = 0.0

        # Bản gốc từ server + mốc sync để nội suy
        self._server_white_time: float = 0.0
        self._server_black_time: float = 0.0
        self._last_clock_sync: float = 0.0  # giây, pygame.time.get_ticks()/1000.0

        # Legal moves client-side (chỉ để highlight UX)
        self.legal_moves_uci: List[str] = generate_legal_moves(self.board)

        # Trạng thái game
        self.game_over = False
        self.game_result: str = "ongoing"
        self.game_over_reason: str = ""
        self.status_text: str = f"Room {room_id} | You are {player_color}"

        # ========= Promotion =========
        self.promotion_active: bool = False
        self.promotion_choices: Dict[str, str] = {}
        self.promotion_buttons: List[Button] = []

        # ========= Pause menu =========
        self.paused: bool = False
        self.pause_buttons: List[Button] = []

        # ========= Game over overlay =========
        self.game_over_buttons: List[Button] = []
        self.font_title_big = pygame.font.Font(None, int(72 * FONT_SCALE))
        self.font_title_small = pygame.font.Font(None, int(40 * FONT_SCALE))
        self.font_button = pygame.font.Font(None, int(36 * FONT_SCALE))

    # ---------- Helpers ----------

    @staticmethod
    def _uci_to_from_to(uci: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        file_from = ord(uci[0]) - ord("a")
        rank_from = int(uci[1]) - 1
        file_to = ord(uci[2]) - ord("a")
        rank_to = int(uci[3]) - 1
        return (file_from, rank_from), (file_to, rank_to)

    def _legal_moves_from_square(self, file: int, rank: int) -> List[str]:
        res: List[str] = []
        for uci in self.legal_moves_uci:
            (ff, rf), _ = self._uci_to_from_to(uci)
            if ff == file and rf == rank:
                res.append(uci)
        return res

    # ---------- Game status (theo server) ----------

    def _update_game_status_from_server(self, result: str):
        """
        Server gửi result trực tiếp: 'white_win' | 'black_win' | 'draw' | 'ongoing'.
        Ta dùng để set game_over + text.
        """
        self.game_result = result

        if result == "ongoing":
            self.game_over = False
            self.game_over_reason = ""
            return

        # Nếu server báo ván đã kết thúc -> tắt pause luôn
        self.game_over = True
        self.paused = False
        self.pause_buttons.clear()

        if result == "white_win":
            self.status_text = "White wins"
        elif result == "black_win":
            self.status_text = "Black wins"
        elif result == "draw":
            self.status_text = "Draw"
        else:
            self.status_text = "Game over"

        # Không có detail từ server, tạm để reason trống
        self.game_over_reason = ""
        self._create_game_over_buttons()

    def _on_flag_timeout(self, white_flag: bool):
        # Online hiện đồng hồ do server quyết định, nên client không tự xử lý.
        pass

    # ---------- Pause menu ----------

    def _set_paused(self, value: bool):
        """
        Bật / tắt pause.
        - Không pause khi game đã over.
        - Hạn chế pause trong lúc đang popup phong cấp để tránh bug input.
        """
        if self.game_over:
            self.paused = False
            self.pause_buttons.clear()
            return
        if self.promotion_active:
            # bắt chọn phong cấp xong đã, rồi mới cho pause
            self.paused = False
            self.pause_buttons.clear()
            return

        self.paused = value
        self.pause_buttons.clear()
        if value:
            self._create_pause_buttons()

    def _create_pause_buttons(self):
        """
        Nút trong pause menu:
        - Resume
        - Offer Draw (gửi message lên server)
        - Resign (đầu hàng)
        - Back to Menu
        """
        btn_w = int(TILE_SIZE * 3.0)
        btn_h = int(TILE_SIZE * 0.8)
        gap_x = int(TILE_SIZE * 0.3)
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.8)

        labels_callbacks = [
            ("Resume", lambda: self._set_paused(False)),
            ("Offer Draw", self._on_offer_draw),
            ("Resign", self._on_resign),
            ("Back to Menu", self._on_back_to_menu),
        ]

        total_width = 4 * btn_w + 3 * gap_x
        start_x = center_x - total_width // 2

        self.pause_buttons.clear()
        for i, (label, cb) in enumerate(labels_callbacks):
            rect = pygame.Rect(0, 0, btn_w, btn_h)
            rect.center = (start_x + i * (btn_w + gap_x) + btn_w // 2, center_y)
            self.pause_buttons.append(Button(rect, label, self.font_button, callback=cb))

    def _on_offer_draw(self):
        """Gửi yêu cầu hoà lên server (nếu server hỗ trợ)."""
        if not self.client.connected:
            self.status_text = "Disconnected"
        else:
            try:
                self.client.send_message({"type": "offer_draw"})
                self.status_text = "Draw offer sent"
            except Exception:
                self.status_text = "Failed to send draw offer"
        # không auto đóng pause cũng được, nhưng cho gọn:
        self._set_paused(False)

    def _on_resign(self):
        """
        Gửi đầu hàng lên server.
        Kết quả thật do server báo lại qua message 'state'.
        """
        if not self.client.connected:
            self.status_text = "Disconnected"
        else:
            try:
                self.client.send_message({"type": "resign"})
                self.status_text = "You resigned (waiting server)"
            except Exception:
                self.status_text = "Failed to send resign"
        self._set_paused(False)

    # ---------- Promotion UI ----------

    def _start_promotion_choice(self, promotion_moves: List[str]):
        self.promotion_active = True
        self.promotion_choices.clear()
        self.promotion_buttons.clear()

        order = ["Q", "R", "B", "N"]
        for uci in promotion_moves:
            promo_char = uci[4].upper()
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
        uci = self.promotion_choices.get(piece_code)
        if not uci:
            return

        self._send_move(uci)
        # Đóng UI; board sẽ update khi server gửi state mới
        self.promotion_active = False
        self.promotion_choices.clear()
        self.promotion_buttons.clear()
        self.selected_square = None
        self.highlight_squares = []

    # ---------- Game over overlay ----------

    def _create_game_over_buttons(self):
        self.game_over_buttons.clear()

        btn_w = int(TILE_SIZE * 3.0)
        btn_h = int(TILE_SIZE * 0.8)
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.8)

        rect_menu = pygame.Rect(0, 0, btn_w, btn_h)
        rect_menu.center = (center_x, center_y)
        self.game_over_buttons.append(
            Button(rect_menu, "Back to Menu", self.font_button, callback=self._on_back_to_menu)
        )

    def _on_back_to_menu(self):
        from .menu_main import MainMenuScene
        if self.client.connected:
            self.client.close()
        self.app.change_scene(MainMenuScene)

    # ---------- Networking ----------

    def _handle_server_message(self, msg: Dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == "state":
            fen = msg.get("fen")
            if isinstance(fen, str):
                self.board.import_fen(fen)

            # Nước đi cuối
            self.last_move_squares = []
            last_uci = msg.get("last_move")
            if isinstance(last_uci, str):
                (sf, sr), (tf, tr) = self._uci_to_from_to(last_uci)
                self.last_move_squares = [(sf, sr), (tf, tr)]

            turn = msg.get("turn", "white")

            # ====== CLOCK: lấy từ server + set mốc sync ======
            tw = msg.get("time_white")
            tb = msg.get("time_black")
            if isinstance(tw, (int, float)):
                self._server_white_time = float(tw)
            if isinstance(tb, (int, float)):
                self._server_black_time = float(tb)
            self._last_clock_sync = pygame.time.get_ticks() / 1000.0

            # Giá trị hiển thị ban đầu = giá trị server
            self.white_time_sec = self._server_white_time
            self.black_time_sec = self._server_black_time

            self.status_text = f"Your color: {self.player_color} | Turn: {turn}"

            result = msg.get("result", "ongoing")
            self._update_game_status_from_server(result)

            # Cập nhật legal moves client-side (chỉ để highlight)
            self.legal_moves_uci = generate_legal_moves(self.board)

        elif mtype == "move_rejected":
            reason = msg.get("reason", "unknown")
            self.status_text = f"Move rejected: {reason}"

        elif mtype == "error":
            self.status_text = f"Error: {msg.get('message', 'unknown')}"

    def _update_from_network(self) -> None:
        if not self.client.connected:
            self.status_text = "Disconnected"
            return
        for msg in self.client.poll_messages():
            self._handle_server_message(msg)

    def _is_player_turn(self) -> bool:
        # Dựa trên state board: turn_white
        if self.game_result != "ongoing":
            return False
        board_turn = "white" if self.board.turn_white else "black"
        return board_turn == self.player_color

    def _send_move(self, uci: str) -> None:
        if not self.client.connected:
            self.status_text = "Disconnected"
            return
        if not self._is_player_turn():
            self.status_text = "Not your turn"
            return
        try:
            self.client.send_message({"type": "move", "uci": uci})
        except Exception:
            self.status_text = "Failed to send move"

    # ---------- Event handling ----------

    def handle_events(self, events: List[pygame.event.Event]):
        # 1. Đang popup phong cấp
        if self.promotion_active and not self.game_over:
            self._handle_promotion_events(events)
            return

        # 2. Game over -> chỉ xử lý overlay + ESC
        if self.game_over:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._on_back_to_menu()
                for btn in self.game_over_buttons:
                    btn.handle_event(event)
            return

        # 3. Đang pause -> chỉ xử lý nút pause + ESC (resume)
        if self.paused:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._set_paused(False)
                for btn in self.pause_buttons:
                    btn.handle_event(event)
            return

        # 4. Bình thường
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # online: ESC -> pause, không thoát thẳng
                    self._set_paused(True)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _handle_promotion_events(self, events: List[pygame.event.Event]):
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
        if not self._is_player_turn():
            return

        sq = pixel_to_board_square(*pos)
        if sq is None:
            self.selected_square = None
            self.highlight_squares = []
            return

        file, rank = sq
        piece_symbol = self.board.piece_symbol_at(file, rank)

        if self.selected_square is None:
            if not piece_symbol:
                return

            is_white_piece = piece_symbol.isupper()
            if (is_white_piece and self.player_color != "white") or (
                not is_white_piece and self.player_color != "black"
            ):
                return

            # Chỉ chọn quân khi đúng lượt mình
            if (self.player_color == "white" and not self.board.turn_white) or (
                self.player_color == "black" and self.board.turn_white
            ):
                return

            self.selected_square = (file, rank)
            moves_from = self._legal_moves_from_square(file, rank)
            dest_squares: List[Tuple[int, int]] = []
            for uci in moves_from:
                _, (tf, tr) = self._uci_to_from_to(uci)
                dest_squares.append((tf, tr))
            self.highlight_squares = dest_squares
        else:
            src_file, src_rank = self.selected_square

            if (file, rank) == (src_file, src_rank):
                self.selected_square = None
                self.highlight_squares = []
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
                self._start_promotion_choice(promotion_moves)
                return

            if normal_move is None:
                self.selected_square = None
                self.highlight_squares = []
                return

            # Gửi move lên server
            self._send_move(normal_move)

            # Reset chọn ô (board sẽ update khi state mới tới)
            self.selected_square = None
            self.highlight_squares = []

    # ---------- Update & Render ----------

    def update(self, dt: float):
        # Online: luôn update mạng & clock, kể cả khi pause
        self._update_from_network()

        if self.game_result != "ongoing":
            return  # game over thì không cần nội suy clock nữa

        # Nội suy clock để đếm ngược từng giây trên client
        now = pygame.time.get_ticks() / 1000.0
        elapsed = max(0.0, now - self._last_clock_sync)

        # lượt hiện tại dựa trên board
        turn_color = "white" if self.board.turn_white else "black"

        if turn_color == "white":
            self.white_time_sec = max(self._server_white_time - elapsed, 0.0)
            self.black_time_sec = self._server_black_time
        else:
            self.black_time_sec = max(self._server_black_time - elapsed, 0.0)
            self.white_time_sec = self._server_white_time

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Gọi giống local: selected, move_squares, last_move_squares, capture_squares
        draw_board(
            surface,
            self.selected_square,
            self.highlight_squares,
            self.last_move_squares,
            [],  # capture_squares: online chưa tách riêng
        )

        draw_pieces(surface, self.board, self.font_piece)

        draw_hud(
            surface,
            self.board,
            self.font_hud,
            self.status_text,
            game_over=self.game_over,
            game_result=self.game_result,
        )

        draw_side_panels(
            surface,
            self.font_hud,
            self.white_time_sec,
            self.black_time_sec,
            self.ply_count,
            self.board.turn_white,
            self.status_text,
        )

        if self.game_over:
            self._render_game_over_overlay(surface)
        elif self.promotion_active:
            self._render_promotion_popup(surface)
        elif self.paused:
            self._render_pause_overlay(surface)

    # ---------- Overlays ----------

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
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

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

        if self.game_over_reason:
            reason_surf = self.font_title_small.render(self.game_over_reason, True, COLOR_TEXT)
            reason_rect = reason_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 0.4))
            )
            surface.blit(reason_surf, reason_rect)

        for btn in self.game_over_buttons:
            btn.draw(surface)

    def _render_pause_overlay(self, surface: pygame.Surface):
        """Overlay khi pause online: tối nền + PAUSED + nút menu."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        title_surf = self.font_title_big.render("PAUSED", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 1.2))
        )
        surface.blit(title_surf, title_rect)

        subtitle = "Online game (server still running)"
        subtitle_surf = self.font_title_small.render(subtitle, True, COLOR_TEXT)
        subtitle_rect = subtitle_surf.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - int(TILE_SIZE * 0.6))
        )
        surface.blit(subtitle_surf, subtitle_rect)

        for btn in self.pause_buttons:
            btn.draw(surface)
