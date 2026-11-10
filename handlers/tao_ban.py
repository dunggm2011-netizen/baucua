import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import VON_LAM_CAI, THOI_GIAN_CUOC
import database.users as users_db
import database.games as games_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "🎲 Tạo bàn")
    def tao_ban(message):
        u = message.from_user
        chat_id = message.chat.id
        
        # Kiểm tra xem đã có bàn nào đang mở chưa
        ban_cu = games_db.get_ban_gan_nhat(chat_id)
        if ban_cu and ban_cu['trang_thai'] in ('dang_cho', 'het_gio'):
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("↩️ Vô lại bàn cũ", callback_data=f"vaoban_{ban_cu['ban_id']}"))
            bot.reply_to(message, "⚠️ Bạn đang có một bàn đang mở.", reply_markup=kb)
            return

        diem = users_db.get_diem(u.id)
        if diem < VON_LAM_CAI:
            bot.reply_to(message, f"❌ Bạn cần tối thiểu {VON_LAM_CAI:,} điểm để làm Cái.")
            return

        ban_id = games_db.tao_ban(u.id, chat_id)
        
        kb = InlineKeyboardMarkup()
        # Trong lúc chờ 40s, Cái có thể xoá bàn nếu muốn
        kb.add(InlineKeyboardButton("🗑 Xoá bàn", callback_data=f"xoaban_{ban_id}"))
        
        msg = bot.send_message(
            chat_id, 
            f"✅ Bàn #{ban_id} đã mở. Bạn là CÁI.\n"
            f"⏰ Đặt cược trong {THOI_GIAN_CUOC} giây!\n"
            f"👉 Người chơi gõ lệnh: `/cuoc <số tiền>`\n", 
            reply_markup=kb,
            parse_mode='Markdown'
        )
        games_db.them_message_id(ban_id, msg.message_id)
        
        # Chạy luồng đếm ngược
        threading.Timer(THOI_GIAN_CUOC, khoa_ban, args=[bot, chat_id, ban_id]).start()

    def khoa_ban(bot, chat_id, ban_id):
        # Hết giờ thì đổi trạng thái sang 'het_gio'
        games_db.khoa_ban(ban_id)
        
        # Đổi nút thành nút SÓC và Xoá bàn
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("🎲 SÓC", callback_data=f"soc_{ban_id}"),
            InlineKeyboardButton("🗑 Xoá bàn", callback_data=f"xoaban_{ban_id}")
        )
        
        msg = bot.send_message(chat_id, "⏰ Hết giờ đặt cược! Người làm cái bấm SÓC.", reply_markup=kb)
        games_db.them_message_id(ban_id, msg.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('xoaban_'))
    def xoa_ban(call):
        ban_id = int(call.data.replace("xoaban_", ""))
        ban = games_db.get_ban(ban_id)
        
        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "Chỉ người tạo bàn mới được xoá!", show_alert=True)
            return
            
        conn = get_conn()
        conn.execute("UPDATE bans SET trang_thai='da_xoa' WHERE ban_id=?", (ban_id,))
        conn.commit(); conn.close()
        
        bot.answer_callback_query(call.id, "Đã xoá bàn!")
        bot.send_message(call.message.chat.id, f"🗑 Bàn #{ban_id} đã bị người tạo xoá.")
