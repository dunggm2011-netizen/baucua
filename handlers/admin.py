from config import ADMIN_ID
import database.users as users_db
from database.db import get_conn
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "⚙️ Admin")
    def admin_menu(message):
        if message.from_user.id != ADMIN_ID: return
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        # Thêm nút Duyệt Rút
        kb.row(KeyboardButton("📋 Duyệt Rút"), KeyboardButton("📊 Top Người Chơi"))
        kb.row(KeyboardButton("⬅️ Quay lại Menu"))
        bot.reply_to(message, "⚙️ BẢNG ĐIỀU KHIỂN ADMIN\nChọn thao tác:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "📋 Duyệt Rút")
    def xem_yeu_cau_rut(message):
        if message.from_user.id != ADMIN_ID: return
        conn = get_conn()
        reqs = conn.execute("SELECT * FROM yeu_cau_rut WHERE trang_thai='cho_duyet'").fetchall()
        conn.close()
        
        if not reqs:
            bot.reply_to(message, "✅ Không có yêu cầu rút nào đang chờ duyệt.")
            return
            
        for r in reqs:
            text = (
                f"🆔 Mã YC: `{r['id']}`\n"
                f"👤 User ID: `{r['user_id']}`\n"
                f"💸 Rút: {r['so_diem']} điểm ({r['so_diem']*10:,}đ)\n"
                f"🏦 STK: `{r['stk']}`\n"
                f"👨‍💼 Chủ thẻ: {r['ten_chu_the']}\n\n"
                f"👉 Duyệt: `/duyetrut {r['id']}`\n"
                f"👉 Từ chối: `/tuchoi {r['id']}`"
            )
            bot.send_message(message.chat.id, text, parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text == "📊 Top Người Chơi")
    def xem_top_user(message):
        if message.from_user.id != ADMIN_ID: return
        conn = get_conn()
        users = conn.execute('SELECT user_id, ho_ten, diem FROM users ORDER BY diem DESC LIMIT 10').fetchall()
        conn.close()
        if not users:
            bot.reply_to(message, "Chưa có người chơi nào."); return
        text = "📊 TOP 10 NGƯỜI CHƠI:\n\n"
        for i, u in enumerate(users, 1):
            text += f"{i}. 👤 {u['ho_ten']} (`{u['user_id']}`) - 💰 {u['diem']:,} điểm\n"
        bot.reply_to(message, text, parse_mode='Markdown')

    @bot.message_handler(commands=['congdiem'])
    def cong_diem_admin(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split()
            user_id, so_diem = int(parts[1]), int(parts[2])
        except:
            bot.reply_to(message, "Cú pháp: /congdiem <user_id> <so_diem>"); return
        users_db.cong_diem(user_id, so_diem)
        bot.reply_to(message, f"✅ Đã cộng {so_diem} điểm cho user {user_id}.")
