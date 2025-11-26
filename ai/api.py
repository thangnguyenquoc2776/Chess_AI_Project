from typing import Dict, Any, Tuple, Optional
import chess
import traceback

# Import các Agent
# Lưu ý: Giả sử bạn đã có file random_agent.py, nếu không có thì API sẽ dùng fallback
try:
    from .random_agent import RandomAgent
except ImportError:
    class RandomAgent:
        def __init__(self, seed=None): pass
        def choose_move(self, board): 
            import random
            move = random.choice(list(board.legal_moves)) if list(board.legal_moves) else None
            return move, {"info": "fallback_random"}

from .minimax.minimax_agent import (
    MinimaxAgent,
    # Import các factory functions nếu có trong file minimax_agent.py
    # Nếu không có thì logic _create_agent bên dưới sẽ tự xử lý
)


# ============================================================
# 1. FACTORY TẠO AGENT
# ============================================================

def _create_agent(agent_spec: Dict[str, Any]):
    """
    Tạo đối tượng Agent dựa trên dictionary cấu hình.
    Hỗ trợ Debug Script Opening thông qua các Level cao.
    """
    agent_type = agent_spec.get("type", "random")
    level = agent_spec.get("level", "medium")
    
    # --- RANDOM AGENT ---
    if agent_type == "random":
        seed = agent_spec.get("seed")
        return RandomAgent(seed=seed)
    
    # --- MINIMAX AGENT ---
    if agent_type == "minimax":
        
        # Xác định cấu hình dựa trên 'level' hoặc 'depth' tùy chỉnh
        depth = 3
        use_advanced = True
        use_quiescence = True
        use_ordering = True

        # Cấu hình sẵn theo Level
        if level == "easy":
            depth = 2
            use_advanced = False  # Không dùng script ở level này
        elif level == "medium":
            depth = 3
            use_advanced = True   # Bắt đầu dùng Eval Advanced (Script có thể active)
        elif level == "hard":
            depth = 4
            use_advanced = True
        elif level == "expert":
            depth = 5
            use_advanced = True
        elif level == "master":
            depth = 6
            use_advanced = True

        # Override nếu có tham số cụ thể trong agent_spec
        if "depth" in agent_spec:
            depth = agent_spec["depth"]
            # Nếu set depth thấp (1-2) thì mặc định tắt advanced trừ khi force bật
            if depth <= 2 and "use_advanced_eval" not in agent_spec:
                use_advanced = False

        if "use_advanced_eval" in agent_spec:
            use_advanced = agent_spec["use_advanced_eval"]

        # Nếu user đang debug script, tốt nhất nên dùng depth=4 hoặc 5 và advanced=True
        # Time limit logic (nếu có class TimeLimited, ở đây dùng Minimax thường làm nền)
        # time_limit = agent_spec.get("time_limit_ms") 
        
        # Tạo Agent
        # Lưu ý: constructor phải khớp với định nghĩa __init__ trong minimax_agent.py
        return MinimaxAgent(
            depth=depth,
            use_advanced_eval=use_advanced,
            use_quiescence=use_quiescence,
            use_move_ordering=use_ordering
        )
    if agent_type == "transformer":
        from .ml.agent import TransformerAgent   
        
        model_path = agent_spec.get("model_path", "models/transformer_chess.pth")
        vocab_path = agent_spec.get("vocab_path", "models/vocab.pkl")
        
        return TransformerAgent(model_path=model_path, vocab_path=vocab_path)
            
    # Fallback
    print(f"[API] Warning: Unknown type '{agent_type}', defaulting to Random.")
    return RandomAgent()


# ============================================================
# 2. MAIN API FUNCTION
# ============================================================

def choose_move_from_fen(fen: str, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hàm chính được gọi bởi Game/Server.
    
    Flow: FEN String -> Board Object -> AI Calculate -> Result Dictionary
    """
    try:
        # 1. Tạo bàn cờ từ FEN
        board = chess.Board(fen)
        
        # 2. Kiểm tra game over ngay lập tức
        if board.is_game_over():
            return {
                "uci": None,
                "info": {"error": "Game is over", "result": board.result()}
            }

        # 3. Khởi tạo AI Agent
        agent = _create_agent(agent_spec)
        
        # 4. AI Tính toán (Phần debug in console sẽ chạy ở đây)
        move, info = agent.choose_move(board)
        
        # 5. Xử lý kết quả
        if move is None or move == chess.Move.null():
             # Trường hợp AI chịu thua hoặc lỗi
            return {
                "uci": None,
                "info": {"error": "AI returned no move (Null)", **info}
            }

        if move not in board.legal_moves:
             # Trường hợp Bot "phát minh" ra nước đi sai luật (hiếm gặp nếu dùng thư viện chess)
            return {
                "uci": None,
                "info": {
                    "error": f"Illegal move generated: {move.uci()}",
                    "valid_moves": [m.uci() for m in board.legal_moves]
                }
            }

        # 6. Trả về đúng format
        return {
            "uci": move.uci(),
            "info": info  # Chứa score, nodes, time, depth...
        }

    except ValueError as e:
        return {"uci": None, "info": {"error": f"Invalid FEN: {e}"}}
    except Exception as e:
        traceback.print_exc() # In lỗi ra console để debug
        return {"uci": None, "info": {"error": f"Internal Error: {str(e)}"}}


# ============================================================
# 3. TIỆN ÍCH HỖ TRỢ UI
# ============================================================

def get_available_agents() -> Dict[str, Any]:
    return {
        "transformer": {
            "name": "Neural Net (Transformer)",
            "description": "AI học sâu",
            "config": {"type": "transformer"},
            "recommended": True,
        },

        # === CLASSIC MINIMAX BOTS ===
        "minimax_medium": {
            "name": "Bot Normal (Minimax)",
            "description": "Độ khó trung bình, dùng thuật toán Minimax truyền thống.",
            "config": {"type": "minimax", "level": "medium"},
        },
        "minimax_hard": {
            "name": "Bot Hard (Minimax)",
            "description": "Tính sâu hơn, khó thắng hơn.",
            "config": {"type": "minimax", "level": "hard"},
        },
        "minimax_master": {
            "name": "Bot Master (Minimax)",
            "description": "Rất mạnh – Minimax depth 6.",
            "config": {"type": "minimax", "level": "master"},
        },

        # Optional: Debug bot (giữ lại nếu bạn cần test script)
        "minimax_debug": {
            "name": "Debug Bot (Script Test)",
            "description": "Dùng để test opening script.",
            "config": {"type": "minimax", "level": "hard", "use_advanced_eval": True},
            "warning": "Check Console"
        },
    }

def create_ai_for_difficulty(difficulty: str) -> Dict[str, Any]:
    """Mapping đơn giản từ string -> config"""
    mapping = {
        "easy": {"type": "minimax", "level": "easy"},
        "medium": {"type": "minimax", "level": "medium"},
        "hard": {"type": "minimax", "level": "hard"},
        "transformer": {"type": "transformer"},
        "neural": {"type": "transformer"},
        "debug": {"type": "minimax", "level": "hard", "use_advanced_eval": True}
        
    }
    return mapping.get(difficulty, mapping["medium"])