# ai/minimax/eval.py
import chess

# Giá trị quân (đơn vị tuỳ, giữ nguyên tỉ lệ là được)
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
}


def evaluate(board: chess.Board) -> int:
    """
    Hàm đánh giá thế cờ, trả int:
    > 0  lợi cho White
    < 0  lợi cho Black
    = 0  cân bằng

    Phiên bản đơn giản: chỉ tính vật chất.
    Có thể nâng cấp thêm mobility, king safety, pawn structure...
    """
    # Kết thúc ván
    if board.is_checkmate():
        # Nếu là turn của bên X mà is_checkmate => X bị chiếu hết => X thua
        return -10_000_000 if board.turn else 10_000_000  # board.turn = bên đang đi

    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0

    # Duyệt từng quân
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    # Nhẹ nhẹ thưởng mobility
    score += len(list(board.legal_moves)) * 1 if board.turn == chess.WHITE else -len(list(board.legal_moves)) * 1

    return score
