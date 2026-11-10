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

        # CHỈ NGƯỜI TẠO BÀN (CÁI) MỚI ĐƯỢC SÓC
        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "❌ Chỉ người tạo bàn (Cái) mới được phép Sóc!", show_alert=True)
            return
            
        if ban['trang_thai'] not in ('dang_cho', 'het_gio'):
            bot.answer_callback_query(call.id, "Bàn này đã sóc rồi!", show_alert=True)
            return

        ket_qua = media.random_ket_qua()
        games_db.ket_thuc_ban(ban_id, ",".join(ket_qua))
        bot.answer_callback_query(call.id)
        
        # Gửi tin nhắn chữ
        bot.send_message(call.message.chat.id, f"🎲 KẾT QUẢ: {' - '.join(TEN_CON_VAT[c] for c in ket_qua)}")

        # Gửi 3 hình ảnh kết quả
        for con in ket_qua:
            path = os.path.join(IMG_DIR, f'{con}.jpg')
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    bot.send_photo(call.message.chat.id, f, caption=TEN_CON_VAT[con])
            else:
                bot.send_message(call.message.chat.id, f"⚠️ Lỗi: Không tìm thấy ảnh {con}.jpg")

        # Tính điểm
        danh_sach = games_db.get_cuoc_cua_ban(ban_id)
        if not danh_sach:
            bot.send_message(call.message.chat.id, "Không có ai đặt cược trong ván này.")
            return

        tong_tra_player = 0
        text = "📊 KẾT QUẢ VÁN CHƠI:\n"
        
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
            
        bot.send_message(call.message.chat.id, text)
