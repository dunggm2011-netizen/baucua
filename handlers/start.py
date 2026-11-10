from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database.users as users_db
from config import ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    users_db.create_user(u.id, u.username, u.full_name)
    diem = users_db.get_diem(u.id)
    kb = [["🎲 Tạo bàn", "🎯 Đặt cược"], ["💰 Nạp tiền", "💸 Rút tiền"], ["📖 Luật chơi"]]
    if u.id == ADMIN_ID: kb.append(["⚙️ Admin"])
    await update.message.reply_text(f"Chào {u.full_name}!\n💰 Điểm: {diem}\n\nChọn chức năng:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def luat_choi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 LUẬT CHƠI:\n- Đặt 1 trong 6 cửa: Bầu, Cua, Tôm, Cá, Gà, Nai.\n- Kết quả ra con nào, nếu cửa bạn đặt xuất hiện n lần → ăn n lần cược.\n- Làm cái cần 100.000 điểm (1 triệu VNĐ).\n- Nạp tối thiểu 10k, tối đa 200k. Phí nạp 2%.")
