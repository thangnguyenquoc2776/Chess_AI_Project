import socket
import threading
import json
import uuid
import time
from typing import Dict, Optional

# Import core chess logic
from core.board import Board
from core.rules import generate_legal_moves, get_game_result

HOST = "0.0.0.0"
PORT = 5000


class GameRoom:
    """
    Một phòng cờ vua cho tối đa 2 người chơi.
    Server giữ Board là source of truth.
    """

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.lock = threading.Lock()
        self.white_conn: Optional[socket.socket] = None
        self.black_conn: Optional[socket.socket] = None

        # Chess board & state
        self.board: Optional[Board] = None
        self.started: bool = False

        # Kết quả ván đấu do server quản lý:
        # "ongoing" | "white_win" | "black_win" | "draw"
        self.result: str = "ongoing"

        # Clock (seconds)
        self.initial_time_sec: float = 300.0  # 5 phút, tuỳ bạn chỉnh
        self.white_time_left: float = self.initial_time_sec
        self.black_time_left: float = self.initial_time_sec
        self.last_update_ts: float = time.time()
        self.turn_color: str = "white"

    def add_player(self, conn: socket.socket) -> Optional[str]:
        """
        Thêm player vào phòng.
        Trả về 'white' hoặc 'black' nếu join thành công, None nếu phòng đã full.
        """
        with self.lock:
            if self.white_conn is None:
                self.white_conn = conn
                return "white"
            elif self.black_conn is None:
                self.black_conn = conn
                return "black"
            else:
                return None

    def other_conn(self, conn: socket.socket) -> Optional[socket.socket]:
        with self.lock:
            if conn is self.white_conn:
                return self.black_conn
            if conn is self.black_conn:
                return self.white_conn
            return None

    def remove_conn(self, conn: socket.socket):
        with self.lock:
            if conn is self.white_conn:
                self.white_conn = None
            elif conn is self.black_conn:
                self.black_conn = None

    def is_empty(self) -> bool:
        with self.lock:
            return self.white_conn is None and self.black_conn is None

    def is_full(self) -> bool:
        with self.lock:
            return self.white_conn is not None and self.black_conn is not None

    def player_count(self) -> int:
        with self.lock:
            c = 0
            if self.white_conn is not None:
                c += 1
            if self.black_conn is not None:
                c += 1
            return c

    # ----- Chess-specific helpers -----

    def ensure_started(self):
        """
        Khởi tạo board khi phòng đã đủ 2 người mà chưa start.
        """
        with self.lock:
            if not self.started:
                self.board = Board()  # new game
                self.started = True
                self.result = "ongoing"
                self.white_time_left = self.initial_time_sec
                self.black_time_left = self.initial_time_sec
                self.last_update_ts = time.time()
                self.turn_color = "white"
                print(f"[ROOM] Board created for room {self.room_id}, game started")

    def _update_clock(self):
        """
        Cập nhật clock dựa trên thời gian thực cho bên đang tới lượt.
        Gọi mỗi lần trước khi xử lý nước đi mới.
        """
        if not self.started or self.board is None:
            return

        now = time.time()
        dt = now - self.last_update_ts
        self.last_update_ts = now

        # turn_color dựa trên board.turn_white
        self.turn_color = "white" if self.board.turn_white else "black"

        if self.turn_color == "white":
            self.white_time_left -= dt
        else:
            self.black_time_left -= dt

        # clamp
        if self.white_time_left < 0:
            self.white_time_left = 0
        if self.black_time_left < 0:
            self.black_time_left = 0

    def _check_flag(self) -> Optional[str]:
        """
        Kiểm tra hết giờ: trả về 'white_win', 'black_win' hoặc None
        (có thể trả 'draw' nếu cả 2 hết giờ).
        """
        if self.white_time_left <= 0 and self.black_time_left <= 0:
            # hoà do cả 2 hết giờ, tuỳ bạn muốn xử lý
            return "draw"
        if self.white_time_left <= 0:
            return "black_win"
        if self.black_time_left <= 0:
            return "white_win"
        return None

    def current_turn_color(self) -> str:
        """
        'white' nếu tới lượt trắng, 'black' nếu tới lượt đen.
        """
        # Nếu vì lý do gì đó board chưa tạo, default trắng
        if self.board is None:
            return "white"
        return "white" if self.board.turn_white else "black"

    def make_move(self, color: str, uci: str) -> dict:
        """
        Thực hiện nước đi nếu hợp lệ & đúng lượt.
        Trả về dict state trả cho client.
        Có thể raise ValueError nếu illegal move hoặc game đã kết thúc.
        """
        # Nếu game đã kết thúc rồi thì không cho đi nữa
        if self.result != "ongoing":
            raise ValueError("game_already_over")

        # nếu vì lý do gì đó chưa start -> chặn
        if self.board is None or not self.started:
            print(f"[DEBUG] make_move called but game not started: board={self.board}, started={self.started}")
            raise ValueError("game_not_started")

        # Cập nhật clock cho lượt hiện tại trước khi xử lý move
        self._update_clock()

        # Kiểm tra hết giờ trước khi cho đi
        flag_result = self._check_flag()
        if flag_result is not None:
            # game đã hết giờ, không cho đi nữa
            self.result = flag_result
            raise ValueError("time_over")

        # Check đúng lượt
        expected_color = self.current_turn_color()
        if color != expected_color:
            raise ValueError("not_your_turn")

        legal_moves = generate_legal_moves(self.board)
        if uci not in legal_moves:
            raise ValueError("illegal_move")

        # Apply move
        self.board.apply_uci(uci)

        # Sau khi đi xong, cập nhật lượt & check kết quả (chiếu hết, hoà...)
        fen = self.board.export_fen()
        result = get_game_result(self.board)

        # Nếu game chưa kết thúc do nước cờ, vẫn cần check flag 1 lần nữa
        if result == "ongoing":
            flag_result = self._check_flag()
            if flag_result is not None:
                result = flag_result

        self.result = result

        state = {
            "type": "state",
            "room_id": self.room_id,
            "fen": fen,
            "turn": self.current_turn_color(),   # dựa trên board.turn_white
            "result": self.result,
            "last_move": uci,
            "time_white": self.white_time_left,
            "time_black": self.black_time_left,
        }
        return state


