from telegram import Update
from telegram.ext import ContextTypes
import database.users as users_db
from config import ADMIN_ID

async def duyet_rut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        parts = update.message.text.split()
        user_id, so_diem = int(parts[1]), int(parts[2])
    except:
        await update.message.reply_text("Cú pháp: /duyetrut <user_id> <so_diem>")
        return
    await update.message.reply_text(f"✅ Đã duyệt rút {so_diem} điểm cho user {user_id}.")
    await context.bot.send_message(chat_id=user_id, text=f"✅ Yêu cầu rút {so_diem} điểm đã được duyệt. Vui lòng kiểm tra tài khoản.")

async def cong_diem_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        parts = update.message.text.split()
        user_id, so_diem = int(parts[1]), int(parts[2])
    except:
        await update.message.reply_text("Cú pháp: /congdiem <user_id> <so_diem>")
        return
    users_db.cong_diem(user_id, so_diem)
    await update.message.reply_text(f"Đã cộng {so_diem} điểm cho {user_id}.")
