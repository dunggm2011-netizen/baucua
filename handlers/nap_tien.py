from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
import database.games as games_db
import urllib.parse

# Danh sách lưu những người đang chờ nhập số tiền
waiting_for_amount = set()

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
    def bat_dau_nap(message):
        waiting_for_amount.add(message.from_user.id)
        bot.reply_to(message, "Nhập số tiền muốn nạp (từ 10.000 đến 200.000 VNĐ):\nVí dụ: 50000\nGõ /huy để hủy.")

    @bot.message_handler(commands=['huy'])
    def huy_nap(message):
        if message.from_user.id in waiting_for_amount:
            waiting_for_amount.remove(message.from_user.id)
        bot.reply_to(message, "Đã hủy thao tác nạp tiền.")

    # Hàm này bắt TẤT CẢ tin nhắn, nhưng chỉ xử lý nếu ID nằm trong danh sách chờ
    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_amount)
    def xu_ly_nap(message):
        # Bỏ qua nếu người dùng bấm các nút menu khác
        if message.text.startswith('/') or message.text in ["🎲 Tạo bàn", "🎯 Đặt cược", "📖 Luật chơi", "💸 Rút tiền", "👤 Hồ sơ"]: 
            if message.from_user.id in waiting_for_amount:
                waiting_for_amount.remove(message.from_user.id)
            return 
            
        try:
            so_tien = int(message.text.replace(".", "").replace(",", ""))
        except:
            bot.reply_to(message, "❌ Số tiền không hợp lệ. Vui lòng nhập lại hoặc gõ /huy.")
            return

        if so_tien < 10000 or so_tien > 200000:
            bot.reply_to(message, "❌ Số tiền phải từ 10.000 đến 200.000. Vui lòng nhập lại hoặc gõ /huy.")
            return

        # Xóa khỏi danh sách chờ
        waiting_for_amount.remove(message.from_user.id)
        
        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        
        # Tạo link QR (dùng định dạng PNG)
        raw_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        qr_url = urllib.parse.quote(raw_url, safe=':/?&=')
        
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        # Gửi tin nhắn kèm nút bấm mở link (Tránh lỗi Telegram không tải được ảnh)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📲 BẤM VÀO ĐÂY ĐỂ LẤY MÃ QR", url=qr_url))

        text = (
            f"✅ Tạo đơn nạp thành công!\n\n"
            f"💵 Số tiền: {so_tien:,}đ\n"
            f"📝 Nội dung CK: <code>{ma_don}</code>\n"
            f"💰 Điểm nhận: {so_diem_nhan} (đã trừ 2% phí)\n\n"
            f"👇 Bấm nút bên dưới để mở mã QR và chuyển khoản."
        )
        
        bot.reply_to(message, text, reply_markup=kb, parse_mode='HTML')
