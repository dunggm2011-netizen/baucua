from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
from database import games as games_db

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
    def nap_tien(message):
        msg = bot.reply_to(message, "Nhập số tiền muốn nạp (10.000 - 200.000 VNĐ):")
        bot.register_next_step_handler(msg, xu_ly_nap)

    def xu_ly_nap(message):
        if message.text.startswith('/'): return
        try:
            so_tien = int(message.text.replace(".", "").replace(",", ""))
            if so_tien < 10000 or so_tien > 200000: raise ValueError
        except:
            bot.reply_to(message, "❌ Số tiền không hợp lệ."); return
            
        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, so_tien, so_diem_nhan, ma_don)

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📲 Lấy mã QR", url=qr_url))
        bot.reply_to(message, f"✅ Tạo đơn nạp {so_tien:,}đ\n📝 Nội dung: {ma_don}\n💰 Nhận: {so_diem_nhan} điểm", reply_markup=kb)