# Global room registry
rooms: Dict[str, GameRoom] = {}
rooms_lock = threading.Lock()


def create_room() -> GameRoom:
    room_id = uuid.uuid4().hex[:8]  # short id
    room = GameRoom(room_id)
    with rooms_lock:
        rooms[room_id] = room
    print(f"[ROOM] Created room {room_id}")
    return room


def get_room(room_id: str) -> Optional[GameRoom]:
    with rooms_lock:
        return rooms.get(room_id)


def delete_room_if_empty(room: GameRoom):
    with rooms_lock:
        if room.is_empty() and room.room_id in rooms:
            print(f"[ROOM] Deleting empty room {room.room_id}")
            del rooms[room.room_id]


# ----- Networking helpers -----

def send_json(conn: socket.socket, msg: dict):
    try:
        data = json.dumps(msg) + "\n"
        conn.sendall(data.encode("utf-8"))
    except OSError as e:
        print(f"[WARN] send_json error: {e}")
        pass


# ----- Per-connection handler -----

def handle_client(conn: socket.socket, addr):
    print(f"[INFO] New connection from {addr}")
    buffer = ""
    current_room: Optional[GameRoom] = None
    player_color: Optional[str] = None  # 'white' hoặc 'black'

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                print(f"[INFO] Connection closed by {addr}")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[WARN] Invalid JSON from {addr}: {line}")
                    send_json(conn, {"type": "error", "message": "invalid_json"})
                    continue

                msg_type = msg.get("type")

                if msg_type == "join":
                    current_room, player_color = handle_join(conn, addr, msg)
                elif msg_type == "move":
                    if current_room is None or player_color is None:
                        send_json(conn, {"type": "error", "message": "not_in_room"})
                    else:
                        handle_move(conn, addr, current_room, player_color, msg)
                elif msg_type == "list_rooms":
                    handle_list_rooms(conn)
                elif msg_type == "resign":
                    if current_room is None or player_color is None:
                        send_json(conn, {"type": "error", "message": "not_in_room"})
                    else:
                        handle_resign(conn, addr, current_room, player_color)
                elif msg_type == "offer_draw":
                    if current_room is None or player_color is None:
                        send_json(conn, {"type": "error", "message": "not_in_room"})
                    else:
                        handle_offer_draw(conn, addr, current_room, player_color)
                else:
                    send_json(conn, {"type": "error", "message": "unknown_message_type"})

    except ConnectionResetError:
        print(f"[INFO] Connection reset by {addr}")
    finally:
        # Cleanup if in room
        if current_room is not None:
            current_room.remove_conn(conn)
            delete_room_if_empty(current_room)
        conn.close()
        print(f"[INFO] Connection handler for {addr} terminated")


def handle_join(conn: socket.socket, addr, msg: dict) -> tuple[Optional[GameRoom], Optional[str]]:
    game_id = msg.get("game_id")
    if game_id in ("", None):
        # create new room
        room = create_room()
    else:
        room = get_room(str(game_id))
        if room is None:
            send_json(conn, {"type": "join_failed", "reason": "room_not_found"})
            return None, None

    color = room.add_player(conn)
    if color is None:
        send_json(conn, {"type": "join_failed", "reason": "room_full"})
        return None, None

    print(f"[ROOM] {addr} joined room {room.room_id} as {color}")
    send_json(conn, {
        "type": "joined",
        "room_id": room.room_id,
        "color": color,
    })

    # Nếu phòng đã đủ 2 người, khởi tạo game và gửi state ban đầu
    if room.is_full():
        print(f"[ROOM] Room {room.room_id} is full, starting game")
        room.ensure_started()
        if room.board is not None:
            initial_state = {
                "type": "state",
                "room_id": room.room_id,
                "fen": room.board.export_fen(),
                "turn": room.current_turn_color(),
                "result": get_game_result(room.board),
                "last_move": None,
                "time_white": room.white_time_left,
                "time_black": room.black_time_left,
            }
        else:
            initial_state = {
                "type": "error",
                "message": "failed_to_start_game",
            }
        print(f"[DEBUG] sending initial_state to both: {initial_state}")

        notify_both(room, initial_state)

    return room, color


