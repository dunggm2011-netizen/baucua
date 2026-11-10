import os
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from config import TEN_CON_VAT, IMG_DIR, THOI_GIAN_CUOC
import database.users as users_db
import database.games as games_db
from utils import media
from utils.tinh_toan import tinh_thang_thua

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('soc_'))
    def xu_ly_soc(call):
        ban_id = int(call.data.replace("soc_", ""))
        ban = games_db.get_ban(ban_id)

        # Chỉ Cái mới được Sóc
        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "❌ Chỉ người tạo bàn (Cái) mới được phép Sóc!", show_alert=True)
            return
            
        # Phải đợi hết 40s mới cho sóc
        if ban['trang_thai'] != 'het_gio':
            bot.answer_callback_query(call.id, "⏰ Chưa hết giờ đặt cược, chưa được sóc!", show_alert=True)
            return

        ket_qua = media.random_ket_qua()
        games_db.ket_thuc_ban(ban_id, ",".join(ket_qua))
        bot.answer_callback_query(call.id)
        
        bot.send_message(call.message.chat.id, f"🎲 KẾT QUẢ: {' - '.join(TEN_CON_VAT[c] for c in ket_qua)}")

        # Gửi 3 tấm ảnh chung 1 tin nhắn (Album)
        media_group = []
        for con in ket_qua:
            path = os.path.join(IMG_DIR, f'{con}.jpg')
            if os.path.exists(path):
                media_group.append(InputMediaPhoto(open(path, 'rb'), caption=TEN_CON_VAT[con]))
                
        if media_group:
            bot.send_media_group(call.message.chat.id, media_group)

        # Tính điểm
        danh_sach = games_db.get_cuoc_cua_ban(ban_id)
        text = "📊 KẾT QUẢ VÁN CHƠI:\n"
        tong_tra_player = 0
        
        if not danh_sach:
            text += "Không có ai đặt cược trong ván này.\n"
        else:
            for c in danh_sach:
                thang, so_diem_nhan = tinh_thang_thua(c['cua'], c['so_diem'], ket_qua)
                if thang:
                    users_db.cong_diem(c['user_id'], so_diem_nhan)
                    tong_tra_player += so_diem_nhan
                    text += f"✅ User {c['user_id']} thắng {so_diem_nhan} điểm ({TEN_CON_VAT[c['cua']]})\n"
                else:
                    text += f"❌ User {c['user_id']} thua {c['so_diem']} điểm ({TEN_CON_VAT[c['cua']]})\n"
            
            if tong_tra_player > 0:
                users_db.tru_diem(ban['cai_id'], tong_tra_player)
                text += f"\n💸 Nhà cái {ban['cai_id']} đã trả {tong_tra_player} điểm."
                
        # Nút lựa chọn sau khi Sóc: Tiếp tục hoặc Xoá
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("🔄 Ván Tiếp", callback_data=f"tiepvan_{ban_id}"),
            InlineKeyboardButton("🗑 Xoá bàn", callback_data=f"xoaban_{ban_id}")
        )
        
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    # Xử lý nút "Ván Tiếp" (Reset lại bàn, đếm ngược lại 40s)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('tiepvan_'))
    def van_tiep(call):
        from handlers.tao_ban import register_handlers as tb # Gọi lại hàm đếm ngược
        import threading
        
        ban_id = int(call.data.replace("tiepvan_", ""))
        ban = games_db.get_ban(ban_id)
        
        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "Chỉ người tạo bàn mới được bấm!", show_alert=True)
            return
            
        # Reset trạng thái bàn
        from database.db import get_conn
        conn = get_conn()
        conn.execute("UPDATE bans SET trang_thai='dang_cho', ket_qua=NULL WHERE ban_id=?", (ban_id,))
        # Xoá các lượt cược cũ của ván trước
        conn.execute("DELETE FROM cuoc WHERE ban_id=?", (ban_id,))
        conn.commit(); conn.close()

        bot.answer_callback_query(call.id, "Bắt đầu ván mới!")
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🗑 Xoá bàn", callback_data=f"xoaban_{ban_id}"))
        
        msg = bot.send_message(
            call.message.chat.id, 
            f"🔄 **VÁN MỚI BẮT ĐẦU!**\n⏰ Đặt cược trong {THOI_GIAN_CUOC} giây!\n👉 Gõ lệnh: `/cuoc <số tiền>`", 
            reply_markup=kb, parse_mode='Markdown'
        )
        games_db.them_message_id(ban_id, msg.message_id)
        
        # Đếm ngược lại 40s
        threading.Timer(THOI_GIAN_CUOC, khoa_ban_tiep, args=[bot, call.message.chat.id, ban_id]).start()

    def khoa_ban_tiep(bot, chat_id, ban_id):
        games_db.khoa_ban(ban_id)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("🎲 SÓC", callback_data=f"soc_{ban_id}"),
            InlineKeyboardButton("🗑 Xoá bàn", callback_data=f"xoaban_{ban_id}")
        )
        msg = bot.send_message(chat_id, "⏰ Hết giờ đặt cược! Người làm cái bấm SÓC.", reply_markup=kb)
        games_db.them_message_id(ban_id, msg.message_id)
