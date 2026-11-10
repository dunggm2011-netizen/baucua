import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import VON_LAM_CAI, THOI_GIAN_CUOC
import database.users as users_db
import database.games as games_db

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "🎲 Tạo bàn")
    def tao_ban(message):
        u = message.from_user
        chat_id = message.chat.id
        diem = users_db.get_diem(u.id)
        
        if diem < VON_LAM_CAI:
            bot.reply_to(message, f"❌ Bạn cần tối thiểu {VON_LAM_CAI:,} điểm để làm Cái.")
            return

        # Xóa ván cũ
        ban_cu = games_db.get_ban_gan_nhat(chat_id)
        if ban_cu and ban_cu['message_ids']:
            for mid in ban_cu['message_ids'].split(","):
                try: bot.delete_message(chat_id, int(mid))
                except: pass

        ban_id = games_db.tao_ban(u.id, chat_id)
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎲 SÓC", callback_data=f"soc_{ban_id}"))
        
        msg = bot.send_message(
            chat_id, 
            f"✅ Bàn #{ban_id} đã mở. Bạn là CÁI.\n"
            f"⏰ Đặt cược trong {THOI_GIAN_CUOC} giây!\n"
            f"👉 Người chơi gõ lệnh: `/cuoc <số tiền>`\n"
            f"Hoặc bấm nút bên dưới để chọn.", 
            reply_markup=kb,
            parse_mode='Markdown'
        )
        
        games_db.them_message_id(ban_id, msg.message_id)
        
        # Đếm ngược 60s
        threading.Timer(THOI_GIAN_CUOC, khoa_ban, args=[bot, chat_id, ban_id]).start()

    def khoa_ban(bot, chat_id, ban_id):
        games_db.khoa_ban(ban_id)
        msg = bot.send_message(chat_id, "⏰ Hết giờ đặt cược! Người làm cái bấm SÓC.")
        games_db.them_message_id(ban_id, msg.message_id)
