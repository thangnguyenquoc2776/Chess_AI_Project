# core/board.py
import chess


class Board:
    """
    Wrapper quanh python-chess.Board, cung cấp API đơn giản
    cho GAME & AI dùng chung.
    """

    def __init__(self, fen: str | None = None):
        if fen:
            self._board = chess.Board(fen)
        else:
            self._board = chess.Board()

    # --------- Trạng thái & FEN ----------

    def export_fen(self) -> str:
        """Trả về chuỗi FEN của trạng thái hiện tại."""
        return self._board.fen()

    def import_fen(self, fen: str) -> None:
        """Load lại trạng thái từ FEN."""
        self._board = chess.Board(fen)

    # --------- Lượt đi & thông tin cơ bản ----------

    @property
    def turn_white(self) -> bool:
        """True nếu tới lượt trắng đi."""
        return self._board.turn == chess.WHITE

    def fullmove_number(self) -> int:
        """Số fullmove (1 = nước đầu tiên của trắng)."""
        return self._board.fullmove_number

    # --------- Truy vấn quân cờ ----------

    def piece_at(self, file_index: int, rank_index: int):
        """
        Lấy chess.Piece (hoặc None) tại ô (file, rank) 0-based:
        - file_index: 0..7 tương ứng a..h
        - rank_index: 0..7 tương ứng rank 1..8 (1 ở dưới nếu ta vẽ trắng ở dưới)
        """
        square = chess.square(file_index, rank_index)
        return self._board.piece_at(square)

    def piece_symbol_at(self, file_index: int, rank_index: int) -> str | None:
        """
        Trả về ký hiệu 'p','P','k','K',... hoặc None nếu ô trống.
        lowercase = quân đen, uppercase = quân trắng.
        """
        p = self.piece_at(file_index, rank_index)
        return p.symbol() if p else None

    # --------- Nước đi & luật ----------

    def legal_moves_uci(self) -> list[str]:
        """Trả về list các nước hợp lệ dạng UCI: 'e2e4', 'g1f3',..."""
        return [move.uci() for move in self._board.legal_moves]

    def apply_uci(self, uci_move: str) -> None:
        """
        Thực hiện một nước đi UCI.
        Nếu nước đi không hợp lệ sẽ raise ValueError.
        """
        move = chess.Move.from_uci(uci_move)
        if move not in self._board.legal_moves:
            raise ValueError(f"Illegal move: {uci_move}")
        self._board.push(move)

    def pop_move(self) -> None:
        """Hoàn tác một nước (nếu có)."""
        if self._board.move_stack:
            self._board.pop()

    # --------- Trạng thái kết thúc ----------

    def is_check(self) -> bool:
        return self._board.is_check()

    def is_checkmate(self) -> bool:
        return self._board.is_checkmate()

    def is_stalemate(self) -> bool:
        return self._board.is_stalemate()

    def is_insufficient_material(self) -> bool:
        return self._board.is_insufficient_material()

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def result_status(self) -> str:
        """
        Trả về:
        - 'white_win'
        - 'black_win'
        - 'draw'
        - 'ongoing'
        """
        if self._board.is_checkmate():
            # Bên tới lượt hiện tại là bên đang bị chiếu hết
            loser_white = self.turn_white
            return "black_win" if loser_white else "white_win"

        if self._board.is_stalemate() or self._board.is_insufficient_material():
            return "draw"

        # Có thể mở rộng thêm 50-move, 3-fold nếu muốn auto hòa
        return "ongoing"
