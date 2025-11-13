# save/save_manager.py
import json
from pathlib import Path
from core.board import Board

SAVE_DIR = Path("save")
SAVE_DIR.mkdir(exist_ok=True)
DEFAULT_SLOT = SAVE_DIR / "slot0.json"


def save_game(board: Board, meta: dict, slot_path: Path = DEFAULT_SLOT):
    data = {
        "fen": board.export_fen(),
        "meta": meta,
    }
    with open(slot_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(slot_path: Path = DEFAULT_SLOT) -> tuple[Board, dict] | None:
    if not slot_path.exists():
        return None

    with open(slot_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    board = Board(data["fen"])
    meta = data.get("meta", {})
    return board, meta
