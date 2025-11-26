# game/ai_hook.py
"""
CẦU NỐI giữa GAME ENGINE và AI MODULE.

File này giúp Game Engine (dùng Board Object) nói chuyện được với 
AI Module (dùng FEN string).
"""

from __future__ import annotations
from typing import Tuple, Dict, Any, Optional

# Giả định class Board của game nằm ở core.board
# Nếu sai đường dẫn, bạn cần chỉnh lại import này
try:
    from core.board import Board
except ImportError:
    # Fallback class để tránh crash nếu chưa có core
    class Board:
        def export_fen(self): return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

from ai.api import (
    choose_move_from_fen, 
    get_available_agents,
    create_ai_for_difficulty
)

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def choose_move_for_game(
    board: Board, 
    agent_spec: dict
) -> Tuple[str | None, dict]:
    """
    Hàm chính để Game gọi AI.
    
    Args:
        board (Board): Object bàn cờ hiện tại của game.
        agent_spec (dict): Cấu hình bot (VD: {"type": "minimax", "level": "medium"})
    
    Returns:
        uci (str | None): Nước đi dạng chuỗi "e2e4" (hoặc None nếu lỗi).
        info (dict): Thông tin telemetry (score, depth, time, debug info).
    """
    
    # 1. Lấy FEN từ bàn cờ game
    # Bước này cực quan trọng để AI nhìn thấy bàn cờ giống Game
    try:
        fen = board.export_fen()
    except Exception as e:
        print(f"[AI HOOK] ❌ LỖI XUẤT FEN: {e}")
        return None, {"error": str(e)}

    # Log cho người code thấy
    # print(f"[AI HOOK] Agent: {agent_spec.get('level', 'custom')} | FEN: {fen}")

    # 2. Gọi AI qua API
    try:
        # Đây là hàm chúng ta đã viết trong ai/api.py
        result = choose_move_from_fen(fen, agent_spec)
    except Exception as e:
        print(f"[AI HOOK] ❌ LỖI GỌI AI: {e}")
        import traceback
        traceback.print_exc()
        return None, {"error": f"AI Crash: {e}"}

    # 3. Xử lý kết quả trả về
    uci = result.get("uci")     # VD: "e2e4"
    info = result.get("info", {}) # VD: {"score": 1000000, ...}

    # 4. Debug Log đặc biệt cho Script Opening
    # Nếu điểm số rất lớn (đang chạy script), log ra để biết
    score = info.get("score", 0)
    if abs(score) > 500000 and abs(score) < 2000000: # Ngưỡng điểm script
        print(f"[AI HOOK] ⚡ BOT ĐANG CHẠY SCRIPT (Score: {score}) --> Move: {uci}")
    else:
        pass
        # print(f"[AI HOOK] Move: {uci} | Score: {score} | Time: {info.get('time_ms')}ms")

    # Trả về UCI và Info cho Game Controller xử lý di chuyển
    return uci, info


# =============================================================================
# HELPER FUNCTIONS (CHO GAME UI/MENU)
# =============================================================================

def create_ai_config(difficulty: str = "medium") -> dict:
    """
    Tạo cấu hình AI theo tên độ khó.
    Hỗ trợ các từ khóa:
    - 'debug': Bot test kịch bản 4 nước.
    - 'easy', 'medium', 'hard', 'expert', 'master'.
    """
    diff = difficulty.lower()
    
    if diff == "debug":
        print("[AI HOOK] Creating DEBUG AGENT (Scripted Opening)")
        return {"type": "minimax", "level": "hard", "use_advanced_eval": True}
        
    if diff in ["easy", "medium", "hard", "expert", "master"]:
        return create_ai_for_difficulty(diff)
    
    # Mặc định
    return {"type": "minimax", "level": "medium"}


def get_ai_display_info(agent_spec: dict) -> dict:
    """
    Trả về thông tin để hiển thị lên UI (Tên bot, Winrate dự kiến...)
    """
    level = agent_spec.get("level", "unknown")
    
    info_map = {
        "easy":   {"name": "Bot Easy", "winrate": "20%"},
        "medium": {"name": "Bot Normal", "winrate": "50%"},
        "hard":   {"name": "Bot Hard", "winrate": "80%"},
        "expert": {"name": "Bot Expert", "winrate": "90%"},
        "master": {"name": "Bot Master", "winrate": "99%"},
        "debug":  {"name": "Bot Tester", "winrate": "?"},
    }
    
    return info_map.get(level, {"name": "Custom Bot", "winrate": "N/A"})