import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import VON_LAM_CAI, THOI_GIAN_CUOC, TEN_CON_VAT
import database.users as users_db
import database.games as games_db
from database.db import get_conn
from utils import media
# Import hàm xử lý Sóc tự động từ file soc.py (sẽ viết ở dưới)
from handlers.soc import tu_dong_soc 

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "🎲 Tạo bàn")
    def tao_ban(message):
        u = message.from_user
        chat_id = message.chat.id
        
        ban_cu = games_db.get_ban_gan_nhat(chat_id)
        if ban_cu and ban_cu['trang_thai'] in ('dang_cho', 'het_gio'):
            bot.reply_to(message, "⚠️ Bạn đang có một bàn đang mở.")
            return

        diem = users_db.get_diem(u.id)
        if diem < VON_LAM_CAI:
            bot.reply_to(message, f"❌ Bạn cần tối thiểu {VON_LAM_CAI:,} điểm để làm Cái.")
            return

        ban_id = games_db.tao_ban(u.id, chat_id)
        
        # Gửi tin nhắn đếm ngược đầu tiên
        msg = bot.send_message(chat_id, f"⏳ Bàn #{ban_id} đang mở. Thời gian đặt cược: {THOI_GIAN_CUOC}s...")
        games_db.them_message_id(ban_id, msg.message_id)
        
        # Chạy luồng đếm ngược ngầm
        threading.Thread(target=dem_nguoc_realtime, args=[bot, chat_id, ban_id, msg.message_id]).start()

    def dem_nguoc_realtime(bot, chat_id, ban_id, msg_id):
        for i in range(THOI_GIAN_CUOC, 0, -1):
            time.sleep(1)
            try:
                # Cập nhật tin nhắn mỗi 5 giây hoặc 3 giây cuối để tránh bị Telegram chặn (Rate Limit)
                if i % 5 == 0 or i <= 3:
                    bot.edit_message_text(
                        chat_id=chat_id, 
                        message_id=msg_id, 
                        text=f"⏳ Bàn #{ban_id} đang mở.\n⏰ Còn lại: <b>{i} giây</b>\n👉 Gõ /cuoc <số tiền> để cược.",
                        parse_mode='HTML'
                    )
            except:
                pass # Bỏ qua nếu có lỗi mạng

        # Hết giờ -> Random kết quả ngầm
        ket_qua_ngam = media.random_ket_qua()
        conn = get_conn()
        conn.execute("UPDATE bans SET trang_thai='het_gio', ket_qua=? WHERE ban_id=?", (",".join(ket_qua_ngam), ban_id))
        conn.commit(); conn.close()
        
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=msg_id, 
            text=f"🔒 Bàn #{ban_id} đã khóa đặt cược.\n🎲 Kết quả đang được công bố...",
            parse_mode='HTML'
        )
        
        # TỰ ĐỘNG SÓC
        tu_dong_soc(bot, ban_id, chat_id)
