from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
import database.games as games_db

def register_handlers(bot):
    # Biến lưu trạng thái chờ nhập tiền (dùng dict thay cho context.user_data)
    waiting_for_amount = set()

    @bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
    def bat_dau_nap(message):
        waiting_for_amount.add(message.from_user.id)
        bot.reply_to(message, "Nhập số tiền muốn nạp (10.000 - 200.000 VNĐ):\nVí dụ: 50000\nGõ /huy để hủy.")

    @bot.message_handler(commands=['huy'])
    def huy(message):
        if message.from_user.id in waiting_for_amount:
            waiting_for_amount.remove(message.from_user.id)
        bot.reply_to(message, "Đã hủy.")

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_amount)
    def xu_ly_so_tien(message):
        if message.text.startswith('/'): return # Bỏ qua lệnh khác
        
        try:
            so_tien = int(message.text.replace(".", "").replace(",", ""))
        except:
            bot.reply_to(message, "Số tiền không hợp lệ. Vui lòng nhập lại:")
            return

        if so_tien < 10000 or so_tien > 200000:
            bot.reply_to(message, "Số tiền phải từ 10.000 đến 200.000. Nhập lại:")
            return

        waiting_for_amount.remove(message.from_user.id) # Xóa trạng thái chờ
        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        bot.send_photo(
            message.chat.id, 
            qr_url, 
            caption=f"Quét QR để nạp {so_tien:,}đ\nNội dung CK: {ma_don}\nĐiểm nhận được: {so_diem_nhan} (đã trừ 2% phí)\n\nSau khi chuyển khoản, điểm sẽ tự động cộng."
        )
