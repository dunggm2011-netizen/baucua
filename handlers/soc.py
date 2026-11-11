import os
from telebot.types import InputMediaPhoto
from config import TEN_CON_VAT, IMG_DIR, GROUP_ID
import database.users as users_db
import database.games as games_db
from database.db import get_conn
from utils.tinh_toan import tinh_thang_thua

def tu_dong_soc(bot, ban_id, chat_id):
    ban = games_db.get_ban(ban_id)
    ket_qua = ban['ket_qua'].split(',')
    
    # Chuyển trạng thái
    conn = get_conn()
    conn.execute("UPDATE bans SET trang_thai='ket_thuc' WHERE ban_id=?", (ban_id,))
    conn.commit(); conn.close()
    
    # 1. Gửi thông báo và ảnh vào nhóm chơi
    ket_qua_chu = " - ".join([TEN_CON_VAT[c] for c in ket_qua])
    bot.send_message(chat_id, f"🎲 KẾT QUẢ: {ket_qua_chu}")

    media_group = []
    for con in ket_qua:
        path = os.path.join(IMG_DIR, f'{con}.jpg')
        if os.path.exists(path):
            media_group.append(InputMediaPhoto(open(path, 'rb'), caption=TEN_CON_VAT[con]))
    if media_group:
        bot.send_media_group(chat_id, media_group)

    # 2. Tính điểm
    danh_sach = games_db.get_cuoc_cua_ban(ban_id)
    text = "📊 <b>KẾT QUẢ VÁN CHƠI:</b>\n"
    tong_tra_player = 0
    
    if danh_sach:
        for c in danh_sach:
            thang, so_diem_nhan = tinh_thang_thua(c['cua'], c['so_diem'], ket_qua)
            u_info = users_db.get_user(c['user_id'])
            ten = u_info['ho_ten'] if u_info else f"User {c['user_id']}"
            
            if thang:
                users_db.cong_diem(c['user_id'], so_diem_nhan)
                tong_tra_player += so_diem_nhan
                text += f"✅ {ten} thắng {so_diem_nhan} điểm\n"
            else:
                text += f"❌ {ten} thua {c['so_diem']} điểm\n"
        
        if tong_tra_player > 0:
            users_db.tru_diem(ban['cai_id'], tong_tra_player)
            text += f"\n💸 Nhà cái đã trả {tong_tra_player:,} điểm."
    else:
        text += "Không có ai đặt cược.\n"
        
    bot.send_message(chat_id, text, parse_mode='HTML')

    # 3. Báo cáo về nhóm riêng của Admin (Nếu có cài đặt GROUP_ID)
    if GROUP_ID and GROUP_ID != 0:
        bao_cao = (
            f"🏁 <b>BÁO CÁO KẾT QUẢ VÁN MỚI</b> (Bàn #{ban_id})\n"
            f"🎲 Kết quả: <b>{ket_qua_chu}</b>\n"
            f"👑 Nhà cái: <code>{ban['cai_id']}</code>\n"
            f"👥 Số người cược: {len(danh_sach) if danh_sach else 0}\n"
            f"💸 Tổng trả: <b>{tong_tra_player:,} điểm</b>"
        )
        try:
            bot.send_message(GROUP_ID, bao_cao, parse_mode='HTML')
        except:
            pass

# Hàm này giữ lại để tương thích nếu lỡ Admin muốn bấm thủ công
def register_handlers(bot):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    @bot.callback_query_handler(func=lambda call: call.data.startswith('soc_'))
    def soc_manual(call):
        ban_id = int(call.data.replace("soc_", ""))
        ban = games_db.get_ban(ban_id)
        if ban['cai_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "Chỉ Cái mới được bấm!", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Đang xử lý...")
        tu_dong_soc(bot, ban_id, call.message.chat.id)
