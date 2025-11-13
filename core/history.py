# core/history.py
from collections import Counter


class FenHistory:
    """
    Lưu lịch sử FEN để kiểm tra 3-fold repetition, nếu sau này cần.
    TEAM GAME/AI có thể dùng để kiểm soát hòa theo luật.
    """

    def __init__(self):
        self._fen_list: list[str] = []

    def push(self, fen: str) -> None:
        self._fen_list.append(fen)

    def pop(self) -> None:
        if self._fen_list:
            self._fen_list.pop()

    def count_fen(self, fen: str) -> int:
        return Counter(self._fen_list)[fen]
