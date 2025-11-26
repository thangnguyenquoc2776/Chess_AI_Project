import chess

# ============================================================
# CONFIG CỨNG
# ============================================================
SCRIPT_BONUS = 1_000_000   # Điểm thưởng cưỡng bức
MAX_SCRIPT_PLY = 20        # QUAN TRỌNG: Tăng lên 20 để Search Depth không bị mất dấu script

# Giá trị quân cờ cơ bản (Fallback)
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, 
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

def evaluate(board: chess.Board) -> int:
    """Normal eval wrapper"""
    return _evaluate_normal_logic(board)

def evaluate_advanced(board: chess.Board) -> int:
    """
    Evaluation thông minh có Scripted Opening.
    
    SỬA LỖI QUAN TRỌNG: 
    Bot không được quên mục tiêu Script khi đào sâu suy nghĩ (Minimax Depth).
    Do đó ta kiểm tra điều kiện script một cách rộng hơn (Ply <= 20).
    """
    
    # Chỉ chạy script trong giai đoạn khai cuộc (Fullmove < 8)
    # Ply kiểm tra rộng ra để cover leaf-nodes của thuật toán tìm kiếm
    if board.fullmove_number <= 8:
        script_score = _evaluate_scripted_targets(board)
        
        # Nếu đạt được ít nhất một mục tiêu trong script, dùng điểm script này
        if abs(script_score) >= SCRIPT_BONUS:
            # Cộng thêm một chút eval thường để bot phân biệt các biến thể cùng điểm script
            return script_score + (_evaluate_normal_logic(board) // 100)

    # Hết script thì đánh giá bình thường
    return _evaluate_normal_logic(board)


def _evaluate_scripted_targets(board: chess.Board) -> int:
    score = 0
    
    # --- TRẮNG (WHITE) ---
    
    # 1. Pawn g3
    if board.piece_at(chess.G3) == chess.Piece(chess.PAWN, chess.WHITE):
        score += SCRIPT_BONUS

    # 2. Knight f3
    if board.piece_at(chess.F3) == chess.Piece(chess.KNIGHT, chess.WHITE):
        score += SCRIPT_BONUS
        
    # 3. Bishop g2
    if board.piece_at(chess.G2) == chess.Piece(chess.BISHOP, chess.WHITE):
        score += SCRIPT_BONUS

    # 4. CASTLE WHITE (King g1 + Rook f1)
    # SỬA LỖI: Kiểm tra thêm Xe ở f1 để đảm bảo là Castle chứ không phải King đi bộ
    w_king_ok = (board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE))
    w_rook_ok = (board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE))
    
    if w_king_ok and w_rook_ok:
        # Điểm rất cao để ép buộc động tác này
        score += SCRIPT_BONUS * 2
    elif (w_king_ok and not w_rook_ok) or bool(board.castling_rights & chess.BB_H1):
        # PHẠT NẶNG: Nếu Vua ở g1 mà Xe không ở f1 (tức là đi bộ), trừ điểm
        # để bot thấy đi bộ là ngu ngốc so với nhập thành
        score -= SCRIPT_BONUS


    # --- ĐEN (BLACK) ---
    
    # 1. Pawn b6
    if board.piece_at(chess.B6) == chess.Piece(chess.PAWN, chess.BLACK):
        score -= SCRIPT_BONUS

    # 2. Knight c6
    if board.piece_at(chess.C6) == chess.Piece(chess.KNIGHT, chess.BLACK):
        score -= SCRIPT_BONUS

    # 3. Bishop b7
    if board.piece_at(chess.B7) == chess.Piece(chess.BISHOP, chess.BLACK):
        score -= SCRIPT_BONUS

    # 4. CASTLE BLACK (Kingside: King g8 + Rook f8)
    b_king_ok = (board.piece_at(chess.G8) == chess.Piece(chess.KING, chess.BLACK))
    b_rook_ok = (board.piece_at(chess.F8) == chess.Piece(chess.ROOK, chess.BLACK))
    
    if b_king_ok and b_rook_ok:
        score -= SCRIPT_BONUS * 2
    elif b_king_ok and not b_rook_ok or bool(board.castling_rights & chess.BB_A1):
        # Phạt nếu đen đi bộ vua
        score += SCRIPT_BONUS

    return score

def _evaluate_normal_logic(board: chess.Board) -> int:
    """Logic đánh giá cờ bình thường (khi hết script)"""
    if board.is_checkmate():
        if board.turn: return -9999999 # Turn = True (White) bị checkmate -> Black win -> Negative big
        else: return 9999999
        
    score = 0
    
    # Material
    score += _eval_material(board)
    
    # Vị trí quân cơ bản (Mobility / Control Center)
    score += board.legal_moves.count() * 5 if board.turn == chess.WHITE else -board.legal_moves.count() * 5
    
    return score

def _eval_material(board: chess.Board) -> int:
    s = 0
    for pt, val in PIECE_VALUES.items():
        if pt == chess.KING: continue
        s += len(board.pieces(pt, chess.WHITE)) * val
        s -= len(board.pieces(pt, chess.BLACK)) * val
    return s