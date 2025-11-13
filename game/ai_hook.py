# game/ai_hook.py
from core.board import Board


def choose_move_for_game(board: Board, agent_spec: dict) -> tuple[str, dict]:
    """
    CẦU NỐI để GAME gọi AI.

    TEAM GAME:
        - Gọi hàm này khi tới lượt AI.
        - Truyền Board và agent_spec vào.

    TEAM AI:
        - Implement nội dung bên trong.
        - Trả về (uci_move, telemetry_info).

    Ở repo Chess_AI_Project nhưng trong khung chat GAME, ta để NotImplemented
    để nhắc đây là việc của TEAM AI.
    """
    raise NotImplementedError("TEAM AI sẽ implement choose_move_for_game()")
