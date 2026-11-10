from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TEN_CON_VAT, CUOC_MAC_DINH
import database.users as users_db
import database.games as games_db

def register_handlers(bot):
    @bot.message_handler(commands=['cuoc'])
    def menu_dat_cuoc(message):
        ban = games_db.get_ban_dang_cho(message.chat.id)
        if not ban:
            bot.reply_to(message, "❌ Không có bàn nào đang mở.")
            return
        kb = InlineKeyboardMarkup()
        row = []
        for con in TEN_CON_VAT:
            row.append(InlineKeyboardButton(TEN_CON_VAT[con], callback_data=f"cuoc_{con}"))
            if len(row) == 3:
                kb.row(*row); row = []
        if row: kb.row(*row)
        bot.reply_to(message, f"Chọn cửa đặt cược ({CUOC_MAC_DINH} điểm/lần):", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('cuoc_'))
    def xu_ly_cuoc(call):
        con = call.data.replace("cuoc_", "")
        u = call.from_user
        ban = games_db.get_ban_dang_cho(call.message.chat.id)
        
        if not ban:
            bot.answer_callback_query(call.id, "⏰ Đã hết giờ đặt cược!", show_alert=True)
            return
        if not users_db.tru_diem(u.id, CUOC_MAC_DINH):
            bot.answer_callback_query(call.id, "❌ Không đủ điểm!", show_alert=True)
            return

        games_db.luu_cuoc(ban['ban_id'], u.id, con, CUOC_MAC_DINH)
        bot.answer_callback_query(call.id, f"✅ Đã cược {CUOC_MAC_DINH} điểm vào {TEN_CON_VAT[con]}")
