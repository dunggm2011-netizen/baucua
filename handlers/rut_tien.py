from telebot.types import ForceReply
from config import ADMIN_ID
import database.users as users_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💸 Rút tiền")
    def bat_dau_rut(message):
        diem = users_db.get_diem(message.from_user.id)
        msg = bot.reply_to(message, f"Điểm hiện tại: {diem}\nNhập số điểm muốn rút (1000 điểm = 10.000đ):", reply_markup=ForceReply(selective=True))
        bot.register_next_step_handler(msg, xu_ly_diem_rut)

    def xu_ly_diem_rut(message):
        if message.text.startswith('/'): return
        try:
            so_diem = int(message.text)
        except:
            bot.reply_to(message, "Số điểm không hợp lệ. Bấm Rút tiền lại.")
            return

        user_id = message.from_user.id
        if users_db.get_diem(user_id) < so_diem:
            bot.reply_to(message, "Không đủ điểm. Bấm Rút tiền lại.")
            return

        msg = bot.reply_to(message, "Nhập số tài khoản ngân hàng của bạn:", reply_markup=ForceReply(selective=True))
        bot.register_next_step_handler(msg, xu_ly_stk, so_diem=so_diem)

    def xu_ly_stk(message, so_diem):
        if message.text.startswith('/'): return
        stk = message.text
        user_id = message.from_user.id

        # Lưu yêu cầu rút vào Database
        conn = get_conn()
        cur = conn.execute('INSERT INTO yeu_cau_rut (user_id, so_diem, stk) VALUES (?, ?, ?)', (user_id, so_diem, stk))
        req_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Báo cho Admin
        admin_msg = (
            f"💰 YÊU CẦU RÚT TIỀN #{req_id}\n"
            f"User: {user_id}\n"
            f"Điểm: {so_diem}\n"
            f"Quy đổi: {so_diem * 10:,}đ\n"
            f"STK: {stk}\n\n"
            f"👉 Chuyển khoản xong, gõ lệnh:\n/duyetrut {req_id}"
        )
        bot.send_message(ADMIN_ID, admin_msg)
        bot.reply_to(message, f"Đã gửi yêu cầu rút #{req_id}. Vui lòng chờ Admin duyệt.")

    @bot.message_handler(commands=['duyetrut'])
    def duyet_rut(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            req_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "Cú pháp: /duyetrut <mã_yêu_cầu>")
            return
        
        conn = get_conn()
        req = conn.execute("SELECT * FROM yeu_cau_rut WHERE id=? AND trang_thai='cho_duyet'", (req_id,)).fetchone()
        
        if not req:
            bot.reply_to(message, "❌ Không tìm thấy yêu cầu này hoặc đã được duyệt rồi.")
            conn.close(); return
            
        user_id = req['user_id']
        so_diem = req['so_diem']

        # Trừ điểm người chơi và cập nhật trạng thái
        if users_db.tru_diem(user_id, so_diem):
            conn.execute("UPDATE yeu_cau_rut SET trang_thai='da_duyet' WHERE id=?", (req_id,))
            conn.commit()
            bot.reply_to(message, f"✅ Đã duyệt rút {so_diem} điểm cho user {user_id}.")
            try:
                bot.send_message(user_id, f"✅ Yêu cầu rút {so_diem} điểm đã được duyệt. Vui lòng kiểm tra tài khoản.")
            except:
                pass
        else:
            bot.reply_to(message, "❌ User này không đủ điểm để trừ (có thể đã tiêu vào việc khác).")
        conn.close()

    @bot.message_handler(commands=['tuchoi'])
    def tu_choi_rut(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            req_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "Cú pháp: /tuchoi <mã_yêu_cầu>")
            return
        
        conn = get_conn()
        req = conn.execute("SELECT * FROM yeu_cau_rut WHERE id=? AND trang_thai='cho_duyet'", (req_id,)).fetchone()
        
        if req:
            conn.execute("UPDATE yeu_cau_rut SET trang_thai='tu_choi' WHERE id=?", (req_id,))
            conn.commit()
            bot.reply_to(message, f"❌ Đã từ chối yêu cầu rút #{req_id}.")
        else:
            bot.reply_to(message, "❌ Không tìm thấy yêu cầu này.")
        conn.close()
