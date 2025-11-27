import socket
import threading
import json
from typing import Optional, List, Dict, Any


class NetworkClient:
    """
    Client TCP đơn giản:
    - connect(host, port)
    - send_message(dict)
    - poll_messages() -> list[dict]
    """

    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._recv_buffer = ""
        self._incoming_lock = threading.Lock()
        self._incoming: List[Dict[str, Any]] = []
        self.connected: bool = False

    # --------- Kết nối / ngắt kết nối ----------

    def connect(self, host: str, port: int, timeout: float = 5.0) -> None:
        if self.connected:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.settimeout(None)  # để thread recv block bình thường

        self._sock = s
        self.connected = True

        self._recv_thread = threading.Thread(
            target=self._recv_loop, daemon=True
        )
        self._recv_thread.start()

    def close(self) -> None:
        self.connected = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    # --------- Gửi / nhận message ----------

    def send_message(self, msg: Dict[str, Any]) -> None:
        """
        Gửi 1 dict JSON (thêm '\n' ở cuối).
        """
        if not self.connected or self._sock is None:
            raise RuntimeError("Not connected")

        data = json.dumps(msg) + "\n"
        try:
            self._sock.sendall(data.encode("utf-8"))
        except OSError:
            self.close()
            raise

    def poll_messages(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả message đã nhận được kể từ lần gọi trước.
        Dùng trong game loop (mỗi frame gọi 1 lần).
        """
        with self._incoming_lock:
            msgs = self._incoming
            self._incoming = []
        return msgs

    # --------- Internal recv loop ----------

    def _recv_loop(self) -> None:
        assert self._sock is not None
        s = self._sock

        try:
            while self.connected:
                data = s.recv(4096)
                if not data:
                    print("[NET] socket closed by server")
                    break

                chunk = data.decode("utf-8")
                # print("[NET] raw recv:", repr(chunk))      # DEBUG
                self._recv_buffer += chunk

                while "\n" in self._recv_buffer:
                    line, self._recv_buffer = self._recv_buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    print("[NET] line:", repr(line))       # DEBUG
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError as e:
                        print("[NET] json error:", e, "line=", repr(line))
                        continue

                    # print("[NET] msg:", msg)              # DEBUG
                    with self._incoming_lock:
                        self._incoming.append(msg)

        except OSError:
            pass
        finally:
            self.connected = False
            try:
                s.close()
            except OSError:
                pass
            self._sock = None

    def peek_messages(self) -> List[Dict[str, Any]]:
        """
        Xem các message đã nhận được nhưng KHÔNG xoá khỏi hàng đợi.
        Dùng trong menu (chờ 'joined') để không làm mất 'state'.
        """
        with self._incoming_lock:
            return list(self._incoming)