
# filepath: c:\Users\Win 10\Desktop\Update Machine learning\Chess_AI_Project\game\scenes\online_menu.py
# game/scenes/online_menu.py
import pygame
from typing import List, Optional

from .base import SceneBase
from game.ui.widgets import Button
from game.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BG,
    COLOR_TEXT,
    ONLINE_SERVER_HOST,
    ONLINE_SERVER_PORT,
)
from game.network_client import NetworkClient
from .game_online import GameOnlineScene


class OnlineMenuScene(SceneBase):
    """
    Menu Play Online.
    - Host Game       : tạo phòng mới trên server mặc định trong config
    - Refresh Rooms   : lấy danh sách phòng hiện tại
    - Danh sách room  : click vào để join phòng
    - Back
    """

    def __init__(self, app):
        super().__init__(app)

        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 36)
        self.font_info = pygame.font.Font(None, 24)

        self.buttons_static: List[Button] = []
        self.buttons_rooms: List[Button] = []  # mỗi room là 1 button

        btn_width = 220
        btn_height = 45
        center_x = SCREEN_WIDTH // 2
        start_y = 160
        gap = 55

        # Host
        rect_host = pygame.Rect(0, 0, btn_width, btn_height)
        rect_host.center = (center_x, start_y)
        self.buttons_static.append(
            Button(
                rect_host,
                "Host Game",
                self.font_button,
                callback=self._on_host,
            )
        )

        # Refresh Rooms
        rect_refresh = pygame.Rect(0, 0, btn_width, btn_height)
        rect_refresh.center = (center_x, start_y + gap)
        self.buttons_static.append(
            Button(
                rect_refresh,
                "Refresh Rooms",
                self.font_button,
                callback=self._on_refresh_rooms,
            )
        )

        # Back
        rect_back = pygame.Rect(0, 0, btn_width, btn_height)
        rect_back.center = (center_x, start_y + 2 * gap)
        self.buttons_static.append(
            Button(
                rect_back,
                "Back",
                self.font_button,
                callback=self._on_back,
            )
        )

        self.info_text = f"Server: {ONLINE_SERVER_HOST}:{ONLINE_SERVER_PORT}"
        self.rooms: List[dict] = []  # từ server: [{"room_id":..., "players":..., "started":...}, ...]

    # ---------- Internal helpers ----------

    def _connect_once(self) -> Optional[NetworkClient]:
        """
        Tạo connection dùng tạm trong menu (host/list/join).
        Mỗi lần gọi tạo mới, xong việc thì hoặc đóng hoặc chuyển qua GameOnlineScene.
        """
        client = NetworkClient()
        try:
            client.connect(ONLINE_SERVER_HOST, ONLINE_SERVER_PORT)
        except Exception as e:
            self.info_text = f"Connect failed: {e}"
            return None
        return client

    def _wait_for_message(
        self,
        client: NetworkClient,
        target_types: list[str],
        timeout: float = 3.0,
    ) -> Optional[dict]:
        """
        Chờ tới khi nhận được 1 message có type trong target_types, hoặc timeout.
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            msgs = client.poll_messages()
            for m in msgs:
                if m.get("type") in target_types:
                    return m
            time.sleep(0.05)
        return None

    # ---------- Callbacks ----------

    def _on_host(self):
        """
        Tạo phòng mới trên server, vào thẳng game online.
        """
        client = self._connect_once()
        if client is None:
            return

        client.send_message({"type": "join", "game_id": None})

        msg = self._wait_for_message(client, ["joined"])
        if msg is None:
            self.info_text = "Host failed (no response)"
            client.close()
            return

        room_id = msg.get("room_id")
        color = msg.get("color")
        if not isinstance(room_id, str) or color not in ("white", "black"):
            self.info_text = "Host failed (invalid response)"
            client.close()
            return

        self.info_text = f"Hosted room {room_id} as {color}"

        # Chuyển sang GameOnlineScene, giữ client để chơi
        self.app.change_scene(
            GameOnlineScene,
            network_client=client,
            room_id=room_id,
            player_color=color,
        )

    def _on_refresh_rooms(self):
        """
        Lấy danh sách phòng từ server, hiển thị thành list button.
        """
        client = self._connect_once()
        if client is None:
            return

        client.send_message({"type": "list_rooms"})

        msg = self._wait_for_message(client, ["rooms"])
        client.close()

        if msg is None:
            self.info_text = "Failed to fetch rooms"
            return

        rooms = msg.get("rooms")
        if not isinstance(rooms, list):
            self.info_text = "Invalid rooms response"
            return

        # Lưu rooms, filter phòng đã full (players >= 2)
        self.rooms = [
            r for r in rooms
            if isinstance(r, dict) and isinstance(r.get("room_id"), str)
        ]

        if not self.rooms:
            self.info_text = "No rooms available"
        else:
            self.info_text = f"{len(self.rooms)} room(s) found"

        self._rebuild_room_buttons()

    def _rebuild_room_buttons(self):
        """
        Tạo lại các Button tương ứng với self.rooms.
        """
        self.buttons_rooms.clear()

        if not self.rooms:
            return

        # Bắt đầu vẽ list từ y cố định
        start_y = 340
        gap_y = 45
        x = SCREEN_WIDTH // 2

        for idx, r in enumerate(self.rooms):
            room_id = r.get("room_id")
            players = r.get("players", 0)
            started = r.get("started", False)

            # Text hiển thị: "room_id | 1/2 | waiting/playing"
            status = "playing" if started else "waiting"
            label = f"{room_id} | {players}/2 | {status}"

            rect = pygame.Rect(0, 0, 420, 36)
            rect.center = (x, start_y + idx * gap_y)

            # callback join room này
            def make_callback(rid=room_id):
                return lambda: self._on_join_room(rid)

            btn = Button(rect, label, self.font_info, callback=make_callback())
            self.buttons_rooms.append(btn)

    def _on_join_room(self, room_id: str):
        """
        Join vào room được click từ list.
        """
        client = self._connect_once()
        if client is None:
            return

        client.send_message({"type": "join", "game_id": room_id})

        msg = self._wait_for_message(client, ["joined", "join_failed"])
        if msg is None:
            self.info_text = "Join failed (no response)"
            client.close()
            return

        if msg.get("type") == "join_failed":
            self.info_text = f"Join failed: {msg.get('reason', 'unknown')}"
            client.close()
            return

        color = msg.get("color")
        if color not in ("white", "black"):
            self.info_text = "Join failed (invalid response)"
            client.close()
            return

        self.info_text = f"Joined room {room_id} as {color}"

        self.app.change_scene(
            GameOnlineScene,
            network_client=client,
            room_id=room_id,
            player_color=color,
        )

    def _on_back(self):
        from .menu_play import PlayMenuScene
        self.app.change_scene(PlayMenuScene)

    # ---------- SceneBase override ----------

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons_static:
                btn.handle_event(event)
            for btn in self.buttons_rooms:
                btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Title
        title_surf = self.font_title.render("Play Online", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surf, title_rect)

        # Info
        if self.info_text:
            info_surf = self.font_info.render(self.info_text, True, COLOR_TEXT)
            info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
            surface.blit(info_surf, info_rect)

        # Buttons (Host / Refresh / Back)
        for btn in self.buttons_static:
            btn.draw(surface)

        # List rooms
        if self.rooms:
            list_title = self.font_info.render("Available Rooms:", True, COLOR_TEXT)
            list_rect = list_title.get_rect(center=(SCREEN_WIDTH // 2, 300))
            surface.blit(list_title, list_rect)

            for btn in self.buttons_rooms:
                btn.draw(surface)
