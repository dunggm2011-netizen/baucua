import os
from config import TEN_CON_VAT, IMG_DIR
import database.users as users_db
import database.games as games_db
from utils import media
from utils.tinh_toan import tinh_thang_thua

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('soc_'))
    def xu_ly_soc(call):
        ban_id = int(call.data.replace("soc_", ""))
        ban = games_db.get_ban(ban_id)

        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "Chỉ người làm cái mới được sóc!", show_alert=True); return
        if ban['trang_thai'] not in ('dang_cho', 'het_gio'):
            bot.answer_callback_query(call.id, "Bàn này đã sóc rồi!", show_alert=True); return

        ket_qua = media.random_ket_qua()
        games_db.ket_thuc_ban(ban_id, ",".join(ket_qua))
        bot.answer_callback_query(call.id)

        bot.send_message(call.message.chat.id, f"🎲 KẾT QUẢ: {' - '.join(TEN_CON_VAT[c] for c in ket_qua)}")

        for con in ket_qua:
            path = media.get_anh(con)
            if path:
                with open(path, 'rb') as f:
                    bot.send_photo(call.message.chat.id, f, caption=TEN_CON_VAT[con])

        danh_sach = games_db.get_cuoc_cua_ban(ban_id)
        for c in danh_sach:
            thang, so_diem_nhan = tinh_thang_thua(c['cua'], c['so_diem'], ket_qua)
            if thang:
                users_db.cong_diem(c['user_id'], so_diem_nhan)
                bot.send_message(call.message.chat.id, f"✅ User {c['user_id']} thắng {so_diem_nhan} điểm")
            else:
                bot.send_message(call.message.chat.id, f"❌ User {c['user_id']} thua {c['so_diem']} điểm")
