from config import ADMIN_ID
import database.users as users_db
from database.db import get_conn

def register_handlers(bot):
    # Lưu trạng thái chờ rút: {user_id: so_diem}
    waiting_for_rut = {}

    @bot.message_handler(func=lambda m: m.text == "💸 Rút tiền")
    def bat_dau_rut(message):
        diem = users_db.get_diem(message.from_user.id)
        waiting_for_rut[message.from_user.id] = None 
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
        # Chỉ kiểm tra xem có đủ điểm không, KHÔNG trừ điểm ở đây
        if users_db.get_diem(user_id) < so_diem:
            bot.reply_to(message, "Không đủ điểm. Nhập lại số điểm khác:")
            return

        waiting_for_rut[user_id] = so_diem 
        bot.reply_to(message, "Nhập số tài khoản ngân hàng của bạn:")

    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_rut and waiting_for_rut[m.from_user.id] is not None)
    def xu_ly_stk(message):
        if message.text.startswith('/'): return
        stk = message.text
        user_id = message.from_user.id
        so_diem = waiting_for_rut.pop(user_id) 

        # Lưu yêu cầu vào Database với trạng thái 'cho_duyet'
        conn = get_conn()
        cur = conn.execute('INSERT INTO yeu_cau_rut (user_id, so_diem, stk) VALUES (?, ?, ?)', (user_id, so_diem, stk))
        req_id = cur.lastrowid
        conn.commit()
        conn.close()

        # Gửi tin nhắn cho Admin (Kèm mã yêu cầu req_id)
        admin_msg = (
            f"💰 YÊU CẦU RÚT TIỀN #{req_id}\n"
            f"User: {user_id}\n"
            f"Điểm: {so_diem}\n"
            f"Quy đổi: {so_diem * 10:,}đ\n"
            f"STK: {stk}\n\n"
            f"👉 Chuyển khoản xong, gõ lệnh:\n/duyetrut {req_id}"
        )
        bot.send_message(ADMIN_ID, admin_msg)
        bot.reply_to(message, f"Đã gửi yêu cầu rút. Vui lòng chờ Admin duyệt.")

    # --- LỆNH ADMIN DUYỆT RÚT ---
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

        # Kiểm tra lại xem user có bị trừ điểm ở chỗ khác không
        diem_hien_tai = users_db.get_diem(user_id)
        if diem_hien_tai < so_diem:
            bot.reply_to(message, f"❌ User này hiện chỉ còn {diem_hien_tai} điểm, không đủ để rút {so_diem}. Hãy /tuchoi {req_id}")
            conn.close(); return

        # Tiến hành trừ điểm và cập nhật trạng thái
        users_db.tru_diem(user_id, so_diem)
        conn.execute("UPDATE yeu_cau_rut SET trang_thai='da_duyet' WHERE id=?", (req_id,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ Đã duyệt rút {so_diem} điểm cho user {user_id}.")
        try:
            bot.send_message(user_id, f"✅ Yêu cầu rút {so_diem} điểm đã được duyệt. Vui lòng kiểm tra tài khoản.")
        except:
            pass

    # --- LỆNH ADMIN TỪ CHỐI RÚT ---
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
        
        if not req:
            bot.reply_to(message, "❌ Không tìm thấy yêu cầu này.")
            conn.close(); return
            
        conn.execute("UPDATE yeu_cau_rut SET trang_thai='tu_choi' WHERE id=?", (req_id,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"❌ Đã từ chối yêu cầu rút #{req_id}.")
        try:
            bot.send_message(req['user_id'], f"❌ Yêu cầu rút {req['so_diem']} điểm đã bị từ chối. Vui lòng liên hệ Admin.")
        except:
            pass
