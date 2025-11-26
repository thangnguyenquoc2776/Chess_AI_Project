# game/config.py
"""
Cấu hình chung cho game cờ vua.
"""

# =========================
#  CỬA SỔ / MÀN HÌNH
# =========================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Chess_AI_Project"

# =========================
#  BÀN CỜ
# =========================
# Số ô mỗi cạnh (cờ vua 8x8)
BOARD_SIZE = 8

# Kích thước 1 ô (pixel)
TILE_SIZE = 80

# Tổng kích thước bàn (pixel)
BOARD_PIXEL_SIZE = TILE_SIZE * BOARD_SIZE

# Vị trí góc trái trên của bàn (canh giữa)
BOARD_LEFT = (SCREEN_WIDTH - BOARD_PIXEL_SIZE) // 2
BOARD_TOP = (SCREEN_HEIGHT - BOARD_PIXEL_SIZE) // 2

# =========================
#  MÀU SẮC
# =========================
# Tên gốc (đang được board_renderer, mouse, ... import)
COLOR_LIGHT_SQUARE = (240, 217, 181)   # ô sáng
COLOR_DARK_SQUARE  = (181, 136,  99)   # ô tối

# Ô đang được chọn (selected square)
COLOR_SELECTED     = (246, 214,  91)   # highlight quân đang chọn

# Ô nước đi hợp lệ (gợi ý move)
COLOR_MOVE_HINT    = (246, 214, 140)   # có thể hơi khác selected 1 chút

# Ô của nước đi cuối cùng (from/to)
COLOR_LAST_MOVE    = (210, 180,  80)

# Nền ngoài bàn cờ
COLOR_BG           = ( 15,  15,  15)

# Màu chữ HUD / panel
COLOR_TEXT         = (255, 255, 255)

# Màu chữ cho quân trắng / quân đen (placeholder cho asset sau này)
COLOR_WHITE_PIECE  = (255, 255, 255)   # trắng tinh
COLOR_BLACK_PIECE  = ( 25,  25,  25)   # gần đen, vẫn thấy trên ô sáng

# Alias tên “mới” nếu sau này ông muốn dùng cho đẹp, nhưng
# vẫn trỏ tới mấy màu ở trên để không bị lệch.
COLOR_LIGHT     = COLOR_LIGHT_SQUARE
COLOR_DARK      = COLOR_DARK_SQUARE
COLOR_HIGHLIGHT = COLOR_SELECTED

# =========================
#  FONT
# =========================
# Tỉ lệ font dựa trên chiều cao 720p
FONT_SCALE = SCREEN_HEIGHT / 720.0

# =========================
#  ĐỒNG HỒ CỜ VUA
# =========================
# Tổng thời gian cho mỗi bên (giây)
# Ví dụ: 5 phút = 300, 10 phút = 600, 15 phút = 900
CHESS_TIME_LIMIT_SEC = 300

# Online server config (sửa IP này sang IP / domain server của bạn khi cần)
ONLINE_SERVER_HOST = "127.0.0.1"
ONLINE_SERVER_PORT = 5000