def handle_move(conn: socket.socket, addr, room: GameRoom, player_color: str, msg: dict):
    """
    Xử lý message move từ client:
    msg: {"type": "move", "uci": "e2e4"}
    """
    uci = msg.get("uci")
    if not isinstance(uci, str):
        send_json(conn, {"type": "error", "message": "invalid_move_format"})
        return

    # Bảo hiểm: đảm bảo game đã start
    room.ensure_started()

    try:
        state = room.make_move(player_color, uci)
    except ValueError as e:
        reason = str(e)
        print(f"[MOVE] Illegal/invalid move ffrom {addr} in room {room.room_id}: {reason}")
        send_json(conn, {"type": "move_rejected", "reason": reason})
        return

    # Move hợp lệ, broadcast state mới cho cả 2
    print(f"[MOVE] {addr} ({player_color}) played {uci} in room {room.room_id}")
    notify_both(room, state)


def handle_resign(conn: socket.socket, addr, room: GameRoom, player_color: str) -> None:
    """
    Người chơi đầu hàng:
    - Nếu white resign -> black_win
    - Nếu black resign -> white_win
    Broadcast luôn state mới cho cả 2.
    """
    # Nếu game chưa start (chưa đủ 2 người) thì báo lỗi nhẹ
    if not room.started or room.board is None:
        send_json(conn, {"type": "error", "message": "game_not_started"})
        return

    # Nếu game đã kết thúc rồi, chỉ gửi lại state hiện tại
    if room.result != "ongoing":
        fen = room.board.export_fen()
        state = {
            "type": "state",
            "room_id": room.room_id,
            "fen": fen,
            "turn": room.current_turn_color(),
            "result": room.result,
            "last_move": None,
            "time_white": room.white_time_left,
            "time_black": room.black_time_left,
        }
        notify_both(room, state)
        return

    # Đặt kết quả dựa trên người đầu hàng
    if player_color == "white":
        room.result = "black_win"
    else:
        room.result = "white_win"

    fen = room.board.export_fen()
    state = {
        "type": "state",
        "room_id": room.room_id,
        "fen": fen,
        "turn": room.current_turn_color(),
        "result": room.result,
        "last_move": None,
        "time_white": room.white_time_left,
        "time_black": room.black_time_left,
    }
    print(f"[GAME] Player {player_color} resigned in room {room.room_id}, result={room.result}")
    notify_both(room, state)


def handle_offer_draw(conn: socket.socket, addr, room: GameRoom, player_color: str) -> None:
    """
    Xử lý đề nghị hoà.
    Đơn giản hoá: cứ ai bấm Offer Draw là hai bên hoà luôn (result='draw').
    Nếu muốn phức tạp hơn (bên kia phải accept) thì cần thêm message 'draw_offer'/'draw_response'.
    """
    # Nếu game chưa start (chưa đủ 2 người) thì báo lỗi
    if not room.started or room.board is None:
        send_json(conn, {"type": "error", "message": "game_not_started"})
        return

    if room.result != "ongoing":
        # Game đã kết thúc rồi, gửi lại state hiện tại
        fen = room.board.export_fen()
        state = {
            "type": "state",
            "room_id": room.room_id,
            "fen": fen,
            "turn": room.current_turn_color(),
            "result": room.result,
            "last_move": None,
            "time_white": room.white_time_left,
            "time_black": room.black_time_left,
        }
        notify_both(room, state)
        return

    room.result = "draw"
    fen = room.board.export_fen()
    state = {
        "type": "state",
        "room_id": room.room_id,
        "fen": fen,
        "turn": room.current_turn_color(),
        "result": room.result,
        "last_move": None,
        "time_white": room.white_time_left,
        "time_black": room.black_time_left,
    }
    print(f"[GAME] Draw agreed (auto) in room {room.room_id}")
    notify_both(room, state)


def handle_list_rooms(conn: socket.socket) -> None:
    """
    Gửi về danh sách các phòng hiện tại, với số người chơi trong phòng.
    Không leak socket info, chỉ room_id + player_count + started.
    """
    room_list = []
    with rooms_lock:
        for room_id, room in rooms.items():
            room_list.append(
                {
                    "room_id": room_id,
                    "players": room.player_count(),
                    "started": room.started,
                }
            )

    send_json(conn, {"type": "rooms", "rooms": room_list})


def notify_both(room: GameRoom, msg: dict):
    with room.lock:
        conns = [c for c in (room.white_conn, room.black_conn) if c is not None]
    for c in conns:
        send_json(c, msg)


# ----- Server loop -----

def start_server(host: str = HOST, port: int = PORT):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    print(f"[INFO] Server listening on {host}:{port}")

    try:
        while True:
            conn, addr = server_sock.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()
