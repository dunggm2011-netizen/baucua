from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import database.users as users_db
from config import ADMIN_ID

RUT_NHAP_DIEM = 1
RUT_NHAP_STK = 2

async def bat_dau_rut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diem = users_db.get_diem(update.effective_user.id)
    await update.message.reply_text(f"Điểm hiện tại: {diem}\nNhập số điểm muốn rút (quy đổi: 1000 điểm = 10.000đ):")
    return RUT_NHAP_DIEM

async def xu_ly_diem_rut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: so_diem = int(update.message.text)
    except: 
        await update.message.reply_text("Số điểm không hợp lệ. Nhập lại:")
        return RUT_NHAP_DIEM

    user_id = update.effective_user.id
    if not users_db.tru_diem(user_id, so_diem):
        await update.message.reply_text("Không đủ điểm. Nhập lại:")
        return RUT_NHAP_DIEM

    context.user_data['rut_diem'] = so_diem
    await update.message.reply_text("Nhập số tài khoản ngân hàng của bạn:")
    return RUT_NHAP_STK

async def xu_ly_stk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stk = update.message.text
    so_diem = context.user_data.get('rut_diem', 0)
    user_id = update.effective_user.id

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"💰 YÊU CẦU RÚT TIỀN\nUser: {user_id}\nĐiểm: {so_diem}\nQuy đổi: {so_diem * 10:,}đ\nSTK: {stk}\n\nDùng /duyetrut {user_id} {so_diem} để xác nhận.")
    await update.message.reply_text("Đã gửi yêu cầu. Admin sẽ xử lý trong ít phút.")
    return ConversationHandler.END

async def huy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy.")
    return ConversationHandler.END
