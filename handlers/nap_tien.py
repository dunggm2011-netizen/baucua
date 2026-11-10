from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
import database.games as games_db

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
    def bat_dau_nap(message):
        msg = bot.reply_to(message, "Nhập số tiền muốn nạp (từ 10.000 đến 200.000 VNĐ):\nVí dụ: 50000")
        bot.register_next_step_handler(msg, xu_ly_nap)

    def xu_ly_nap(message):
        # Bỏ qua nếu người dùng bấm nhầm các nút menu khác
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
        
        # Tạo link QR từ VietQR
        qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        
        # Lưu giao dịch
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        # Gửi ảnh QR
        try:
            bot.send_photo(
                message.chat.id, 
                qr_url, 
                caption=f"✅ Tạo đơn nạp thành công!\n\nQuét QR để nạp: {so_tien:,}đ\nNội dung CK: {ma_don}\nĐiểm nhận: {so_diem_nhan} (đã trừ 2% phí)\n\nSau khi chuyển khoản, điểm sẽ tự động cộng."
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Lỗi tạo mã QR: {str(e)}")
