from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database.users as users_db
import database.games as games_db
from config import VON_LAM_CAI, THOI_GIAN_CUOC

async def tao_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    chat_id = update.effective_chat.id
    diem = users_db.get_diem(u.id)
    if diem < VON_LAM_CAI:
        await update.message.reply_text(f"❌ Cần {VON_LAM_CAI:,} điểm để làm cái.")
        return

    # Xóa ván cũ
    ban_cu = games_db.get_ban_gan_nhat(chat_id)
    if ban_cu and ban_cu['message_ids']:
        for mid in ban_cu['message_ids'].split(","):
            try: await context.bot.delete_message(chat_id=chat_id, message_id=int(mid))
            except: pass

    ban_id = games_db.tao_ban(u.id, chat_id)
    context.user_data['ban_id'] = ban_id

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎲 SÓC", callback_data=f"soc_{ban_id}")]])
    msg = await update.message.reply_text(f"✅ Bàn #{ban_id} đã mở. Bạn là CÁI.\n⏰ Đặt cược trong {THOI_GIAN_CUOC} giây!\nGõ /cuoc để đặt cược.", reply_markup=kb)
    games_db.them_message_id(ban_id, msg.message_id)

    context.job_queue.run_once(thong_bao_het_gio, THOI_GIAN_CUOC, data={"chat_id": chat_id, "ban_id": ban_id})

async def thong_bao_het_gio(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    games_db.khoa_ban(data["ban_id"])
    msg = await context.bot.send_message(chat_id=data["chat_id"], text="⏰ Hết giờ đặt cược! Người làm cái bấm SÓC.")
    games_db.them_message_id(data["ban_id"], msg.message_id)
