from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP, ADMIN_ID
import database.games as games_db
import urllib.parse

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

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_amount)
    def xu_ly_nap(message):
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

        waiting_for_amount.remove(message.from_user.id)
        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        # LINK TẠO MÃ QR CHUẨN CỦA SEPAY (GIỐNG HỆT ẢNH BẠN GỬI)
        raw_url = f"https://vietqr.app/img?bank=TPBank&acc={SEPAY_BANK_NUMBER}&template=compact&amount={so_tien}&des={ma_don}&showinfo=true&holder={SEPAY_ACCOUNT_NAME}"
        
        # Mã hóa URL để xử lý dấu cách trong tên chủ thẻ
        qr_url = urllib.parse.quote(raw_url, safe=':/?&=')

        # Gửi ảnh QR và thông tin
        try:
            bot.send_photo(
                message.chat.id, 
                photo=qr_url, 
                caption=f"✅ Tạo đơn nạp thành công!\n\n"
                        f"💵 Số tiền: {so_tien:,}đ\n"
                        f"📝 Nội dung CK: <code>{ma_don}</code>\n"
                        f"💰 Điểm nhận: {so_diem_nhan} (đã trừ 2% phí)\n\n"
                        f"👇 Quét mã QR để thanh toán. Hệ thống sẽ tự động cộng điểm sau 1-2 phút.",
                parse_mode='HTML'
            )
        except Exception as e:
            # Nếu Telegram lỗi không hiển thị được ảnh, gửi link dự phòng
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📲 BẤM VÀO ĐÂY ĐỂ LẤY MÃ QR", url=qr_url))
            bot.reply_to(message, f"✅ Đã tạo đơn nạp {so_tien:,}đ.\nBấm nút bên dưới để lấy mã QR thanh toán:", reply_markup=kb)
