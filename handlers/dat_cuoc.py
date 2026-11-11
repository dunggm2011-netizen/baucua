from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TEN_CON_VAT
import database.users as users_db
import database.games as games_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "🎯 Đặt cược")
    def hien_danh_sach_ban(message):
        conn = get_conn()
        bans = conn.execute("SELECT * FROM bans WHERE trang_thai='dang_cho' OR trang_thai='het_gio'").fetchall()
        conn.close()
        
        if not bans:
            bot.reply_to(message, "❌ Hiện không có bàn nào đang mở.")
            return
            
        kb = InlineKeyboardMarkup()
        for b in bans:
            kb.add(InlineKeyboardButton(f"Bàn #{b['ban_id']} (Cái: {b['cai_id']})", callback_data=f"vaoban_{b['ban_id']}"))
            
        bot.reply_to(message, "Chọn bàn bạn muốn vào:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('vaoban_'))
    def vao_ban(call):
        ban_id = int(call.data.split('_')[1])
        ban = games_db.get_ban(ban_id)
        
        if not ban or ban['trang_thai'] not in ('dang_cho', 'het_gio'):
            bot.answer_callback_query(call.id, "Bàn này đã bị xoá hoặc không tồn tại!", show_alert=True)
            return
            
        kb = InlineKeyboardMarkup()
        row = []
        for con in TEN_CON_VAT:
            row.append(InlineKeyboardButton(TEN_CON_VAT[con], callback_data=f"choncon_{con}_{ban_id}"))
            if len(row) == 3:
                kb.row(*row); row = []
        if row: kb.row(*row)
        
        bot.send_message(call.message.chat.id, f"Bạn đang vào Bàn #{ban_id}.\nGõ lệnh `/cuoc <số tiền>` hoặc chọn con vật bên dưới:", reply_markup=kb, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('choncon_'))
    def chon_con(call):
        parts = call.data.split('_')
        con = parts[1]
        ban_id = int(parts[2])
        
        kb = InlineKeyboardMarkup()
        menh_gia = [100, 500, 1000, 5000, 10000]
        row = []
        for mg in menh_gia:
            row.append(InlineKeyboardButton(f"{mg} điểm", callback_data=f"cuoc_{con}_{ban_id}_{mg}"))
            if len(row) == 3:
                kb.row(*row); row = []
        if row: kb.row(*row)
        
        bot.edit_message_text(
            f"Bạn chọn cửa **{TEN_CON_VAT[con]}** ở Bàn #{ban_id}.\nChọn mệnh giá cược:", 
            chat_id=call.message.chat.id, message_id=call.message.message_id, 
            reply_markup=kb, parse_mode='Markdown'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('cuoc_'))
    def xu_ly_cuoc(call):
        parts = call.data.split('_')
        con = parts[1]
        ban_id = int(parts[2])
        so_diem = int(parts[3])
        u = call.from_user
        
        ban = games_db.get_ban(ban_id)
        if not ban or ban['trang_thai'] not in ('dang_cho', 'het_gio'):
            bot.answer_callback_query(call.id, "⏰ Bàn này đã bị xoá!", show_alert=True)
            return
        
        if ban['cai_id'] == u.id:
            bot.answer_callback_query(call.id, "❌ Bạn là Nhà Cái, không thể tự đặt cược!", show_alert=True)
            return
            
        if not users_db.tru_diem(u.id, so_diem):
            bot.answer_callback_query(call.id, f"❌ Bạn không đủ {so_diem} điểm!", show_alert=True)
            return

        games_db.luu_cuoc(ban_id, u.id, con, so_diem)
        users_db.cong_tien_cuoc(u.id, so_diem) # CỘNG DỒN TIỀN CƯỢC
        
        bot.answer_callback_query(call.id, f"✅ Đã cược {so_diem} điểm vào {TEN_CON_VAT[con]}")
        bot.send_message(call.message.chat.id, f"✅ User {u.full_name} đã cược {so_diem} điểm vào {TEN_CON_VAT[con]} (Bàn #{ban_id})")

    @bot.message_handler(commands=['cuoc'])
    def lenh_cuoc(message):
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Cú pháp: `/cuoc <số tiền>`\nVí dụ: `/cuoc 1000`", parse_mode='Markdown')
            return
        try: so_diem = int(parts[1])
        except:
            bot.reply_to(message, "Số tiền không hợp lệ."); return
            
        conn = get_conn()
        ban = conn.execute("SELECT * FROM bans WHERE chat_id=? AND (trang_thai='dang_cho' OR trang_thai='het_gio') ORDER BY ban_id DESC LIMIT 1", (message.chat.id,)).fetchone()
        conn.close()
        
        if not ban:
            bot.reply_to(message, "❌ Hiện không có bàn nào đang mở trong nhóm này."); return
            
        if ban['cai_id'] == message.from_user.id:
            bot.reply_to(message, "❌ Bạn là Nhà Cái của bàn này, không thể tự đặt cược!")
            return
            
        kb = InlineKeyboardMarkup()
        row = []
        for con in TEN_CON_VAT:
            row.append(InlineKeyboardButton(TEN_CON_VAT[con], callback_data=f"cuoc_{con}_{ban['ban_id']}_{so_diem}"))
            if len(row) == 3:
                kb.row(*row); row = []
        if row: kb.row(*row)
        
        bot.reply_to(message, f"Bạn muốn cược **{so_diem} điểm** vào con nào ở Bàn #{ban['ban_id']}?", reply_markup=kb, parse_mode='Markdown')
