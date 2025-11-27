# filepath: c:\Users\Win 10\Desktop\Update Machine learning\Chess_AI_Project\game\scenes\game_online.py
# game/scenes/game_online.py
import pygame
from typing import List, Tuple, Optional, Dict, Any

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


        self.legal_moves_uci: List[str] = []  # chỉ dùng để highlight / client-side UX

        self.legal_moves_uci: List[str] = generate_legal_moves(self.board)


        self.game_over = False
        self.game_result: str = "ongoing"
        self.game_over_reason: str = ""
        self.status_text: str = f"Room {room_id} | You are {player_color}"

        # ========= Promotion =========
        self.promotion_active: bool = False
        self.promotion_choices: Dict[str, str] = {}
        self.promotion_buttons: List[Button] = []

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

        self.game_over = True
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
        # Online hiện chưa dùng đồng hồ, giữ cho API giống local.
        pass

    # ---------- Promotion UI (local only, dùng để chọn piece cho UCI có 5 kí tự) ----------

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
        gap = int(TILE_SIZE * 0.5)

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2 + int(TILE_SIZE * 0.8)

        rect_again = pygame.Rect(0, 0, btn_w, btn_h)
        rect_again.center = (center_x - (btn_w // 2 + gap // 2), center_y)
        self.game_over_buttons.append(
            Button(rect_again, "Back to Menu", self.font_button, callback=self._on_back_to_menu)
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

            self.last_move_squares = []
            last_uci = msg.get("last_move")
            if isinstance(last_uci, str):
                (sf, sr), (tf, tr) = self._uci_to_from_to(last_uci)
                self.last_move_squares = [(sf, sr), (tf, tr)]

            turn = msg.get("turn", "white")

            # ====== CLOCK: lấy từ server ======
            tw = msg.get("time_white")
            tb = msg.get("time_black")
            if isinstance(tw, (int, float)):
                self._server_white_time = float(tw)
            if isinstance(tb, (int, float)):
                self._server_black_time = float(tb)
            self._last_clock_sync = pygame.time.get_ticks() / 1000.0

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
        if self.promotion_active and not self.game_over:
            self._handle_promotion_events(events)
            return

        if self.game_over:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._on_back_to_menu()
                for btn in self.game_over_buttons:
                    btn.handle_event(event)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._on_back_to_menu()
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
        self._update_from_network()
        # Không chạy đồng hồ local (server chưa hỗ trợ), time panel chỉ để tham khảo
         # nội suy clock để đếm ngược từng giây trên client
        if self.game_result != "ongoing":
            return  # game over thì không cần chạy clock nữa

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

        # GỌI Y HỆT LOCAL, CHỈ KHÁC LÀ capture_squares = []
        draw_board(
            surface,
            self.selected_square,      # selected_square
            self.highlight_squares,    # move_squares
            [],                        # capture_squares (online chưa tách riêng, để trống)
            self.last_move_squares,    # last_move_squares (đã set từ server)
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
