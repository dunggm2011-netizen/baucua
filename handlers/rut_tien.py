from config import ADMIN_ID
import database.users as users_db

def register_handlers(bot):
    # Lưu trạng thái chờ rút: {user_id: so_diem}
    waiting_for_rut = {}

    @bot.message_handler(func=lambda m: m.text == "💸 Rút tiền")
    def bat_dau_rut(message):
        diem = users_db.get_diem(message.from_user.id)
        waiting_for_rut[message.from_user.id] = None # Đánh dấu đang chờ nhập điểm
        bot.reply_to(message, f"Điểm hiện tại: {diem}\nNhập số điểm muốn rút (quy đổi: 1000 điểm = 10.000đ):")

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_rut and waiting_for_rut[m.from_user.id] is None)
    def xu_ly_diem_rut(message):
        if message.text.startswith('/'): return
        try:
            so_diem = int(message.text)
        except:
            bot.reply_to(message, "Số điểm không hợp lệ. Nhập lại:")
            return

        user_id = message.from_user.id
        if not users_db.tru_diem(user_id, so_diem):
            bot.reply_to(message, "Không đủ điểm. Nhập lại số điểm khác:")
            return

        waiting_for_rut[user_id] = so_diem # Lưu số điểm, chuyển sang chờ nhập STK
        bot.reply_to(message, "Nhập số tài khoản ngân hàng của bạn:")

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_rut and waiting_for_rut[m.from_user.id] is not None)
    def xu_ly_stk(message):
        if message.text.startswith('/'): return
        stk = message.text
        user_id = message.from_user.id
        so_diem = waiting_for_rut.pop(user_id) # Lấy điểm ra và xóa trạng thái

        # Gửi tin nhắn cho Admin
        admin_msg = (
            f"💰 YÊU CẦU RÚT TIỀN\n"
            f"User: {user_id}\n"
            f"Điểm: {so_diem}\n"
            f"Quy đổi: {so_diem * 10:,}đ\n"
            f"STK: {stk}\n\n"
            f"Dùng lệnh: /duyetrut {user_id} {so_diem} để xác nhận."
        )
        bot.send_message(ADMIN_ID, admin_msg)
        bot.reply_to(message, "Đã gửi yêu cầu. Admin sẽ xử lý trong ít phút.")

    # Lệnh Admin duyệt rút
    @bot.message_handler(commands=['duyetrut'])
    def duyet_rut(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split()
            user_id = int(parts[1])
            so_diem = int(parts[2])
        except:
            bot.reply_to(message, "Cú pháp: /duyetrut <user_id> <so_diem>")
            return
        
        bot.reply_to(message, f"✅ Đã duyệt rút {so_diem} điểm cho user {user_id}.")
        try:
            bot.send_message(user_id, f"✅ Yêu cầu rút {so_diem} điểm đã được duyệt. Vui lòng kiểm tra tài khoản.")
        except:
            bot.send_message(ADMIN_ID, f"⚠️ Không thể nhắn tin cho user {user_id} (có thể họ đã chặn bot).")
