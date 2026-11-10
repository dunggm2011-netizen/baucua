from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database.users as users_db
import database.games as games_db
from config import TEN_CON_VAT, CUOC_MAC_DINH

async def menu_dat_cuoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ban = games_db.get_ban_dang_cho(update.effective_chat.id)
    if not ban:
        await update.message.reply_text("❌ Không có bàn nào đang mở.")
        return
    kb, row = [], []
    for con in TEN_CON_VAT:
        row.append(InlineKeyboardButton(TEN_CON_VAT[con], callback_data=f"cuoc_{con}"))
        if len(row) == 3:
            kb.append(row); row = []
    if row: kb.append(row)
    await update.message.reply_text(f"Chọn cửa đặt cược ({CUOC_MAC_DINH} điểm/lần):", reply_markup=InlineKeyboardMarkup(kb))

async def xu_ly_cuoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    con = query.data.replace("cuoc_", "")
    u = query.from_user

    ban = games_db.get_ban_dang_cho(query.message.chat_id)
    if not ban:
        await query.answer("⏰ Đã hết giờ đặt cược hoặc bàn đã đóng!", show_alert=True)
        return

    if not users_db.tru_diem(u.id, CUOC_MAC_DINH):
        await query.answer("❌ Không đủ điểm!", show_alert=True)
        return

    games_db.luu_cuoc(ban['ban_id'], u.id, con, CUOC_MAC_DINH)
    await query.answer(f"✅ Đã cược {CUOC_MAC_DINH} điểm vào {TEN_CON_VAT[con]}")
