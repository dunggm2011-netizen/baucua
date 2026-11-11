from config import ADMIN_ID
import database.users as users_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "💸 Rút tiền")
    def bat_dau_rut(message):
        user_id = message.from_user.id
        diem = users_db.get_diem(user_id)
        
        # 1. Kiểm tra điều kiện cược
        tien = users_db.get_tien_cuoc_va_nap(user_id)
        tong_nap = tien['tong_nap']
        da_cuoc = tien['da_cuoc']
        
        if da_cuoc < tong_nap:
            thieu = tong_nap - da_cuoc
            bot.reply_to(message, f"❌ Bạn chưa đủ điều kiện rút tiền!\n\n"
                                  f"💰 Tổng điểm đã nạp: {tong_nap:,} điểm\n"
                                  f"🎯 Tổng điểm đã cược: {da_cuoc:,} điểm\n"
                                  f"👉 Bạn cần cược thêm {thieu:,} điểm nữa mới được rút.")
            return

        msg = bot.reply_to(message, f"Điểm hiện tại: {diem}\n"
                                    f"Nhập số điểm muốn rút (Tối thiểu: 3.000 điểm | Tối đa: 40.000 điểm):")
        bot.register_next_step_handler(msg, xu_ly_diem_rut)

    def xu_ly_diem_rut(message):
        if message.text.startswith('/') or message.text in ["🎲 Tạo bàn", "🎯 Đặt cược", "📖 Luật chơi", "💰 Nạp tiền", "👤 Hồ sơ", "🏆 TOP NẠP"]: 
            return
            
        try:
            so_diem = int(message.text)
        except:
            bot.reply_to(message, "❌ Số điểm không hợp lệ. Vui lòng bấm nút Rút tiền để làm lại.")
            return

        # 2. Kiểm tra Min/Max
        if so_diem < 3000:
            bot.reply_to(message, "❌ Số điểm rút tối thiểu là 3.000 điểm (30.000 VNĐ). Vui lòng nhập lại.")
            return
        if so_diem > 40000:
            bot.reply_to(message, "❌ Số điểm rút tối đa là 40.000 điểm (400.000 VNĐ). Vui lòng nhập lại.")
            return

        user_id = message.from_user.id
        if users_db.get_diem(user_id) < so_diem:
            bot.reply_to(message, "❌ Không đủ điểm. Vui lòng nhập lại.")
            return

        msg = bot.reply_to(message, "Nhập số tài khoản ngân hàng của bạn:")
        bot.register_next_step_handler(msg, xu_ly_stk, so_diem=so_diem)

    def xu_ly_stk(message, so_diem):
        if message.text.startswith('/') or message.text in ["🎲 Tạo bàn", "🎯 Đặt cược", "📖 Luật chơi", "💰 Nạp tiền", "👤 Hồ sơ", "🏆 TOP NẠP"]: 
            return
            
        stk = message.text
        msg = bot.reply_to(message, "Nhập tên chủ tài khoản (viết không dấu, ví dụ: NGUYEN VAN A):")
        bot.register_next_step_handler(msg, xu_ly_ten, so_diem=so_diem, stk=stk)

    def xu_ly_ten(message, so_diem, stk):
        if message.text.startswith('/'): return
        ten_chu_the = message.text
        user_id = message.from_user.id

        # Lưu vào Database
        conn = get_conn()
        cur = conn.execute(
            'INSERT INTO yeu_cau_rut (user_id, so_diem, stk, ten_chu_the) VALUES (?, ?, ?, ?)', 
            (user_id, so_diem, stk, ten_chu_the)
        )
        req_id = cur.lastrowid
        conn.commit(); conn.close()

        # Báo Admin
        admin_msg = (
            f"💰 <b>YÊU CẦU RÚT TIỀN MỚI</b> #{req_id}\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"💸 Số điểm rút: {so_diem} ({so_diem * 10:,}đ)\n"
            f"🏦 STK: <code>{stk}</code>\n"
            f"👨‍💼 Chủ thẻ: {ten_chu_the}\n\n"
            f"👉 Duyệt: /duyetrut {req_id}\n"
            f"👉 Từ chối: /tuchoi {req_id}"
        )
        bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
        bot.reply_to(message, f"✅ Đã gửi yêu cầu rút #{req_id}. Vui lòng chờ Admin duyệt tay.")

    # --- CÁC LỆNH DUYỆT CỦA ADMIN ---
    @bot.message_handler(commands=['duyetrut'])
    def duyet_rut(message):
        if message.from_user.id != ADMIN_ID: return
        try: req_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "Cú pháp: /duyetrut <mã_yêu_cầu>")
            return
        
        conn = get_conn()
        req = conn.execute("SELECT * FROM yeu_cau_rut WHERE id=? AND trang_thai='cho_duyet'", (req_id,)).fetchone()
        
        if not req:
            bot.reply_to(message, "❌ Không tìm thấy yêu cầu này hoặc đã được duyệt.")
            conn.close(); return
            
        user_id = req['user_id']
        so_diem = req['so_diem']

        if users_db.tru_diem(user_id, so_diem):
            conn.execute("UPDATE yeu_cau_rut SET trang_thai='da_duyet' WHERE id=?", (req_id,))
            conn.commit()
            bot.reply_to(message, f"✅ Đã duyệt rút {so_diem} điểm cho user {user_id}.")
            try:
                bot.send_message(user_id, f"✅ Yêu cầu rút {so_diem} điểm đã được duyệt.")
            except: pass
        else:
            bot.reply_to(message, "❌ User này hiện không đủ điểm để trừ.")
        conn.close()

    @bot.message_handler(commands=['tuchoi'])
    def tu_choi_rut(message):
        if message.from_user.id != ADMIN_ID: return
        try: req_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "Cú pháp: /tuchoi <mã_yêu_cầu>")
            return
        
        conn = get_conn()
        req = conn.execute("SELECT * FROM yeu_cau_rut WHERE id=? AND trang_thai='cho_duyet'", (req_id,)).fetchone()
        
        if req:
            conn.execute("UPDATE yeu_cau_rut SET trang_thai='tu_choi' WHERE id=?", (req_id,))
            conn.commit()
            bot.reply_to(message, f"❌ Đã từ chối yêu cầu rút #{req_id}.")
            try:
                bot.send_message(req['user_id'], f"❌ Yêu cầu rút {req['so_diem']} điểm của bạn đã bị từ chối.")
            except: pass
        else:
            bot.reply_to(message, "❌ Không tìm thấy yêu cầu này.")
        conn.close()
