from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import database.games as games_db
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP

NAP_NHAP_SO_TIEN = 1

async def bat_dau_nap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nhập số tiền muốn nạp (10.000 - 200.000 VNĐ):\nVí dụ: 50000\nGõ /huy để hủy.")
    return NAP_NHAP_SO_TIEN

async def xu_ly_so_tien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: so_tien = int(update.message.text.replace(".", "").replace(",", ""))
    except: 
        await update.message.reply_text("Số tiền không hợp lệ. Nhập lại:")
        return NAP_NHAP_SO_TIEN

    if so_tien < 10000 or so_tien > 200000:
        await update.message.reply_text("Số tiền phải từ 10.000 đến 200.000. Nhập lại:")
        return NAP_NHAP_SO_TIEN

    user_id = update.effective_user.id
    ma_don = f"NAP{user_id}{so_tien}"
    qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
    
    so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
    games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

    await update.message.reply_photo(photo=qr_url, caption=f"Quét QR để nạp {so_tien:,}đ\nNội dung CK: {ma_don}\nĐiểm nhận được: {so_diem_nhan} (đã trừ 2% phí)\n\nSau khi chuyển khoản, điểm sẽ tự động cộng.")
    return ConversationHandler.END

async def huy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy.")
    return ConversationHandler.END
