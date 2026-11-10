from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
import database.games as games_db
import urllib.parse

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
    def bat_dau_nap(message):
        msg = bot.reply_to(message, "Nhập số tiền muốn nạp (từ 10.000 đến 200.000 VNĐ):\nVí dụ: 50000")
        bot.register_next_step_handler(msg, xu_ly_nap)

    def xu_ly_nap(message):
        if message.text.startswith('/') or message.text in ["🎲 Tạo bàn", "🎯 Đặt cược", "📖 Luật chơi", "💸 Rút tiền", "👤 Hồ sơ"]: 
            return 
            
        try:
            so_tien = int(message.text.replace(".", "").replace(",", ""))
        except:
            bot.reply_to(message, "❌ Số tiền không hợp lệ. Vui lòng bấm nút Nạp tiền để làm lại.")
            return

        if so_tien < 10000 or so_tien > 200000:
            bot.reply_to(message, "❌ Số tiền phải từ 10.000 đến 200.000. Vui lòng bấm nút Nạp tiền để làm lại.")
            return

        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        
        # Tạo link QR (mã hóa an toàn)
        raw_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        qr_url = urllib.parse.quote(raw_url, safe=':/?&=')
        
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        # Gửi link dưới dạng nút bấm (Đảm bảo không bị Telegram chặn, không bị treo bot)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📲 BẤM VÀO ĐÂY ĐỂ LẤY MÃ QR", url=qr_url))

        text = (
            f"✅ Tạo đơn nạp thành công!\n\n"
            f"💵 Số tiền: {so_tien:,}đ\n"
            f"📝 Nội dung CK: {ma_don}\n"
            f"💰 Điểm nhận: {so_diem_nhan} (đã trừ 2% phí)\n\n"
            f"👇 Bấm nút bên dưới để mở mã QR."
        )
        
        bot.reply_to(message, text, reply_markup=kb)
