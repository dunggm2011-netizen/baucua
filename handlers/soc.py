from telegram import Update
from telegram.ext import ContextTypes
import database.users as users_db
import database.games as games_db
from utils import media
from utils.tinh_toan import tinh_thang_thua
from config import TEN_CON_VAT

async def xu_ly_soc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ban_id = int(query.data.replace("soc_", ""))
    ban = games_db.get_ban(ban_id)

    if ban['cai_id'] != query.from_user.id:
        await query.answer("Chỉ người làm cái mới được sóc!", show_alert=True)
        return
    if ban['trang_thai'] not in ('dang_cho', 'het_gio'):
        await query.answer("Bàn này đã sóc rồi!", show_alert=True)
        return

    ket_qua = media.random_ket_qua()
    games_db.ket_thuc_ban(ban_id, ",".join(ket_qua))

    ten_ket_qua = " - ".join(TEN_CON_VAT[c] for c in ket_qua)
    await query.message.reply_text(f"🎲 KẾT QUẢ: {ten_ket_qua}")

    for con in ket_qua:
        path = media.get_anh(con)
        if path:
            with open(path, 'rb') as f:
                await query.message.reply_photo(photo=f, caption=TEN_CON_VAT[con])

    danh_sach_cuoc = games_db.get_cuoc_cua_ban(ban_id)
    ket_qua_lines = []
    for cuoc in danh_sach_cuoc:
        thang, so_diem_nhan = tinh_thang_thua(cuoc['cua'], cuoc['so_diem'], ket_qua)
        if thang:
            users_db.cong_diem(cuoc['user_id'], so_diem_nhan)
            ket_qua_lines.append(f"✅ User {cuoc['user_id']} thắng {so_diem_nhan} điểm")
        else:
            ket_qua_lines.append(f"❌ User {cuoc['user_id']} thua {cuoc['so_diem']} điểm")

    if ket_qua_lines: await query.message.reply_text("\n".join(ket_qua_lines))
    else: await query.message.reply_text("Không có ai đặt cược.")
