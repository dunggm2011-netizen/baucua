import os

# Bắt buộc phải điền
BOT_TOKEN = os.getenv("BOT_TOKEN", "8077955829:AAHHkj9UfheUOx19dfQU-KCaXvSkJz7m92A")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7564889663")) # ID Telegram của bạn
ADMIN_KEY = "bita" # Key bảo mật cho web admin

# Cấu hình Ngân hàng (SePay)
SEPAY_BANK_BIN = "970436"  # Mã BIN ngân hàng (VD: 970436 là Vietcombank)
SEPAY_BANK_NUMBER = "0123456789" # Số tài khoản
SEPAY_ACCOUNT_NAME = "NGUYEN VAN A" # Tên chủ tài khoản

# Cấu hình Game
VON_LAM_CAI = 100000  # 100.000 điểm = 1.000.000 VNĐ
THOI_GIAN_CUOC = 40
CUOC_MAC_DINH = 100
PHI_NAP = 0.02

CON_VAT = ["bau", "cua", "tom", "ca", "ga", "nai"]
TEN_CON_VAT = {
    "bau": "Bầu", "cua": "Cua", "tom": "Tôm",
    "ca": "Cá", "ga": "Gà", "nai": "Nai"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Lưu ý: Trên Render Free, data sẽ bị xóa khi restart. Nên dùng Postgres nếu chạy thật.
DB_PATH = os.path.join(BASE_DIR, "data", "game_data.db")
IMG_DIR = os.path.join(BASE_DIR, "data", "images")
