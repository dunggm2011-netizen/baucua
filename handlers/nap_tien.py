import urllib.request
import urllib.parse
from io import BytesIO
from PIL import Image
from config import SEPAY_BANK_BIN, SEPAY_BANK_NUMBER, SEPAY_ACCOUNT_NAME, PHI_NAP
import database.games as games_db

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
            bot.reply_to(message, "❌ Số tiền không hợp lệ.")
            return

        if so_tien < 10000 or so_tien > 200000:
            bot.reply_to(message, "❌ Số tiền phải từ 10.000 đến 200.000.")
            return

        user_id = message.from_user.id
        ma_don = f"NAP{user_id}{so_tien}"
        
        # Mã hóa URL để không bị lỗi khoảng trắng trong tên chủ thẻ
        qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
        qr_url = urllib.parse.quote(qr_url, safe=':/?&=') 
        
        so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
        games_db.luu_giao_dich(user_id, "nap", so_tien, so_diem_nhan, ma_don)

        try:
            # Dùng urllib của Python để tải ảnh
            req = urllib.request.Request(qr_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                img_data = response.read()

            # Dùng Pillow xử lý ảnh
            img = Image.open(BytesIO(img_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            bio = BytesIO()
            bio.name = 'qr_code.jpg'
            img.save(bio, 'JPEG', quality=95)
            bio.seek(0)
            
            bot.send_photo(
                message.chat.id, 
                photo=bio, 
                caption=f"✅ Tạo đơn nạp thành công!\n\nQuét QR để nạp: {so_tien:,}đ\nNội dung CK: {ma_don}\nĐiểm nhận: {so_diem_nhan} (đã trừ 2% phí)\n\nSau khi chuyển khoản, điểm sẽ tự động cộng."
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Lỗi: {str(e)}")
